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


def clear_user_data():
    """Clear all user-specific data from session state"""
    # List of keys to preserve during logout
    preserve_keys = {'auth_manager', 'authenticated', 'user_info', 'auth_page'}
    
    # Remove all user data except authentication-related keys
    keys_to_remove = [key for key in st.session_state.keys() if key not in preserve_keys]
    for key in keys_to_remove:
        del st.session_state[key]


def login_page():
    """Display login page"""
    
    # Center content with better spacing
    col1, col2, col3 = st.columns([1, 2.5, 1])

    with col2:
        # Add some top spacing
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Logo/Icon section
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 2rem;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">🎓</div>
                <h1 style="font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem;">Welcome to EduAI</h1>
                <p style="font-size: 1.1rem; color: #9ca3af;">Your AI-Powered Learning Companion</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form", clear_on_submit=False):
            st.markdown('<h3 style="text-align: center;">Sign In</h3>', unsafe_allow_html=True)
            
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

            submit = st.form_submit_button("Sign In", use_container_width=True, type="primary")

            if submit:
                if not username or not password:
                    st.error("⚠️ Please enter both username and password")
                else:
                    with st.spinner("Signing in..."):
                        result = st.session_state.auth_manager.authenticate_user(
                            username, password
                        )

                        if result["success"]:
                            # Clear any previous user's data before setting new user
                            clear_user_data()
                            
                            st.session_state.authenticated = True
                            st.session_state.user_info = result
                            st.session_state.session_token = result["session_token"]
                            st.success(f"✅ Welcome back, {result['username']}!")
                            st.rerun()
                        else:
                            st.error(f"❌ {result['error']}")

        # Divider
        st.markdown(
            """
            <div style="text-align: center; margin: 2rem 0;">
                <p style="color: #6b7280;">Don't have an account?</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Sign up button
        if st.button("Create New Account", use_container_width=True, type="secondary"):
            st.session_state.auth_page = "signup"
            st.rerun()


def signup_page():
    """Display signup page"""
    
    # Center content
    col1, col2, col3 = st.columns([1, 2.5, 1])

    with col2:
        # Add some top spacing
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Logo/Icon section
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 2rem;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">🚀</div>
                <h1 style="font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem;">Join EduAI</h1>
                <p style="font-size: 1.1rem; color: #9ca3af;">Start your learning journey today</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("signup_form", clear_on_submit=False):
            st.markdown('<h3 style="text-align: center;">Create Account</h3>', unsafe_allow_html=True)
            
            username = st.text_input(
                "Username",
                placeholder="Choose a username (min. 3 characters)",
                key="signup_username",
            )

            email = st.text_input(
                "Email",
                placeholder="your.email@example.com",
                key="signup_email",
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Create a strong password (min. 6 characters)",
                key="signup_password",
            )

            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                placeholder="Re-enter your password",
                key="signup_confirm",
            )

            submit = st.form_submit_button("Create Account", use_container_width=True, type="primary")

            if submit:
                # Validation
                if not username or not email or not password or not confirm_password:
                    st.error("⚠️ Please fill in all fields")
                elif password != confirm_password:
                    st.error("⚠️ Passwords do not match")
                elif len(password) < 6:
                    st.error("⚠️ Password must be at least 6 characters long")
                elif len(username) < 3:
                    st.error("⚠️ Username must be at least 3 characters long")
                elif "@" not in email or "." not in email:
                    st.error("⚠️ Please enter a valid email address")
                else:
                    with st.spinner("Creating your account..."):
                        result = st.session_state.auth_manager.create_user(
                            username, email, password
                        )

                        if result["success"]:
                            st.success("✅ Account created successfully!")
                            st.info("🔐 Redirecting to login page...")
                            # Automatically switch to login page after 2 seconds
                            import time
                            time.sleep(2)
                            st.session_state.auth_page = "login"
                            st.rerun()
                        else:
                            st.error(f"❌ {result['error']}")

        # Divider
        st.markdown(
            """
            <div style="text-align: center; margin: 2rem 0;">
                <p style="color: #6b7280;">Already have an account?</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Back to login button
        if st.button("Back to Sign In", use_container_width=True, type="secondary"):
            st.session_state.auth_page = "login"
            st.rerun()

        # Info footer
        st.markdown(
            """
            <div style="text-align: center; margin-top: 2rem; padding: 1rem; 
                        background-color: #374151; border-radius: 8px;">
                <p style="font-size: 0.85rem; color: #9ca3af; margin: 0;">
                    🔒 Your data is secure and encrypted<br>
                    📚 Start learning with AI-powered tools
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def show_auth_page():
    """Main authentication page controller"""
    init_auth_state()

    # If authenticated, don't show auth pages
    if st.session_state.authenticated:
        return True

    # Hide sidebar and default header for cleaner auth pages
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {display: none;}
            header {visibility: hidden;}
            .block-container {padding-top: 2rem;}
            
            /* Custom input styling */
            .stTextInput input {
                background-color: #374151 !important;
                border: 1px solid #4b5563 !important;
                border-radius: 8px !important;
                padding: 0.75rem !important;
                color: #f9fafb !important;
                font-size: 1rem !important;
            }
            
            .stTextInput input:focus {
                border-color: #3b82f6 !important;
                box-shadow: 0 0 0 1px #3b82f6 !important;
            }
            
            /* Button styling */
            .stButton button {
                border-radius: 8px !important;
                font-weight: 600 !important;
                padding: 0.75rem 1.5rem !important;
                transition: all 0.3s ease !important;
            }
            
            .stButton button[kind="primary"] {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                border: none !important;
            }
            
            .stButton button[kind="primary"]:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4) !important;
            }
            
            .stButton button[kind="secondary"] {
                background-color: transparent !important;
                border: 2px solid #4b5563 !important;
                color: #f9fafb !important;
            }
            
            .stButton button[kind="secondary"]:hover {
                border-color: #3b82f6 !important;
                background-color: #374151 !important;
            }
            
            /* Form styling */
            [data-testid="stForm"] {
                border: none !important;
                padding: 0 !important;
            }
            
            /* Hide labels */
            .stTextInput label {
                display: none !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

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

    # Clear all user data
    clear_user_data()
    
    st.session_state.authenticated = False
    st.session_state.user_info = None
    st.session_state.auth_page = "login"
    st.rerun()


def get_current_user_id():
    """Get the current authenticated user's ID"""
    if st.session_state.authenticated and st.session_state.user_info:
        return st.session_state.user_info.get('user_id')
    return None
