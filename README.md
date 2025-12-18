# 🎓 EduAI – AI-Powered Learning Assistant

EduAI is an **AI-powered learning assistant** built using **Streamlit**, **LangChain**, **LangGraph**, **FAISS**, and **OpenAI models**.  
It helps students learn more effectively by allowing them to upload study materials (PDFs) and then:

- Ask questions based on the content
- Generate structured study notes
- Create practice MCQs
- Maintain learning sessions with persistent memory

EduAI uses **Retrieval-Augmented Generation (RAG)** to ensure answers are grounded in the uploaded documents.

---

## 📚 Features

- 📤 Upload multiple PDF study documents  
- 🔎 Context-aware Question Answering  
- 📝 Automatic study notes generation  
- 📋 MCQ generation with answer keys  
- 💬 Streaming AI responses  
- 🗂️ Session management with history  
- 💾 Persistent storage using SQLite  
- 🎨 Modern dark-themed Streamlit UI  

---

## 🏗️ Project Structure

```
EduAI/
│
├── app.py                   # Main Streamlit application
├── build_vectorstore.py     # PDF embedding & FAISS index builder
├── DocQA.py                 # Document-based Q&A system (RAG)
├── Notes.py                 # Study notes generator
├── MCQs.py                  # MCQ generator
├── database.py              # SQLite database manager
├── auth_manager.py          # (Optional) Authentication logic
├── auth_pages.py            # (Optional) Login & Signup UI
├── faiss_index_local/       # Generated FAISS vector store
└── eduai_data.db            # SQLite database (auto-created)
```

---

## ⚙️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Kushagra3355/EduAI.git
cd EduAI
```

### 2. Create a Virtual Environment (Recommended)
```bash
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🔐 Configuration

### OpenAI API Key

EduAI requires an OpenAI API key.

#### Option 1: Environment Variable
```bash
export OPENAI_API_KEY="your-api-key"
```

#### Option 2: Streamlit Secrets
Create `.streamlit/secrets.toml`:
```toml
OPENAI_API_KEY="your-api-key"
```

---

## 🧠 Building the Vector Store

Before asking questions or generating content, upload PDFs and process them inside the app.

Internally, EduAI:
- Splits documents into chunks
- Creates embeddings using OpenAI
- Stores vectors locally using FAISS

The index is saved in `faiss_index_local/`.

---

## 🚀 Running the Application

```bash
streamlit run app.py
```

---

## 🧩 Application Pages

### 📤 Upload Documents
- Upload one or more PDFs
- Build a searchable knowledge base

### 💬 Ask Questions
- Ask questions based on uploaded content
- Get streaming, context-aware answers

### 📝 Generate Notes
- Create structured study notes
- Download notes as `.txt` files

### 📋 Create MCQs
- Generate 10 MCQs with 4 options each
- Includes a complete answer key

---

## 🗄️ Database Design

EduAI uses SQLite to store:

- Chat conversations
- Application state
- Uploaded document metadata
- Generated notes and MCQs
- Session information

Each session maintains its own learning context.

---

## 🧰 Technologies Used

- **Frontend**: Streamlit  
- **LLM**: OpenAI (GPT-4o-mini)  
- **Embeddings**: text-embedding-3-small  
- **Vector Store**: FAISS  
- **Orchestration**: LangGraph  
- **Database**: SQLite  
- **Language**: Python  

---

## 🛠 Troubleshooting

**Documents not processed**
- Upload PDFs before using other features

**OpenAI API errors**
- Verify API key configuration

**Slow processing**
- Large PDFs may take longer to embed

---

## 🚧 Future Enhancements

- User authentication (already scaffolded)
- Support for DOCX / TXT files
- Cloud-hosted vector storage
- Multi-user collaboration
- Progress tracking

---

## 📄 License

MIT License

---

## 👤 Author

**Kushagra**  
GitHub: https://github.com/Kushagra3355

---

🎓 *EduAI – Learn smarter, not harder.*
