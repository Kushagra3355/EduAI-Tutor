# 🎓 EduAI – AI-Powered Learning Assistant

EduAI is an interactive **AI-powered study assistant** built with **Streamlit**, **LangChain**, **LangGraph**, and **OpenAI models**.  
It allows users to upload PDF study materials and then:

- Ask intelligent, context-aware questions  
- Generate structured study notes  
- Create exam-ready multiple-choice questions (MCQs)  
- Manage multiple learning sessions with persistent memory  

The system uses **Retrieval-Augmented Generation (RAG)** with **FAISS vector search** and **SQLite** for persistent storage.

---

## 📚 Table of Contents

- Features  
- Project Structure  
- Installation  
- Configuration  
- Usage  
- Core Components  
- Database Design  
- Technologies Used  
- Troubleshooting  
- Future Enhancements  
- License  

---

## ✨ Features

- 📤 Upload multiple PDF documents  
- 🔎 Semantic document-based question answering  
- 📝 Automatic study notes generation  
- 📋 MCQ generation with answer keys  
- 💬 Streaming AI responses  
- 🗂️ Session-based learning with history  
- 💾 Persistent storage using SQLite  
- 🎨 Modern dark-themed Streamlit UI  

---

## 🏗 Project Structure

EduAI/
│
├── app.py                  # Main Streamlit application  
├── build_vectorstore.py    # PDF embedding and FAISS index creation  
├── DocQA.py                # Retrieval-Augmented Q&A system  
├── Notes.py                # Study notes generator  
├── MCQs.py                 # MCQ generator  
├── database.py             # SQLite database manager  
├── auth_manager.py         # (Optional) Authentication logic  
├── auth_pages.py           # (Optional) Login & signup UI  
├── faiss_index_local/      # Generated FAISS vector store  
└── eduai_data.db           # SQLite database (auto-generated)  

---

## ⚙️ Installation

### 1. Clone the Repository
git clone https://github.com/Kushagra3355/EduAI-Tutor.git
cd eduai  

### 2. Create a Virtual Environment
python -m venv venv  
source venv/bin/activate  

### 3. Install Dependencies
pip install -r requirements.txt  

---

## 🔐 Configuration

Set your OpenAI API key:

export OPENAI_API_KEY="your-api-key"

or using Streamlit secrets:

OPENAI_API_KEY="your-api-key"

---

## 🚀 Usage

Run the application:

streamlit run app.py

1. Upload PDF documents  
2. Process documents  
3. Ask questions / Generate notes / Create MCQs  
4. Download generated content  

---

## 🧠 Core Components

- **Document Q&A** – Context-aware question answering using FAISS + LLM  
- **Notes Generator** – Structured academic notes generation  
- **MCQ Generator** – Exam-ready multiple-choice questions  
- **Database Manager** – Persistent session & content storage  

---

## 🗃 Database Design

Tables:
- sessions  
- conversations  
- documents  
- generated_content  
- app_state  

---

## 🧰 Technologies Used

- Streamlit  
- LangChain & LangGraph  
- OpenAI GPT Models  
- FAISS  
- SQLite  
- Python  

---

## 🛠 Troubleshooting

- Ensure documents are uploaded before querying  
- Verify OpenAI API key  
- Large PDFs may take time to process  

---

## 🚧 Future Enhancements

- User authentication  
- Support for DOCX/TXT  
- Cloud vector storage  
- Multi-user support  

---

## 📄 License

MIT License  

---
