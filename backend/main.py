import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
    raise ValueError("Please set GROQ_API_KEY in .env file. Get one free at https://console.groq.com/keys")

llm = ChatGroq(
    model=GROQ_MODEL,
    api_key=GROQ_API_KEY,
    temperature=0.7,
    max_tokens=512,
)

SYSTEM_PROMPT = """You are a helpful, harmless, and honest AI assistant. 
Answer questions directly and concisely. If you don't know something, say so."""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])

chain = prompt | llm

# In-memory session store
session_store: dict[str, BaseChatMessageHistory] = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in session_store:
        session_store[session_id] = InMemoryChatMessageHistory()
    return session_store[session_id]

chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)

app = FastAPI(title="AI Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    response: str
    session_id: str


class HealthResponse(BaseModel):
    status: str
    model: str


class UploadRequest(BaseModel):
    session_id: str


class UploadResponse(BaseModel):
    document_name: str
    status: str
    extracted_text: str = ""
    chunks: int = 0


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", model=GROQ_MODEL)


@app.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...), request: UploadRequest = ...):
    """Document loader: extract text from PDF, PPT, and DOC files."""
    try:
        session_id = request.session_id
        filename = file.filename or "uploaded_document"

        # Read file content
        content = await file.read()

        # Save to temp file for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        # Extract text based on file type
        extracted_text = ""
        
        if filename.lower().endswith(".pdf"):
            from PyPDF2 import PdfReader
            try:
                reader = PdfReader(tmp_path)
                for page in reader.pages:
                    extracted_text += page.extract_text() or ""
            except Exception as e:
                os.unlink(tmp_path)
                return UploadResponse(
                    document_name=filename,
                    status="error",
                    extracted_text=f"PDF error: {str(e)}",
                    chunks=0
                )

        elif filename.lower().endswith(".pptx"):
            from pptx import Presentation
            try:
                prs = Presentation(tmp_path)
                for slide in prs.slides:
                    for shape in slide.shapes:
                        if hasattr(shape, "text"):
                            extracted_text += shape.text or ""
            except Exception as e:
                os.unlink(tmp_path)
                return UploadResponse(
                    document_name=filename,
                    status="error",
                    extracted_text=f"PPT error: {str(e)}",
                    chunks=0
                )

        elif filename.lower().endswith(".docx"):
            try:
                from docx import Document
                doc = Document(tmp_path)
                for paragraph in doc.paragraphs:
                    extracted_text += paragraph.text + "\n"
            except Exception as e:
                os.unlink(tmp_path)
                return UploadResponse(
                    document_name=filename,
                    status="error",
                    extracted_text=f"DOCX error: {str(e)}",
                    chunks=0
                )

        else:
            os.unlink(tmp_path)
            return UploadResponse(
                document_name=filename,
                status="unsupported_format",
                extracted_text="",
                chunks=0
            )

        os.unlink(tmp_path)

        # Count chunks (basic word count for now, actual chunking will be done later)
        word_count = len(extracted_text.split()) if extracted_text else 0

        return UploadResponse(
            document_name=filename,
            status="success",
            extracted_text=extracted_text[:1000] + ("..." if len(extracted_text) > 1000 else ""),
            chunks=word_count // 500  # rough estimate, actual chunking pending
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        config = {"configurable": {"session_id": request.session_id}}
        result = await chain_with_history.ainvoke(
            {"input": request.message},
            config=config
        )
        response_text = result.content if hasattr(result, 'content') else str(result)
        return ChatResponse(response=response_text, session_id=request.session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/chat/{session_id}")
async def clear_chat(session_id: str):
    if session_id in session_store:
        del session_store[session_id]
    return {"message": "Chat history cleared"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8011)
