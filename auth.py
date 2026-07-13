import streamlit as st
import db_utils
import hashlib
import secrets
import sqlite3
import os
import time

# ===========================================================================
# ---- SECURE "REMEMBER ME" (DB-backed, revocable, per-browser) ----
#
# History:
#   v1 bug: session data written to data/.login_cache.json - shared file
#   on Streamlit Cloud's shared filesystem -> leaked across visitors.
#
#   v2 (cookie-based): fixed the leak, but streamlit-cookies-manager's
#   underlying JS component has a "ready()" race condition - on some
#   reruns it never signals ready in time, so login()/logout() silently
#   no-op and the user gets logged out on refresh anyway. Burned hours
#   debugging component timing instead of auth logic.
#
#   v3 (this file): token lives in the URL query string instead of a
#   cookie. No JS component, no ready() wait, no race condition -
#   st.query_params is synchronous and available immediately.
#
# Design (same DB-backed revocation model as v2, just a different place
# to stash the raw token client-side):
#   1. On login, generate an OPAQUE random token. Store only its SHA-256
#      hash in a local sessions DB, alongside user_id/username/expiry.
#      The raw token is never persisted server-side - same principle as
#      password hashing.
#   2. Put the RAW token in the URL: ?session=xyz123...
#   3. On every app load, read st.query_params -> hash it -> look up the
#      hash in the sessions DB -> if found and not expired, restore the
#      session.
#   4. TOKEN ROTATION: every time a session is successfully restored from
#      the URL, immediately issue a fresh token, delete the old DB row,
#      and rewrite the URL with the new token. This shrinks the window
#      during which a leaked/shared URL is still useful - a URL that's
#      been copied and reused is already dead the next time the real
#      owner's browser loads the app.
#   5. Logout deletes the DB row AND clears the query param.
#
# Known trade-off (be upfront about this with anyone reviewing the code):
# the token is visible in the URL bar. If someone screenshots or shares
# that exact URL before rotation kicks in, the token in it is usable
# until rotated/expired/revoked. Mitigations: rotate-on-restore (above),
# short 2-day expiry, and instant DB-side revocation on logout. Combined
# with `rel="noreferrer"` on any outbound links elsewhere in the app
# (so the token doesn't leak via the Referer header when a user clicks
# an evidence source link), this keeps exposure low without needing a
# cookie component at all.
# ===========================================================================

SESSION_DB_PATH = os.path.join("data", "sessions.db")
SESSION_EXPIRY_DAYS = 2
QUERY_PARAM_NAME = "session"


