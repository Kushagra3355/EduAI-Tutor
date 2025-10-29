import streamlit as st
import os
import tempfile
from pathlib import Path
from build_vectorstore import embed_docs
from DocQA import DocumentQA
from MCQs import mcqs_generator
from Notes import notes_generator
from database import DatabaseManager
from auth_pages import show_auth_page, logout_user, get_current_user_id

try:
    if "OPENAI_API_KEY" in st.secrets:
        os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
except FileNotFoundError:
    # secrets.toml not found, will use .env file instead
    from dotenv import load_dotenv
    load_dotenv()


st.set_page_config(
    page_title="EduAI - AI-Powered Learning Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .main-header {
        text-align: center;
        color: #ffffff;
        font-size: 3rem;
        margin-bottom: 2rem;
        font-weight: 700;
    }
    .sub-header {
        text-align: center;
        color: #e5e7eb;
        font-size: 1.2rem;
        margin-bottom: 3rem;
        font-weight: 400;
    }
    .feature-box {
        background-color: #374151;
        color: #f9fafb;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #3b82f6;
        border: 1px solid #4b5563;
    }
    .success-message {
        background-color: #065f46;
        color: #d1fae5;
        padding: 1rem;
        border-radius: 6px;
        margin: 1rem 0;
        border: 1px solid #10b981;
    }
    .warning-message {
        background-color: #92400e;
        color: #fef3c7;
        padding: 1rem;
        border-radius: 6px;
        margin: 1rem 0;
        border: 1px solid #f59e0b;
    }
    .stApp {
        background-color: #1f2937;
        color: #f9fafb;
    }
    .sidebar .sidebar-content {
        background-color: #111827;
    }
    .chat-message {
        background-color: #374151;
        color: #f9fafb;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 6px;
        border: 1px solid #4b5563;
    }
    .user-message {
        background-color: #1e3a8a;
        color: #dbeafe;
        border-left: 4px solid #3b82f6;
    }
    .assistant-message {
        background-color: #0c4a6e;
        color: #e0f2fe;
        border-left: 4px solid #0ea5e9;
    }
    .status-ready {
        background-color: #065f46;
        color: #d1fae5;
        padding: 0.5rem;
        border-radius: 4px;
        border: 1px solid #10b981;
        font-weight: 600;
    }
    .status-pending {
        background-color: #92400e;
        color: #fef3c7;
        padding: 0.5rem;
        border-radius: 4px;
        border: 1px solid #f59e0b;
        font-weight: 600;
    }
    .session-item {
        background-color: #374151;
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 6px;
        border: 1px solid #4b5563;
        cursor: pointer;
        transition: all 0.2s;
    }
    .session-item:hover {
        background-color: #4b5563;
        border-color: #3b82f6;
    }
    .session-item.active {
        background-color: #1e3a8a;
        border-color: #3b82f6;
    }
    .stMarkdown, .stText, h1, h2, h3, h4, h5, h6, p, div {
        color: #f9fafb !important;
    }
    .stSelectbox label, .stFileUploader label {
        color: #f9fafb !important;
    }
    .user-info-box {
        background-color: #1e3a8a;
        color: #dbeafe;
        padding: 1rem;
        border-radius: 6px;
        margin: 1rem 0;
        border: 1px solid #3b82f6;
    }
