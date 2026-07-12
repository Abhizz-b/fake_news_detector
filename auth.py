import streamlit as st
import db_utils
import hashlib
import time

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
    """
    Initialize auth-related session state.

    SECURITY FIX: this used to also fall back to check_saved_login(),
    which read a login token from a file on disk (data/.login_cache.json)
    shared by the whole server process. On Streamlit Community Cloud,
    EVERY visitor's app instance runs on the same shared filesystem, so
    that file was effectively global, not per-user. Whoever logged in
    last with "Remember me" checked got their session handed to anyone
    who opened the app afterwards - a cross-user account/history leak.

    Fix: login state now lives ONLY in st.session_state, which Streamlit
    keeps separate per browser session automatically. No file, no
    cross-user leakage. The tradeoff is that "remember me across a
    closed tab/browser restart" no longer works - that's the correct
    behavior for a public multi-user deployment; a fully persistent
    "remember me" would need a proper per-browser secure cookie/token
    scheme, which is a separate, bigger feature.
    """
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None

    if 'username' not in st.session_state:
        st.session_state.username = None

    if 'auth_page' not in st.session_state:
        st.session_state.auth_page = 'login'  # options: 'login', 'register'

def generate_login_token(username: str) -> str:
    """
    Generate login token
    """
    timestamp = str(int(time.time()))
    token_string = f"{username}:{timestamp}:fake_news_detector"
    return hashlib.md5(token_string.encode()).hexdigest()

def save_login_state(username: str, user_id: int, remember: bool = False):
    """
    SECURITY FIX: no longer writes anything to disk (data/.login_cache.json
    used to be shared across every visitor on Streamlit Cloud - see
    init_auth_state() for the full explanation). Login state now lives
    only in st.session_state, which login()/logout() already manage
    directly. This function is kept as a no-op (rather than deleted
    outright) so existing calls to it elsewhere don't break; the
    `remember` flag is intentionally unused now.
    """
    return

def check_saved_login():
    """
    SECURITY FIX: previously read a login token from a file on disk that
    was shared across ALL visitors on Streamlit Cloud, silently logging
    every new visitor in as whoever last checked "Remember me". Now
    always returns None - session state (per-browser, managed by
    Streamlit itself) is the only source of truth for login state.
    Kept as a stub so any existing callers don't break.
    """
    return None

def is_logged_in() -> bool:
    """
    Check if user is logged in

    Returns:
        Whether the user is logged in
    """
    return st.session_state.user_id is not None

def login(username: str, password: str):
    """
    Verify user and set session state

    Args:
        username: username
        password: password

    Returns:
        Returns user_id on success, None on failure
    """
    user_id = db_utils.verify_user(username, password)

    if user_id:
        st.session_state.user_id = user_id
        st.session_state.username = username
        return user_id
    else:
        return None

def logout():
    """
    Log out user, clear session state
    """
    st.session_state.user_id = None
    st.session_state.username = None

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
        submit = st.form_submit_button("Login")

        if submit:
            result = login(username, password)
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
    Display auth UI (login or register)
    """
    init_auth_state()

    # If already logged in, return directly
    if is_logged_in():
        return True

    # If not logged in, show login or register form
    if st.session_state.auth_page == 'login':
        show_login_form()
    else:
        show_register_form()

    return False
