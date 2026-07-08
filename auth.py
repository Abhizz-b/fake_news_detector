import streamlit as st
import db_utils
import hashlib
import time
import json
import os

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
    Initialize auth-related session state
    """
    # Check if login state already exists
    if 'user_id' not in st.session_state or st.session_state.user_id is None:
        # Check if persisted login data exists in session state
        if 'persisted_login' in st.session_state:
            saved_login = st.session_state.persisted_login
            # Check if expired
            if saved_login["expires"] > int(time.time()):
                st.session_state.user_id = saved_login['user_id']
                st.session_state.username = saved_login['username']
            else:
                # Expired, clear it
                del st.session_state.persisted_login
                st.session_state.user_id = None
                st.session_state.username = None
        else:
            # Check if saved login state exists in file
            saved_login = check_saved_login()
            if saved_login:
                st.session_state.user_id = saved_login['user_id']
                st.session_state.username = saved_login['username']
                # Also save to session state for next time
                st.session_state.persisted_login = saved_login
            else:
                st.session_state.user_id = None
                st.session_state.username = None

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

def get_login_cache_file():
    """Get login cache file path"""
    return "data/.login_cache.json"

def save_login_state(username: str, user_id: int, remember: bool = False):
    """
    Save login state to local file and session state
    """
    if remember:
        token = generate_login_token(username)
        login_data = {
            "username": username,
            "user_id": user_id,
            "token": token,
            "expires": int(time.time()) + (30 * 24 * 3600)  # 30 days
        }

        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)

        # Save to file
        try:
            cache_file = get_login_cache_file()
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(login_data, f)

            # Save to session state - this is key!
            st.session_state.persisted_login = login_data

        except Exception as e:
            st.warning(f"Failed to save login state: {e}")
    else:
        # Clear saved login state
        try:
            cache_file = get_login_cache_file()
            if os.path.exists(cache_file):
                os.remove(cache_file)
        except Exception:
            pass

        # Clear session state
        if "persisted_login" in st.session_state:
            del st.session_state.persisted_login

def check_saved_login():
    """
    Check if a valid saved login state exists
    """
    try:
        cache_file = get_login_cache_file()
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                saved = json.load(f)

            # Check if expired
            current_time = int(time.time())
            if saved["expires"] > current_time:
                # Return saved login data
                return saved
            else:
                # Expired, delete cache file
                os.remove(cache_file)
    except Exception:
        # File corrupted or read failed, delete cache file
        try:
            if os.path.exists(get_login_cache_file()):
                os.remove(get_login_cache_file())
        except Exception:
            pass

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

    # Clear saved login state
    save_login_state("", 0, remember=False)

    # Clear auto-login check flag, will recheck on next startup
    if "auto_login_checked" in st.session_state:
        del st.session_state.auto_login_checked

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
        remember_me = st.checkbox("Remember me", help="If checked, no need to log in again for 30 days")
        submit = st.form_submit_button("Login")

        if submit:
            result = login(username, password)
            if result:
                # Save login state
                save_login_state(username, result, remember_me)
                st.success("Login successful!" + (" Login state saved" if remember_me else ""))
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