from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import shutil, os

from build_vectorstore import embed_docs
from DocQA import DocumentQA
from MCQs import mcqs_generator
from Notes import notes_generator


app = FastAPI()

PDF_DIR = "pdfs"
FAISS_INDEX_DIR = "faiss_index_local"
os.makedirs(PDF_DIR, exist_ok=True)

docqa_model = None
mcq_model = None
notes_model = None


@app.get("/")
def root():
    return {"messages": "EduAI Tutor API"}


@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    global docqa_model, mcq_model, notes_model

    upload_path = os.path.join(PDF_DIR, file.filename)
    with open(upload_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    embed_docs(pdf_path=PDF_DIR, faiss_save_path=FAISS_INDEX_DIR)

    docqa_model = DocumentQA(faiss_path=FAISS_INDEX_DIR)
    mcq_model = mcqs_generator(faiss_path=FAISS_INDEX_DIR)
    notes_model = notes_generator(faiss_path=FAISS_INDEX_DIR)

    return {"message": f"{file.filename} uploaded and indexed successfully."}


@app.get("/ask-docqa/")
def ask_doc(question: str):
    if not docqa_model:
        return JSONResponse(content={"error": "Upload a PDF first."}, status_code=400)
    result = docqa_model.run(question)
    return {"response": result["response"]}


@app.get("/generate-mcqs/")
def generate_mcqs():
    if not mcq_model:
        return JSONResponse(content={"error": "Upload a PDF first."}, status_code=400)
    result = mcq_model.run()
    return {"mcqs": result["response"]}


@app.get("/generate-notes/")
def generate_notes():
    if not notes_model:
        return JSONResponse(content={"error": "Upload a PDF first."}, status_code=400)
    result = notes_model.run()
    return {"notes": result["response"]}
