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


# ===========================================================================
# ---- UI: CSS (card, icon badge, gradient button, responsive) ----
# ===========================================================================

def _inject_auth_css():
    """
    Injects the auth-page CSS once. Only touches the visual layer -
    no auth logic lives here. Uses Streamlit's own data-testid hooks
    to restyle native widgets (form inputs, buttons) so we don't need
    a JS component (same reasoning as the cookie->URL-token switch:
    fewer moving parts on Streamlit Cloud = fewer race conditions).
    """
    st.markdown(
        """
        <style>
        /* ---------- shared tokens ---------- */
        :root {
            --auth-bg: #0d0b1a;
            --auth-card-border: rgba(255,255,255,0.12);
            --auth-accent: #6d5bf0;
            --auth-accent-dark: #4f3fc9;
            --auth-text-dim: rgba(255,255,255,0.55);
        }

        /* ---------- global reset: kill the scroll causes ---------- */
        /* box-sizing guard: without this, input padding-left (2.4rem)
           gets ADDED to width instead of eating into it, which is what
           was pushing content past the viewport and forcing a
           horizontal scrollbar on phones. */
        *, *::before, *::after {
            box-sizing: border-box !important;
        }
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
            overflow-x: hidden !important;
        }

        /* Hide Streamlit's own chrome (top header bar, menu, footer,
           the coloured "decoration" strip). On the login/register page
           this chrome was eating ~5-6rem of vertical space above our
           own header for nothing - that's most of the "extra scroll". */
        header[data-testid="stHeader"] { display: none !important; height: 0 !important; }
        #MainMenu { visibility: hidden !important; }
        footer { visibility: hidden !important; }
        div[data-testid="stToolbar"] { display: none !important; }
        div[data-testid="stDecoration"] { display: none !important; }
        div[data-testid="stStatusWidget"] { display: none !important; }

        /* ==========================================================
           FIX: VERTICAL CENTERING
           Root cause of "sab data upar chipka hai, neeche khaali
           space bacha hai": .block-container below only had
           horizontal centering (max-width + margin:0 auto). Nothing
           told the PARENT (stMain) to take full viewport height and
           center its child vertically, so the card rendered flush at
           the top and the rest of the tall mobile viewport was just
           empty space beneath it.

           Fix: make [data-testid="stMain"] a full-height flex
           container that centers its single child (.block-container)
           both vertically and horizontally. Uses 100dvh (dynamic
           viewport height) with 100vh as a fallback for browsers that
           don't support dvh yet - dvh is what actually accounts for
           mobile browser chrome (address bar collapsing/expanding),
           vh alone can leave a similar gap on some mobile browsers.
           ========================================================== */
        [data-testid="stMain"] {
            min-height: 100vh;
            min-height: 100dvh;
            display: flex !important;
            align-items: center;
            justify-content: center;
        }
        [data-testid="stMain"] > div {
            width: 100%;
        }

        /* Center + cap the whole app content so the card doesn't
           stretch edge-to-edge on desktop, but stays full-width
           feeling on mobile. Since the Streamlit header is now
           hidden, padding-top can shrink a lot. */
        .main .block-container {
            max-width: 480px;
            width: 100%;
            margin: 0 auto;
            padding-top: 1.25rem;
            padding-bottom: 1.25rem;
        }

        /* Streamlit puts every st.markdown/st.form/st.button call in
           its own element-container and stacks them with a flex gap.
           With ~8 separate calls per page that gap alone added several
           rem of dead space - this is the other half of the "too much
           scroll" problem. Tighten it globally on this page. */
        [data-testid="stVerticalBlock"] {
            gap: 0.5rem !important;
        }
        div[data-testid="element-container"] {
            margin-bottom: 0 !important;
        }

        /* CRITICAL: every direct child of the vertical block (every
           element-container - markdown, form, button, all of them)
           must take the FULL card width. Without this, div[data-testid
           ="stButton"] itself renders shrink-to-fit (only as wide as
           the button text needs), so the justify-content:center below
           ends up centering the button inside a tiny box that's
           already sitting at the left edge - not inside the actual
           card. This is the rule that makes "center the wrapper" mean
           anything: the wrapper has to be full-width FIRST, then
           flex can center a smaller button inside it. */
        .main .block-container div[data-testid="stVerticalBlock"] > div {
            width: 100% !important;
        }

        /* ROOT FIX for the button-centering bug (v2 - flexbox, not
           position math):
           The old rule used position:relative + left:50% +
           transform:translateX(-50%) on the BUTTON itself. That only
           works if left/transform stay in sync with the button's
           CURRENT computed width every time the width changes (e.g.
           the mobile media query below switching it to width:100%).
           Since only `width` was overridden inside the media query
           and left/transform were left untouched, the 50%/-50% math
           kept being computed against a stale width -> visible
           pixel-level left shift on mobile, which is exactly the bug
           in the screenshots.

           Fix: drop position math entirely. Make the WRAPPER
           (div[data-testid="stButton"]) a flex container with
           justify-content:center. A flex parent centers a child of
           ANY width with zero math - this is true whether the button
           ends up 200px wide (desktop/tablet) or 100% wide (mobile),
           so the two states below not only can't drift out of sync,
           there's no sync to maintain in the first place. */
        /* Note: horizontal centering/width for the "Register a new
           account" / "Back to login" buttons is now handled entirely
           by st.columns([1, 2, 1]) + use_container_width=True in the
           Python code, NOT by CSS - see show_login_form() /
           show_register_form(). That's a Streamlit layout primitive,
           immune to data-testid/DOM changes across Streamlit
           versions, unlike position/flex tricks here. This CSS block
           only handles colors/border - it deliberately does NOT set
           width/max-width/margin so it can never fight with
           use_container_width for control of the button's size.*/
        div[data-testid="stButton"] button {
            background: transparent !important;
            border: 1.5px solid var(--auth-accent) !important;
            border-radius: 10px !important;
            color: var(--auth-accent) !important;
            font-weight: 600 !important;
            height: 2.6rem !important;
        }
        div[data-testid="stButton"] button:hover {
            background: rgba(109, 91, 240, 0.1) !important;
        }

        /* ---------- primary (gradient) button - form submit ---------- */
        div[data-testid="stFormSubmitButton"] {
            display: flex !important;
            width: 100% !important;
        }
        div[data-testid="stFormSubmitButton"] button {
            display: block !important;
            width: 100% !important;
            max-width: 100% !important;
            background: linear-gradient(135deg, var(--auth-accent), var(--auth-accent-dark)) !important;
            border: none !important;
            border-radius: 10px !important;
            color: #fff !important;
            font-weight: 600 !important;
            height: 2.9rem !important;
            margin: 0.35rem 0 0.25rem 0 !important;
        }
        div[data-testid="stFormSubmitButton"] button:hover {
            filter: brightness(1.08);
        }

        /* ---------- input icons ---------- */
        div[data-testid="stTextInput"] {
            position: relative;
            width: 100%;
        }
        div[data-testid="stTextInput"] input {
            background-color: rgba(255,255,255,0.04) !important;
            border: 1px solid var(--auth-card-border) !important;
            border-radius: 10px !important;
            color: #fff !important;
            padding-left: 2.4rem !important;
            height: 2.9rem !important;
            width: 100% !important;
        }
        div[data-testid="stTextInput"] input::placeholder {
            color: rgba(255,255,255,0.35) !important;
        }
        div[data-testid="stTextInput"]::before {
            position: absolute;
            left: 0.9rem;
            top: 2.5rem;
            font-size: 1rem;
            opacity: 0.6;
            z-index: 2;
            pointer-events: none;
        }
        div[data-testid="stTextInput"].auth-field-user::before { content: "👤"; }
        div[data-testid="stTextInput"].auth-field-pass::before { content: "🔒"; }

        /* ---------- header: icon badge + title + subtitle ---------- */
        .auth-header {
            text-align: center;
            margin-bottom: 1rem;
        }
        .auth-icon-badge {
            width: 56px;
            height: 56px;
            border-radius: 50%;
            border: 1.5px solid var(--auth-card-border);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 0.6rem auto;
        }
        .auth-icon-badge svg {
            width: 26px;
            height: 26px;
            stroke: var(--auth-accent);
        }
        .auth-title {
            color: #fff;
            font-size: 1.65rem;
            font-weight: 700;
            margin: 0;
        }
        .auth-subtitle {
            color: var(--auth-text-dim);
            font-size: 0.85rem;
            margin-top: 0.25rem;
        }

        /* ---------- card title/subtitle (now the first thing inside
           the native st.form, sharing its bordered card with the
           inputs) ---------- */
        .auth-card-title {
            color: #fff;
            font-size: 1.35rem;
            font-weight: 700;
            letter-spacing: -0.01em;
            line-height: 1.3;
            margin: 0.15rem 0 0.45rem 0;
        }
        .auth-card-subtitle {
            color: var(--auth-text-dim);
            font-size: 0.72rem;
            line-height: 1.4;
            margin: 0 0 1.1rem 0;
        }

        /* ---------- divider ---------- */
        .auth-divider {
            display: flex;
            align-items: center;
            text-align: center;
            color: var(--auth-text-dim);
            font-size: 0.8rem;
            margin: 0.5rem 0;
        }
        .auth-divider::before, .auth-divider::after {
            content: "";
            flex: 1;
            border-bottom: 1px solid var(--auth-card-border);
        }
        .auth-divider:not(:empty)::before { margin-right: 0.75rem; }
        .auth-divider:not(:empty)::after { margin-left: 0.75rem; }

        .auth-switch-prompt {
            text-align: center;
            color: var(--auth-text-dim);
            font-size: 0.85rem;
            margin-bottom: 0.35rem;
        }

        .auth-footer {
            text-align: center;
            color: var(--auth-text-dim);
            font-size: 0.78rem;
            margin-top: 1rem;
        }

        /* ---------- responsive tweaks ---------- */
        /* phones */
        @media (max-width: 480px) {
            [data-testid="stMain"] {
                align-items: center;
            }
            .main .block-container {
                max-width: 100%;
                padding-left: 1rem;
                padding-right: 1rem;
                padding-top: 1rem;
                padding-bottom: 1rem;
            }
            [data-testid="stVerticalBlock"] {
                gap: 0.4rem !important;
            }
            .auth-header { margin-bottom: 0.6rem; }
            .auth-icon-badge { width: 46px; height: 46px; margin-bottom: 0.4rem; }
            .auth-icon-badge svg { width: 22px; height: 22px; }
            .auth-title { font-size: 1.35rem; }
            .auth-subtitle { font-size: 0.78rem; }
            .auth-card-title { font-size: 1.15rem; margin-bottom: 0.4rem; }
            .auth-card-subtitle { font-size: 0.68rem; margin-bottom: 0.9rem; }
            .auth-divider { margin: 0.35rem 0; }
            .auth-footer { margin-top: 0.6rem; font-size: 0.72rem; }
            div[data-testid="stTextInput"] input { height: 2.6rem !important; }
            div[data-testid="stFormSubmitButton"] button { height: 2.6rem !important; }
            /* Width/centering come from st.columns + use_container_width
               (see Python code) on every screen size - only the height
               needs a phone-specific tweak here. */
            div[data-testid="stButton"] button {
                height: 2.4rem !important;
            }
        }
        /* iPad / iPad Pro portrait+landscape */
        @media (min-width: 768px) and (max-width: 1024px) {
            .main .block-container {
                max-width: 460px;
                padding-top: 2rem;
            }
        }
        /* desktop */
        @media (min-width: 1025px) {
            .main .block-container {
                max-width: 440px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _auth_header():
    st.markdown(
        """
        <div class="auth-header">
            <div class="auth-icon-badge">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="11" cy="11" r="7" stroke-width="2"/>
                    <line x1="21" y1="21" x2="16.65" y2="16.65" stroke-width="2" stroke-linecap="round"/>
                </svg>
            </div>
            <p class="auth-title">AI Fake News Detector</p>
            <p class="auth-subtitle">Verify. Analyze. Stay Informed.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _auth_footer():
    """No longer called from either form - kept as a no-op stub in case
    something elsewhere still references it, so nothing breaks."""
    pass


def _tag_field_icons():
    """
    Runs a tiny bit of JS to tag the username/password stTextInput
    wrapper divs with a class (auth-field-user / auth-field-pass) so
    the CSS above can attach the right icon. Matches purely on the
    visible label text, so it stays correct even if Streamlit changes
    internal DOM structure elsewhere.

    Uses a MutationObserver (instead of fixed setTimeout delays) so
    tagging isn't a timing gamble - on mobile/slower renders the fixed
    150ms/500ms delays could fire before the fields existed, which is
    why the icons sometimes silently never showed up. The observer
    reacts the instant the fields actually appear in the DOM, and
    disconnects once both fields on the page are tagged.
    """
    st.markdown(
        """
        <script>
        (function() {
            const tagFields = () => {
                const doc = window.parent.document;
                const wrappers = doc.querySelectorAll('div[data-testid="stTextInput"]');
                let allTagged = wrappers.length > 0;
                wrappers.forEach((w) => {
                    const label = w.querySelector('label');
                    if (!label) { allTagged = false; return; }
                    const text = label.innerText.trim().toLowerCase();
                    if (text === "username") {
                        w.classList.add("auth-field-user");
                    } else if (text === "password" || text === "confirm password") {
                        w.classList.add("auth-field-pass");
                    } else {
                        allTagged = false;
                    }
                });
                return allTagged;
            };

            // Try immediately in case fields are already there.
            if (tagFields()) return;

            const doc = window.parent.document;
            const observer = new MutationObserver(() => {
                if (tagFields()) {
                    observer.disconnect();
                }
            });
            observer.observe(doc.body, { childList: true, subtree: true });

            // Safety net: stop observing after 5s no matter what, so we
            // never leak an observer if something unexpected happens.
            setTimeout(() => observer.disconnect(), 5000);
        })();
        </script>
        """,
        unsafe_allow_html=True,
    )


# ===========================================================================
# ---- UI: forms (same logic calls as before, new markup around them) ----
# ===========================================================================

def show_login_form():
    """
    Display login form - card UI, same login()/session logic as before.
    """
    _auth_header()

    # NOTE: previously wrapped in a raw '<div class="auth-card">' /
    # '</div>' pair split across two separate st.markdown() calls.
    # Streamlit renders each st.markdown() as its own isolated HTML
    # fragment, so the browser auto-closed the unclosed <div> right
    # there - it never actually wrapped the title/subtitle/form below
    # it, and just rendered as an empty bordered box. Removed; the
    # native st.form() below already renders its own bordered card, so
    # the title/subtitle are placed AS THE FIRST THING INSIDE that
    # form, making them visually part of the same bordered box as the
    # inputs (previously they sat above the box, outside its border).
    with st.form("login_form"):
        st.markdown('<p class="auth-card-title">Welcome back</p>', unsafe_allow_html=True)
        st.markdown('<p class="auth-card-subtitle">Login to continue</p>', unsafe_allow_html=True)

        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        remember = st.checkbox("Remember me on this browser", value=True)
        submit = st.form_submit_button("Login")

        if submit:
            result = login(username, password, remember=remember)
            if result:
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Incorrect username or password")

    st.markdown('<div class="auth-divider">or</div>', unsafe_allow_html=True)
    st.markdown('<p class="auth-switch-prompt">Don\'t have an account?</p>', unsafe_allow_html=True)

    # Centering via st.columns instead of CSS: this is Streamlit's own
    # layout primitive, not dependent on any data-testid selector
    # matching the installed Streamlit version's actual DOM. The
    # middle column is guaranteed centered because the two side
    # columns are equal width - no CSS guesswork involved at all.
    _, mid, _ = st.columns([1.04, 1.92, 1.04])
    with mid:
        if st.button("Register a new account", use_container_width=True):
            st.session_state.auth_page = 'register'
            st.rerun()

    _tag_field_icons()


def show_register_form():
    """
    Display registration form - card UI, same register() logic as before.
    """
    _auth_header()

    # Same reasoning as show_login_form(): title/subtitle now render
    # as the first thing INSIDE st.form, so they sit inside the same
    # bordered card as the inputs instead of above it.
    with st.form("register_form"):
        st.markdown('<p class="auth-card-title">Create an account</p>', unsafe_allow_html=True)
        st.markdown('<p class="auth-card-subtitle">Register to get started</p>', unsafe_allow_html=True)

        username = st.text_input("Username", placeholder="Choose a username")
        password = st.text_input("Password", type="password", placeholder="Choose a password")
        confirm_password = st.text_input("Confirm password", type="password", placeholder="Re-enter your password")
        submit = st.form_submit_button("Register")

        if submit:
            success, error_msg = register(username, password, confirm_password)
            if success:
                st.success("Registration successful! You can now log in")
                st.session_state.auth_page = 'login'
                st.rerun()
            else:
                st.error(error_msg)

    st.markdown('<div class="auth-divider">or</div>', unsafe_allow_html=True)
    st.markdown('<p class="auth-switch-prompt">Already have an account?</p>', unsafe_allow_html=True)

    # Same column-based centering as the login page - see comment
    # there for why this replaces the old CSS-only approach.
    _, mid, _ = st.columns([1.04, 1.92, 1.04])
    with mid:
        if st.button("Back to login", use_container_width=True):
            st.session_state.auth_page = 'login'
            st.rerun()

    _tag_field_icons()


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

    _inject_auth_css()

    # If not logged in, show login or register form
    if st.session_state.auth_page == 'login':
        show_login_form()
    else:
        show_register_form()

    return False
