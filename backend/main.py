import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
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

@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", model=GROQ_MODEL)

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