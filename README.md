# EduAI-Tutor
An intelligent AI-powered educational assistant that transforms PDF documents into interactive learning experiences. Upload study materials and get instant Q&A, auto-generated MCQs, and comprehensive study notes.
Features:

1. PDF Document Processing: Upload and index PDF documents for intelligent content retrieval
2. Interactive Q&A: Ask questions about your study materials and get contextual answers
3. MCQ Generation: Automatically generate multiple-choice questions for self-assessment
4. Study Notes Creation: Convert PDF content into well-structured, bullet-pointed study notes
5. Vector-based Search: Uses FAISS for efficient similarity search and content retrieval

Architecture:

The application uses a graph-based approach with LangGraph for processing workflows:

Document Ingestion: PDFs are chunked and embedded into a FAISS vector store
Query Processing: User queries are processed through retrieval-augmented generation (RAG)
Content Generation: Three specialized modules handle different educational tasks

Future Enhancements:

-FastAPI for backend
-Multi-language support

How to run:

1. Download the repo in your systems
2. Add your OpenAI API key in the .env file
3. In the terminal window hit - > "streamlit run main.py"
