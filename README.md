# AI Chatbot

A simple Question-Answer chatbot with a **FastAPI backend** (Groq + LangChain) and a **React frontend** (Vite + TypeScript).

## Features

- 💬 Real-time chat interface
- 🧠 Session-based conversation memory
- ⚡ Fast inference via Groq (free tier: 14,400 req/day)
- 🔄 Multiple model support (Llama 3.3, Qwen, Mixtral, Gemma)
- 🎨 Clean, responsive UI

## Architecture

```
┌─────────────┐     HTTP/JSON      ┌─────────────┐
│  Frontend   │ ◄─────────────────► │  Backend    │
│  (React)    │   localhost:8011   │  (FastAPI)  │
└─────────────┘                    └─────────────┘
                                           │
                                           ▼
                                    ┌─────────────┐
                                    │   Groq API  │
                                    │  (LLM)      │
                                    └─────────────┘
```

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Free [Groq API key](https://console.groq.com/keys)

### 1. Backend Setup
```bash
cd backend
pip install -r requirements.txt

# Configure environment
cp ../.env.example ../.env
# Edit .env and add your GROQ_API_KEY

# Run server (port 8011)
python main.py
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Project Structure

```
AIchatbot/
├── chatbot.py              # Standalone CLI version (HuggingFace)
├── requirements.txt        # CLI dependencies
├── .env                    # Your API keys (gitignored)
├── .env.example            # Template for API keys
├── backend/
│   ├── main.py             # FastAPI server
│   └── requirements.txt    # Backend dependencies
└── frontend/
    ├── src/
    │   ├── App.tsx         # Chat UI component
    │   ├── main.jsx        # React entry point
    │   └── index.css       # Styles
    ├── package.json
    └── vite.config.js
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check + model info |
| POST | `/chat` | Send message `{message, session_id}` |
| DELETE | `/chat/{session_id}` | Clear conversation history |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GROQ_API_KEY` | Your Groq API key | Required |
| `GROQ_MODEL` | Model to use | `qwen/qwen3.8-27b` |

Available models:
- `llama-3.3-70b-versatile` — Best quality
- `llama-3.1-8b-instant` — Fastest
- `mixtral-8x7b-32768` — Large context
- `gemma2-9b-it` — Google's model
- `qwen/qwen3.8-27b` — Current default

## CLI Version

For terminal-only usage (uses HuggingFace instead of Groq):
```bash
pip install -r requirements.txt
cp .env.example .env  # Add HF_TOKEN
python chatbot.py
```

## License

MIT