def _ensure_session_table():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(SESSION_DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            token_hash TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            expires_at INTEGER NOT NULL,
            created_at INTEGER NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def _cleanup_expired_sessions():
    """Best-effort cleanup of expired rows. Cheap enough to run on
    every app start - no separate cron/infra needed."""
    _ensure_session_table()
    conn = sqlite3.connect(SESSION_DB_PATH)
    conn.execute("DELETE FROM sessions WHERE expires_at < ?", (int(time.time()),))
    conn.commit()
    conn.close()


def create_session_token(user_id: int, username: str) -> str:
    """
    Generates a new opaque random token, stores ONLY its hash (+
    user_id/username/expiry) in the sessions DB, and returns the raw
    token so the caller can place it in the URL.
    """
    _ensure_session_table()
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    expires_at = int(time.time()) + SESSION_EXPIRY_DAYS * 86400

    conn = sqlite3.connect(SESSION_DB_PATH)
    conn.execute(
        "INSERT INTO sessions (token_hash, user_id, username, expires_at, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (token_hash, user_id, username, expires_at, int(time.time())),
    )
    conn.commit()
    conn.close()
    return raw_token


def verify_session_token(raw_token: str):
    """
    Returns (user_id, username) if raw_token hashes to a valid,
    non-expired row in the sessions DB, else None. If the row is
    expired, it is cleaned up on the way out.
    """
    if not raw_token:
        return None

    _ensure_session_table()
    token_hash = _hash_token(raw_token)

    conn = sqlite3.connect(SESSION_DB_PATH)
    row = conn.execute(
        "SELECT user_id, username, expires_at FROM sessions WHERE token_hash = ?",
        (token_hash,),
    ).fetchone()
    conn.close()

    if not row:
        return None

    user_id, username, expires_at = row
    if expires_at < int(time.time()):
        delete_session_token(raw_token)
        return None

    return user_id, username


def delete_session_token(raw_token: str):
    """Revokes a specific session token immediately (used on logout and
    on rotation of an old token)."""
    if not raw_token:
        return
    _ensure_session_table()
    token_hash = _hash_token(raw_token)
    conn = sqlite3.connect(SESSION_DB_PATH)
    conn.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
    conn.commit()
    conn.close()


def _set_url_token(raw_token: str):
    st.query_params[QUERY_PARAM_NAME] = raw_token


def _clear_url_token():
    if QUERY_PARAM_NAME in st.query_params:
        del st.query_params[QUERY_PARAM_NAME]


# ===========================================================================
# ---- AUTH STATE ----
# ===========================================================================

def login_required(func):
    """
    Decorator: ensures user is logged in, otherwise redirects to login page
    """
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            st.warning("Please log in first")
            show_login_form()
            return None
        return func(*args, **kwargs)
    return wrapper


def init_auth_state():
    """Initialize auth-related session state."""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None

    if 'username' not in st.session_state:
        st.session_state.username = None

    if 'auth_page' not in st.session_state:
        st.session_state.auth_page = 'login'  # options: 'login', 'register'

    if 'session_restored' not in st.session_state:
        # Guards against re-attempting restore/rotation on every single
        # rerun - we only need to do it once per browser session.
        st.session_state.session_restored = False


def try_restore_session():
    """
    Looks for a session token in the URL (?session=...) and restores
    st.session_state's user_id/username if it's still valid (present +
    not expired + not revoked) in the sessions DB. On a successful
    restore, immediately rotates the token (issues a new one, deletes
    the old DB row, rewrites the URL) so a copied/leaked URL stops
    working the next time the real owner loads the app.

    Must be called once near the top of the script, before deciding
    whether to show the login form.
    """
    if st.session_state.user_id is not None:
        return  # already logged in this run

    if st.session_state.session_restored:
        return  # already attempted restore once this session

    st.session_state.session_restored = True

    raw_token = st.query_params.get(QUERY_PARAM_NAME)
    result = verify_session_token(raw_token) if raw_token else None

    if result:
        user_id, username = result
        st.session_state.user_id = user_id
        st.session_state.username = username

        # Rotate: old token is now dead, issue a fresh one and put it
        # in the URL so this exact link can't be reused elsewhere.
        delete_session_token(raw_token)
        new_token = create_session_token(user_id, username)
        _set_url_token(new_token)

    # Opportunistic cleanup - cheap, keeps the sessions table small.
    _cleanup_expired_sessions()


def is_logged_in() -> bool:
    """
    Check if user is logged in

    Returns:
        Whether the user is logged in
    """
    return st.session_state.user_id is not None


def login(username: str, password: str, remember: bool = True):
    """
    Verify user and set session state. If remember=True, also issues a
    secure session token and puts it in the URL (?session=...) so the
    login survives a refresh on THIS browser via the URL bar.

    Args:
        username: username
        password: password
        remember: whether to persist login across refreshes

    Returns:
        Returns user_id on success, None on failure
    """
    user_id = db_utils.verify_user(username, password)

    if user_id:
        st.session_state.user_id = user_id
        st.session_state.username = username

        if remember:
            raw_token = create_session_token(user_id, username)
            _set_url_token(raw_token)

        return user_id
    else:
        return None


def logout():
    """
    Log out user: revokes the session token in the DB (instant,
    server-side revocation), clears it from the URL, and clears
    session state.
    """
    raw_token = st.query_params.get(QUERY_PARAM_NAME)
    if raw_token:
        delete_session_token(raw_token)
    _clear_url_token()

    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.session_restored = False

    # Clear chat history
    if 'messages' in st.session_state:
        st.session_state.messages = []


def register(username: str, password: str, confirm_password: str) -> tuple[bool, str]:
    """
    Register new user

    Args:
        username: username
        password: password
        confirm_password: confirm password

    Returns:
        (success flag, error message)
    """
    # Validate user input
    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters"

    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters"

    if password != confirm_password:
        return False, "Passwords do not match"

    # Try to create user
    success = db_utils.create_user(username, password)

    if success:
        return True, ""
    else:
        return False, "Username already exists, please choose another"


def show_login_form():
    """
    Display login form
    """
    st.subheader("Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        remember = st.checkbox("Remember me on this browser", value=True)
        submit = st.form_submit_button("Login")

        if submit:
            result = login(username, password, remember=remember)
            if result:
                st.success("Login successful!")
                st.rerun()  # Rerun app to update UI
            else:
                st.error("Incorrect username or password")

    # Navigation button outside the form
    st.markdown("---")
    st.markdown("Don't have an account?")

    if st.button("Register a new account"):
        st.session_state.auth_page = 'register'
        st.rerun()


def show_register_form():
    """
    Display registration form
    """
    st.subheader("Register a new account")

    with st.form("register_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm password", type="password")
        submit = st.form_submit_button("Register")

        if submit:
            success, error_msg = register(username, password, confirm_password)
            if success:
                st.success("Registration successful! You can now log in")
                st.session_state.auth_page = 'login'
                st.rerun()
            else:
                st.error(error_msg)

    # Navigation button outside the form
    st.markdown("---")
    st.markdown("Already have an account?")

    if st.button("Back to login"):
        st.session_state.auth_page = 'login'
        st.rerun()


def show_auth_ui():
    """
    Display auth UI (login or register). Also transparently restores a
    valid remembered session from the URL's ?session= token before
    deciding whether to show the login form at all.
    """
    init_auth_state()
    try_restore_session()

    # If already logged in (fresh login this run, or restored from URL),
    # return directly
    if is_logged_in():
        return True

    # If not logged in, show login or register form
    if st.session_state.auth_page == 'login':
        show_login_form()
    else:
        show_register_form()

    return False
