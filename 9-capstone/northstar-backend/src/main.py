from typing import Any
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

# services
from .services.doc_service import load_documents
from .services.rag_service import create_retriever, chunk_documents, get_embedding
from .graph.support_graph import build_graph

# routes
from .api.health_route import router as health_router
from .api.chat_route import router as chat_router

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
ENV_DIR = PROJECT_DIR / ".env"
KNOWLEDGE_DIR = BASE_DIR / "_data"

# load ENV variables
load_dotenv(ENV_DIR)

app = FastAPI(title="Northstar CSA")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

raw_documents = load_documents(KNOWLEDGE_DIR)
documents = chunk_documents(raw_documents)
embedding = get_embedding()
retriever = create_retriever(documents, embeddings=embedding)
graph = build_graph(retriever)
app.state.graph = graph

# Mount routers
# RUN: uv run uvicorn src.main:app --reload
app.include_router(health_router)
app.include_router(chat_router)

