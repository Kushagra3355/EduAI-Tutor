import streamlit as st
from auth_manager import AuthManager


def init_auth_state():
    """Initialize authentication state"""
    if "auth_manager" not in st.session_state:
        st.session_state.auth_manager = AuthManager()

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user_info = None

    # Check for existing session
    if not st.session_state.authenticated and "session_token" in st.session_state:
        user_info = st.session_state.auth_manager.verify_session(
            st.session_state.session_token
        )
        if user_info:
            st.session_state.authenticated = True
            st.session_state.user_info = user_info


def login_page():
    """Display login page"""
    st.markdown(
        '<h1 class="main-header">🎓 EduAI Login</h1>', unsafe_allow_html=True
    )
    st.markdown(
        '<p class="sub-header">Sign in to access your AI Learning Assistant</p>',
        unsafe_allow_html=True,
    )

    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown(
            """
        <div class="feature-box" style="margin-top: 2rem;">
            <h3 style="text-align: center; margin-bottom: 1.5rem;">Sign In</h3>
        </div>
        """,
            unsafe_allow_html=True,
        )

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input(
                "Username or Email",
                placeholder="Enter your username or email",
                key="login_username",
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password",
            )

            col_a, col_b, col_c = st.columns([1, 2, 1])
            with col_b:
                submit = st.form_submit_button("Login", use_container_width=True)

            if submit:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    result = st.session_state.auth_manager.authenticate_user(
                        username, password
                    )

                    if result["success"]:
                        st.session_state.authenticated = True
                        st.session_state.user_info = result
                        st.session_state.session_token = result["session_token"]
                        st.success(f"Welcome back, {result['username']}!")
                        st.rerun()
                    else:
                        st.error(result["error"])

        st.markdown("---")
        st.markdown(
            "<p style='text-align: center;'>Don't have an account?</p>",
            unsafe_allow_html=True,
        )
        col_x, col_y, col_z = st.columns([1, 2, 1])
        with col_y:
            if st.button("Create Account", use_container_width=True):
                st.session_state.auth_page = "signup"
                st.rerun()


def signup_page():
    """Display signup page"""
    st.markdown(
        '<h1 class="main-header">🎓 Create Your EduAI Account</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="sub-header">Join thousands of students learning smarter with AI</p>',
        unsafe_allow_html=True,
    )

    # Center the signup form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown(
            """
        <div class="feature-box" style="margin-top: 2rem;">
            <h3 style="text-align: center; margin-bottom: 1.5rem;">Sign Up</h3>
        </div>
        """,
            unsafe_allow_html=True,
        )

        with st.form("signup_form", clear_on_submit=False):
            username = st.text_input(
                "Username",
                placeholder="Choose a username (min. 3 characters)",
                key="signup_username",
            )
            email = st.text_input(
                "Email",
                placeholder="Enter your email address",
                key="signup_email",
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Create a password (min. 6 characters)",
                key="signup_password",
            )
            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                placeholder="Re-enter your password",
                key="signup_confirm",
            )

            col_a, col_b, col_c = st.columns([1, 2, 1])
            with col_b:
                submit = st.form_submit_button("Create Account", use_container_width=True)

            if submit:
                # Validation
                if not username or not email or not password or not confirm_password:
                    st.error("Please fill in all fields")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    result = st.session_state.auth_manager.create_user(
                        username, email, password
                    )

                    if result["success"]:
                        st.success(
                            "Account created successfully! Please log in to continue."
                        )
                        st.balloons()
                        # Automatically switch to login page after 2 seconds
                        import time

                        time.sleep(2)
                        st.session_state.auth_page = "login"
                        st.rerun()
                    else:
                        st.error(result["error"])

        st.markdown("---")
        st.markdown(
            "<p style='text-align: center;'>Already have an account?</p>",
            unsafe_allow_html=True,
        )
        col_x, col_y, col_z = st.columns([1, 2, 1])
        with col_y:
            if st.button("Back to Login", use_container_width=True):
                st.session_state.auth_page = "login"
                st.rerun()


def show_auth_page():
    """Main authentication page controller"""
    init_auth_state()

    # If authenticated, don't show auth pages
    if st.session_state.authenticated:
        return True

    # Determine which page to show
    if "auth_page" not in st.session_state:
        st.session_state.auth_page = "login"

    if st.session_state.auth_page == "login":
        login_page()
    else:
        signup_page()

    return False


def logout_user():
    """Handle user logout"""
    if "session_token" in st.session_state:
        st.session_state.auth_manager.logout(st.session_state.session_token)
        del st.session_state.session_token

    st.session_state.authenticated = False
    st.session_state.user_info = None
    st.session_state.auth_page = "login"
    st.rerun()
