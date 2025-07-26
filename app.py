import streamlit as st
import os
import tempfile
from pathlib import Path
from build_vectorstore import embed_docs
from DocQA import DocumentQA
from MCQs import mcqs_generator
from Notes import notes_generator

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
    .nav-button {
        width: 100%;
        margin: 0.5rem 0;
        padding: 1rem;
        background-color: #374151;
        color: #f9fafb;
        border: 1px solid #4b5563;
        border-radius: 6px;
        text-align: left;
        cursor: pointer;
        font-size: 1rem;
        font-weight: 500;
    }
    .nav-button:hover {
        background-color: #4b5563;
    }
    .nav-button.active {
        background-color: #3b82f6;
        border-color: #2563eb;
    }
    /* Override Streamlit default styles */
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

if "vectorstore_ready" not in st.session_state:
    st.session_state.vectorstore_ready = False
if "chat_state" not in st.session_state:
    st.session_state.chat_state = None
if "qa_system" not in st.session_state:
    st.session_state.qa_system = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "Upload Documents"


def main():
    
    st.markdown('<h1 class="main-header">EduAI: AI Tutor</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Your AI-Powered Learning Assistant</p>',
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.title("Navigation")

        pages = ["Upload Documents", "Ask Questions", "Generate Notes", "Create MCQs"]

        for page in pages:
            button_class = (
                "nav-button active"
                if st.session_state.current_page == page
                else "nav-button"
            )
            if st.button(page, key=f"nav_{page}", use_container_width=True):
                st.session_state.current_page = page
                st.rerun()

        st.markdown("---")
        st.subheader("System Status")
        if st.session_state.vectorstore_ready:
            st.markdown(
                '<div class="status-ready">Documents loaded and ready</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="status-pending">Please upload documents first</div>',
                unsafe_allow_html=True,
            )

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
    st.header("Upload Your Study Documents")

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
                for uploaded_file in uploaded_files:
                    file_path = os.path.join(temp_dir, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                faiss_path = "faiss_index_local"
                embed_docs(temp_dir, faiss_path)

                st.session_state.vectorstore_ready = True
                st.session_state.qa_system = (
                    None  
                )

        st.markdown(
            """
        <div class="success-message">
            <h4>Success!</h4>
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
    st.header("Ask Questions About Your Documents")

    if not st.session_state.vectorstore_ready:
        st.markdown(
            """
        <div class="warning-message">
            <h4>No Documents Loaded</h4>
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
        <p>Ask any question about your uploaded documents and get intelligent, context-aware answers.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if st.session_state.qa_system is None:
        with st.spinner("Initializing Q&A system..."):
            st.session_state.qa_system = DocumentQA()
            st.session_state.chat_state = st.session_state.qa_system.init_state()

    if "messages" not in st.session_state:
        st.session_state.messages = []

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

        with st.spinner("Processing your question..."):
            try:
                result = st.session_state.qa_system.run(
                    prompt, st.session_state.chat_state
                )
                st.session_state.chat_state = result
                response = result["response"]
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )
                st.rerun()
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )
                st.rerun()


def generate_notes_page():
    st.header("Generate Study Notes")

    if not st.session_state.vectorstore_ready:
        st.markdown(
            """
        <div class="warning-message">
            <h4>No Documents Loaded</h4>
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

    if st.button("Generate Notes", type="primary"):
        with st.spinner("Generating comprehensive notes..."):
            try:
                notes_gen = notes_generator()
                state = notes_gen.init_state()
                result = notes_gen.run(state)

                st.success("Notes generated successfully!")

                st.markdown("### Your Study Notes")
                st.markdown("---")
                st.markdown(result["response"])

                st.download_button(
                    label="Download Notes",
                    data=result["response"],
                    file_name="study_notes.txt",
                    mime="text/plain",
                )

            except Exception as e:
                st.error(f"Error generating notes: {str(e)}")


def create_mcqs_page():
    st.header("Create Practice MCQs")

    if not st.session_state.vectorstore_ready:
        st.markdown(
            """
        <div class="warning-message">
            <h4>No Documents Loaded</h4>
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

    if st.button("Generate MCQs", type="primary"):
        with st.spinner("Creating practice questions..."):
            try:
                mcq_gen = mcqs_generator()
                state = mcq_gen.init_state()
                result = mcq_gen.run(state)

                st.success("MCQs generated successfully!")

                st.markdown("### Practice Questions")
                st.markdown("---")
                st.markdown(result["response"])

                st.download_button(
                    label="Download MCQs",
                    data=result["response"],
                    file_name="practice_mcqs.txt",
                    mime="text/plain",
                )

            except Exception as e:
                st.error(f"Error generating MCQs: {str(e)}")


def show_footer():
    pass


if __name__ == "__main__":
    main()
    show_footer()
