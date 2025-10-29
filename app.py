import streamlit as st
import os
import tempfile
from pathlib import Path
from build_vectorstore import embed_docs
from DocQA import DocumentQA
from MCQs import mcqs_generator
from Notes import notes_generator
from database import DatabaseManager

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
</style>
""",
    unsafe_allow_html=True,
)

# Initialize database
if "db_manager" not in st.session_state:
    st.session_state.db_manager = DatabaseManager()

# Initialize session state from database
if "initialized" not in st.session_state:
    st.session_state.initialized = True

    # Load app state from database
    app_state = st.session_state.db_manager.get_app_state()
    if app_state:
        st.session_state.vectorstore_ready = app_state["vectorstore_ready"]
        st.session_state.chat_state = app_state["chat_state"]
    else:
        st.session_state.vectorstore_ready = False
        st.session_state.chat_state = None

    st.session_state.qa_system = None
    st.session_state.current_page = "Upload Documents"
    st.session_state.messages_loaded = False
    st.session_state.show_session_manager = False


def load_messages_from_db():
    """Load messages from database into session state"""
    if not st.session_state.messages_loaded:
        conversation_history = st.session_state.db_manager.get_conversation_history()
        st.session_state.messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in conversation_history
        ]
        st.session_state.messages_loaded = True


def load_session(session_id: str):
    """Load a specific session"""
    st.session_state.db_session_id = session_id
    st.session_state.messages_loaded = False
    st.session_state.initialized = False

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


def main():

    st.markdown(
        '<h1 class="main-header">🎓 EduAI: AI Tutor</h1>', unsafe_allow_html=True
    )
    st.markdown(
        '<p class="sub-header">Your AI-Powered Learning Assistant</p>',
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.title("Navigation")

        pages = ["Upload Documents", "Ask Questions", "Generate Notes", "Create MCQs"]

        for page in pages:
            if st.button(page, key=f"nav_{page}", use_container_width=True):
                st.session_state.current_page = page
                st.rerun()

        st.markdown("---")
        st.subheader("System Status")
        if st.session_state.vectorstore_ready:
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
                st.session_state.db_manager.clear_conversation()
                st.session_state.messages = []
                st.session_state.messages_loaded = False
                st.success("Chat history cleared!")
                st.rerun()

        with col2:
            if st.button("🗑️ Reset All", use_container_width=True):
                st.session_state.db_manager.delete_session()
                st.session_state.vectorstore_ready = False
                st.session_state.chat_state = None
                st.session_state.qa_system = None
                st.session_state.messages = []
                st.session_state.messages_loaded = False
                st.success("Session reset!")
                st.rerun()

        if st.button("📂 Manage Sessions", use_container_width=True):
            st.session_state.show_session_manager = (
                not st.session_state.show_session_manager
            )
            st.rerun()

        if st.session_state.show_session_manager:
            st.markdown("---")
            st.subheader("Your Sessions")

            # Get current session
            current_session_id = st.session_state.db_manager.get_session_id()
            sessions = st.session_state.db_manager.get_all_sessions()

            # New Session button
            if st.button("➕ New Session", use_container_width=True, type="primary"):
                import time

                new_session_id = f"session_{int(time.time() * 1000000)}"
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

    page = st.session_state.current_page
    if page == "Upload Documents":
        upload_documents_page()
    elif page == "Ask Questions":
        ask_questions_page()
    elif page == "Generate Notes":
        generate_notes_page()
    elif page == "Create MCQs":
        create_mcqs_page()


def upload_documents_page():
    st.header("📤 Upload Your Study Documents")

    st.markdown(
        """
    <div class="feature-box">
        <h4>Document Upload</h4>
        <p>Upload your PDF documents to create a knowledge base for AI-powered learning.</p>
        <ul>
            <li>Supports multiple PDF files</li>
            <li>Automatically processes and indexes content</li>
            <li>Creates searchable vector embeddings</li>
        </ul>
    </div>
    """,
        unsafe_allow_html=True,
    )

    uploaded_docs = st.session_state.db_manager.get_documents()
    if uploaded_docs:
        st.markdown("### Previously Uploaded Documents")
        with st.expander("View document history"):
            for doc in uploaded_docs:
                st.write(f"• {doc['filename']} ({doc['file_size']} bytes)")

    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload one or more PDF files to build your knowledge base",
    )

    if uploaded_files:
        st.success(f"{len(uploaded_files)} file(s) selected")

        with st.expander("View uploaded files"):
            for file in uploaded_files:
                st.write(f"• {file.name} ({file.size} bytes)")

        if st.button("Process Documents", type="primary"):
            process_documents(uploaded_files)


def process_documents(uploaded_files):
    """Process uploaded documents and create vector store"""
    try:
        with st.spinner("Processing documents... This may take a few moments."):
            with tempfile.TemporaryDirectory() as temp_dir:
                # Collect filenames for session naming
                filenames = []
                for uploaded_file in uploaded_files:
                    file_path = os.path.join(temp_dir, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    filenames.append(uploaded_file.name.replace(".pdf", ""))
                    st.session_state.db_manager.save_document(
                        uploaded_file.name, uploaded_file.size
                    )

                # Name session based on uploaded files
                if filenames:
                    if len(filenames) == 1:
                        session_name = filenames[0]
                    elif len(filenames) <= 3:
                        session_name = ", ".join(filenames)
                    else:
                        session_name = (
                            ", ".join(filenames[:3]) + f" (+{len(filenames) - 3} more)"
                        )

                    st.session_state.db_manager.rename_session(
                        st.session_state.db_manager.get_session_id(), session_name
                    )

                faiss_path = "faiss_index_local"
                embed_docs(temp_dir, faiss_path)

                st.session_state.vectorstore_ready = True
                st.session_state.qa_system = None

                st.session_state.db_manager.save_app_state(
                    vectorstore_ready=True, chat_state=st.session_state.chat_state
                )

        st.markdown(
            """
        <div class="success-message">
            <h4>✓ Success!</h4>
            <p>Documents have been processed and indexed successfully. You can now:</p>
            <ul>
                <li>Ask questions about your documents</li>
                <li>Generate comprehensive notes</li>
                <li>Create practice MCQs</li>
            </ul>
        </div>
        """,
            unsafe_allow_html=True,
        )

    except Exception as e:
        st.error(f"Error processing documents: {str(e)}")
        st.info(
            "Make sure you have set up your OpenAI API key in your environment variables."
        )


def ask_questions_page():
    st.header("💬 Ask Questions About Your Documents")

    if not st.session_state.vectorstore_ready:
        st.markdown(
            """
        <div class="warning-message">
            <h4>⚠ No Documents Loaded</h4>
            <p>Please upload and process documents first using the "Upload Documents" page.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        """
    <div class="feature-box">
        <h4>AI-Powered Q&A</h4>
        <p>Ask any question about your uploaded documents and get intelligent, context-aware answers with streaming responses.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Initialize QA system if needed
    if st.session_state.qa_system is None:
        with st.spinner("Initializing Q&A system..."):
            st.session_state.qa_system = DocumentQA()

            # Restore chat state from database if available
            if st.session_state.chat_state:
                st.session_state.chat_state = st.session_state.qa_system.restore_state(
                    st.session_state.chat_state
                )
            else:
                st.session_state.chat_state = st.session_state.qa_system.init_state()

    load_messages_from_db()

    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(
                f'<div class="chat-message user-message"><strong>You:</strong> {message["content"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="chat-message assistant-message"><strong>Assistant:</strong> {message["content"]}</div>',
                unsafe_allow_html=True,
            )

    if prompt := st.chat_input("Ask a question about your documents..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.db_manager.save_message("user", prompt)

        st.markdown(
            f'<div class="chat-message user-message"><strong>You:</strong> {prompt}</div>',
            unsafe_allow_html=True,
        )

        with st.container():
            message_placeholder = st.empty()
            full_response = ""

            try:
                for chunk in st.session_state.qa_system.run_stream(
                    prompt, st.session_state.chat_state
                ):
                    if "response_chunk" in chunk:
                        full_response += chunk["response_chunk"]
                        message_placeholder.markdown(
                            f'<div class="chat-message assistant-message"><strong>Assistant:</strong> {full_response}▌</div>',
                            unsafe_allow_html=True,
                        )
                    elif "state" in chunk:
                        st.session_state.chat_state = chunk["state"]

                message_placeholder.markdown(
                    f'<div class="chat-message assistant-message"><strong>Assistant:</strong> {full_response}</div>',
                    unsafe_allow_html=True,
                )

                st.session_state.messages.append(
                    {"role": "assistant", "content": full_response}
                )
                st.session_state.db_manager.save_message("assistant", full_response)

                # Serialize and save chat state to database
                serialized_state = st.session_state.qa_system.serialize_state(
                    st.session_state.chat_state
                )
                st.session_state.db_manager.save_app_state(
                    vectorstore_ready=st.session_state.vectorstore_ready,
                    chat_state=serialized_state,
                )

            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )
                st.session_state.db_manager.save_message("assistant", error_msg)


def generate_notes_page():
    st.header("📝 Generate Study Notes")

    if not st.session_state.vectorstore_ready:
        st.markdown(
            """
        <div class="warning-message">
            <h4>⚠ No Documents Loaded</h4>
            <p>Please upload and process documents first using the "Upload Documents" page.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        """
    <div class="feature-box">
        <h4>Comprehensive Notes Generation</h4>
        <p>Generate well-structured study notes from your documents with:</p>
        <ul>
            <li>Key concepts and definitions</li>
            <li>Important facts and examples</li>
            <li>Clear bullet-point formatting</li>
            <li>Logical organization</li>
        </ul>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Load existing notes if available
    existing_notes = st.session_state.db_manager.get_generated_content("notes")

    if existing_notes:
        st.success("Previously generated notes found!")
        st.markdown("### Your Study Notes")
        st.markdown("---")
        st.markdown(existing_notes)

        st.download_button(
            label="📥 Download Notes",
            data=existing_notes,
            file_name="study_notes.txt",
            mime="text/plain",
        )

        st.markdown("---")

    if st.button("🔄 Generate New Notes", type="primary"):
        message_placeholder = st.empty()
        full_response = ""

        with st.spinner("Generating comprehensive notes..."):
            try:
                notes_gen = notes_generator()
                state = notes_gen.init_state()

                for chunk in notes_gen.run_stream(state):
                    if "response_chunk" in chunk:
                        full_response += chunk["response_chunk"]
                        message_placeholder.markdown(f"{full_response}▌")

                message_placeholder.markdown(full_response)

                # Save to database
                st.session_state.db_manager.save_generated_content(
                    "notes", full_response
                )

                st.success("Notes generated successfully!")

                st.download_button(
                    label="📥 Download Notes",
                    data=full_response,
                    file_name="study_notes.txt",
                    mime="text/plain",
                )

            except Exception as e:
                st.error(f"Error generating notes: {str(e)}")


def create_mcqs_page():
    st.header("📋 Create Practice MCQs")

    if not st.session_state.vectorstore_ready:
        st.markdown(
            """
        <div class="warning-message">
            <h4>⚠ No Documents Loaded</h4>
            <p>Please upload and process documents first using the "Upload Documents" page.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        """
    <div class="feature-box">
        <h4>Practice Questions Generator</h4>
        <p>Generate multiple-choice questions for exam preparation:</p>
        <ul>
            <li>10 carefully crafted MCQs</li>
            <li>4 options per question (A, B, C, D)</li>
            <li>Mixed difficulty levels</li>
            <li>Complete answer key provided</li>
        </ul>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Load existing MCQs if available
    existing_mcqs = st.session_state.db_manager.get_generated_content("mcqs")

    if existing_mcqs:
        st.success("Previously generated MCQs found!")
        st.markdown("### Practice Questions")
        st.markdown("---")
        st.markdown(existing_mcqs)

        st.download_button(
            label="📥 Download MCQs",
            data=existing_mcqs,
            file_name="practice_mcqs.txt",
            mime="text/plain",
        )

        st.markdown("---")

    if st.button("🔄 Generate New MCQs", type="primary"):
        message_placeholder = st.empty()
        full_response = ""

        with st.spinner("Creating practice questions..."):
            try:
                mcq_gen = mcqs_generator()
                state = mcq_gen.init_state()

                for chunk in mcq_gen.run_stream(state):
                    if "response_chunk" in chunk:
                        full_response += chunk["response_chunk"]
                        message_placeholder.markdown(f"{full_response}▌")

                message_placeholder.markdown(full_response)

                # Save to database
                st.session_state.db_manager.save_generated_content(
                    "mcqs", full_response
                )

                st.success("MCQs generated successfully!")

                st.download_button(
                    label="📥 Download MCQs",
                    data=full_response,
                    file_name="practice_mcqs.txt",
                    mime="text/plain",
                )

            except Exception as e:
                st.error(f"Error generating MCQs: {str(e)}")


if __name__ == "__main__":
    main()