</style>
""",
    unsafe_allow_html=True,
)


def initialize_user_session():
    """Initialize or reinitialize session for current user"""
    current_user_id = get_current_user_id()
    
    # If no user is authenticated, don't initialize
    if current_user_id is None:
        return
    
    # Check if we need to reinitialize for a different user
    if "current_user_id" not in st.session_state or st.session_state.current_user_id != current_user_id:
        # Clear all session state except auth-related keys
        keys_to_preserve = {'auth_manager', 'authenticated', 'user_info', 'session_token', 'auth_page'}
        keys_to_remove = [key for key in st.session_state.keys() if key not in keys_to_preserve]
        for key in keys_to_remove:
            del st.session_state[key]
        
        # Set current user ID
        st.session_state.current_user_id = current_user_id
        
        # Initialize database manager with user ID
        st.session_state.db_manager = DatabaseManager(user_id=current_user_id)
        
        # Initialize app state
        try:
            app_state = st.session_state.db_manager.get_app_state()
            if app_state:
                st.session_state.vectorstore_ready = app_state["vectorstore_ready"]
                st.session_state.chat_state = app_state["chat_state"]
            else:
                st.session_state.vectorstore_ready = False
                st.session_state.chat_state = None
        except Exception as e:
            print(f"Error loading app state: {e}")
            st.session_state.vectorstore_ready = False
            st.session_state.chat_state = None

        st.session_state.qa_system = None
        st.session_state.current_page = "Upload Documents"
        st.session_state.messages_loaded = False
        st.session_state.show_session_manager = False
        st.session_state.initialized = True


def load_messages_from_db():
    """Load messages from database into session state"""
    if "messages_loaded" not in st.session_state or not st.session_state.messages_loaded:
        try:
            conversation_history = st.session_state.db_manager.get_conversation_history()
            st.session_state.messages = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in conversation_history
            ]
            st.session_state.messages_loaded = True
        except Exception as e:
            print(f"Error loading messages: {e}")
            st.session_state.messages = []
            st.session_state.messages_loaded = True


def load_session(session_id: str):
    """Load a specific session"""
    try:
        # Update session ID
        st.session_state.db_session_id = session_id
        st.session_state.messages_loaded = False

        # Load app state for this session
        app_state = st.session_state.db_manager.get_app_state(session_id)
        if app_state:
            st.session_state.vectorstore_ready = app_state["vectorstore_ready"]
            st.session_state.chat_state = app_state["chat_state"]
        else:
            st.session_state.vectorstore_ready = False
            st.session_state.chat_state = None

        # Reset QA system to force reinitialization with new state
        st.session_state.qa_system = None
        st.session_state.show_session_manager = False
        st.rerun()
    except Exception as e:
        st.error(f"Error loading session: {e}")


def main():
    # Check authentication first
    if not show_auth_page():
        return  # If not authenticated, show auth page and return

    # User is authenticated, initialize user-specific session
    initialize_user_session()

    st.markdown(
        '<h1 class="main-header">🎓 EduAI: AI Tutor</h1>', unsafe_allow_html=True
    )
    st.markdown(
        '<p class="sub-header">Your AI-Powered Learning Assistant</p>',
        unsafe_allow_html=True,
    )

    with st.sidebar:
        # Display user info
        if st.session_state.user_info:
            st.markdown(
                f"""
            <div class="user-info-box">
                <strong>👤 {st.session_state.user_info['username']}</strong><br>
                <small>{st.session_state.user_info['email']}</small>
            </div>
            """,
                unsafe_allow_html=True,
            )

        if st.button("🚪 Logout", use_container_width=True):
            logout_user()

        st.markdown("---")
        st.title("Navigation")

        pages = ["Upload Documents", "Ask Questions", "Generate Notes", "Create MCQs"]

        for page in pages:
            if st.button(page, key=f"nav_{page}", use_container_width=True):
                st.session_state.current_page = page
                st.rerun()

        st.markdown("---")
        st.subheader("System Status")
        if st.session_state.get("vectorstore_ready", False):
            st.markdown(
                '<div class="status-ready">✓ Documents loaded and ready</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="status-pending">⚠ Please upload documents first</div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.subheader("Session Management")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Clear Chat", use_container_width=True):
                try:
                    st.session_state.db_manager.clear_conversation()
                    st.session_state.messages = []
                    st.session_state.messages_loaded = False
                    st.success("Chat history cleared!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error clearing chat: {e}")

        with col2:
            if st.button("🗑️ Reset All", use_container_width=True):
                try:
                    st.session_state.db_manager.delete_session()
                    st.session_state.vectorstore_ready = False
                    st.session_state.chat_state = None
                    st.session_state.qa_system = None
                    st.session_state.messages = []
                    st.session_state.messages_loaded = False
                    st.success("Session reset!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error resetting session: {e}")

        if st.button("📂 Manage Sessions", use_container_width=True):
            st.session_state.show_session_manager = (
                not st.session_state.get("show_session_manager", False)
            )
            st.rerun()

        if st.session_state.get("show_session_manager", False):
            st.markdown("---")
            st.subheader("Your Sessions")

            try:
                # Get current session
                current_session_id = st.session_state.db_manager.get_session_id()
                sessions = st.session_state.db_manager.get_all_sessions()

                # New Session button
                if st.button("➕ New Session", use_container_width=True, type="primary"):
                    import time
                    user_id = get_current_user_id()
                    new_session_id = f"session_{user_id}_{int(time.time() * 1000000)}"
                    st.session_state.db_manager.create_session(
                        new_session_id, "Untitled Session"
                    )
                    load_session(new_session_id)

                st.markdown("**All Sessions:**")

                if not sessions:
                    st.info("No sessions yet. Upload documents to get started!")

                for session in sessions:
                    is_active = session["session_id"] == current_session_id

                    # Display session name and message count
                    display_name = session["session_name"]
                    button_label = f"{'▶ ' if is_active else ''}{display_name}"
                    if session["message_count"] > 0:
                        button_label += f" ({session['message_count']} msgs)"

                    if st.button(
                        button_label,
                        key=f"session_{session['session_id']}",
                        use_container_width=True,
                        disabled=is_active,
                    ):
                        load_session(session["session_id"])
            except Exception as e:
                st.error(f"Error managing sessions: {e}")

    # Get current page from session state
    page = st.session_state.get("current_page", "Upload Documents")
    
    if page == "Upload Documents":
        upload_documents_page()
    elif page == "Ask Questions":
        ask_questions_page()
    elif page == "Generate Notes":
        generate_notes_page()
    elif page == "Create MCQs":
        create_mcqs_page()


if __name__ == "__main__":
    main()
