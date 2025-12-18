# ⚖️ LegalEase AI – AI-Powered Legal Assistant

LegalEase AI is an **AI-powered legal assistant for Indian law**, built using **Streamlit**, **LangChain**, **LangGraph**, **FAISS**, and **OpenAI models**.  
It helps users understand legal concepts, Bare Acts, and legal documents through **context-aware, explainable, and source-cited responses**.

> ⚠️ **Disclaimer:** LegalEase AI is for educational and informational purposes only. It does **not** provide legal advice.

---

## 📚 Features

- ⚖️ **NyayGPT** – Ask questions about Indian law and legal procedures  
- 📄 **Ask Document** – Upload and analyze legal PDF documents  
- 🔍 **Bare Act Retrieval** using FAISS vector search  
- 🧠 Retrieval-Augmented Generation (RAG)  
- 💬 Streaming AI responses  
- 📚 Source-aware explanations (Act / Section references)  
- 🎨 Clean, minimal Streamlit UI  

---

## 🏗️ Project Structure

```
LegalEase-AI/
│
├── main.py                   # Streamlit application entry point
├── embed_docs.py             # Optimized Bare Act PDF embedding & FAISS index creation
├── LegalChatBot.py           # NyayGPT (legal Q&A chatbot)
├── DocumentQAGraph.py        # Ask Document tool with RAG pipeline
├── bare_act_retriever.py     # FAISS-based Bare Act retriever
├── faiss_index_legal/        # Generated FAISS index (required at runtime)
├── .env                      # Environment variables (OpenAI API key)
└── requirements.txt          # Python dependencies
```

---

## ⚙️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Kushagra3355/LegalEase-AI.git
cd LegalEase-AI
```

### 2. Create a Virtual Environment (Recommended)
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🔐 Configuration

### OpenAI API Key

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your-openai-api-key
```

For **Streamlit Cloud**, add the key under:
**Settings → Secrets**

---

## 🧠 Creating the FAISS Index (Mandatory)

Before running the app, you **must generate the FAISS vector store** from Bare Act PDFs:

```bash
python embed_docs.py
```

This command:
- Loads Bare Act PDFs
- Cleans and deduplicates text
- Creates optimized embeddings
- Saves the FAISS index to `faiss_index_legal/`

> ⚠️ Ensure `faiss_index_legal/` exists before running the app.

---

## 🚀 Running the Application

```bash
streamlit run main.py
```

---

## 🧩 Application Modes

### ⚖️ NyayGPT
- Ask questions about Indian law
- Retrieves relevant Bare Act sections
- Provides concise, easy-to-understand explanations
- Always cites sources
- Never gives legal advice

### 📄 Ask Document
- Upload legal PDFs (judgments, contracts, notices)
- Ask questions based on uploaded documents
- Combines document context with Bare Act references

---

## 🧰 Technologies Used

- **Frontend**: Streamlit  
- **LLM**: OpenAI (GPT-4o-mini)  
- **Embeddings**: text-embedding-3-small  
- **Vector Store**: FAISS  
- **Orchestration**: LangGraph  
- **Backend**: Python  

---

## 🛠 Troubleshooting

**FAISS index not found**
- Run `python embed_docs.py`
- Ensure `faiss_index_legal/` exists

**OpenAI API error**
- Verify API key in `.env` or Streamlit secrets

**Large FAISS index**
- Use Git LFS or external storage if index exceeds GitHub limits

---

## 🚧 Future Enhancements

- Multi-language legal support  
- Case law and judgment database integration  
- User authentication  
- Cloud-hosted vector database  
- Highlighted PDF citations  

---

## 📄 License

MIT License

---

## 👤 Author

**Kushagra**  
GitHub: https://github.com/Kushagra3355

---

⚖️ *LegalEase AI – Making Indian law more accessible, one question at a time.*
