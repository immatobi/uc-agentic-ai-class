from typing import Any
from dotenv import load_dotenv
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.chat_route import router as chat_router
from .api.health_route import router as health_router
from .services.doc_service import load_documents
from .services.rag_service import create_retriever, chunk_documents, get_embedding
from .graph.rag_graph import build_graph
from .utils.dir_util import find_directory

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

ENV_DIR = PROJECT_DIR / ".env"
KNOWLEDGE_DIR = BASE_DIR / "_data" / "kbase"

load_dotenv(ENV_DIR)

app = FastAPI(title="UNI RAG API")
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

app.include_router(health_router)
app.include_router(chat_router)
