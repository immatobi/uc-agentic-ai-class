from typing import List, Any
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

# Chunk all documents
def chunk_documents(documents: List[Document]) -> list[Document]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_documents(documents)
    print(f"No. of Chunks: {len(chunks)}")
    # print(f"Chunks {chunks}")

    return chunks

# Create the embeddings for the document object
def get_embedding() -> GoogleGenerativeAIEmbeddings:
    embed = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001"
    )
    return embed

# Store document in chroma vector ( as retriever ) database
def create_retriever(chunks: list[Document], embeddings: GoogleGenerativeAIEmbeddings) -> Any:
    store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        # persist_directory="./chroma_db"
    )
    print(f"Vectors created: {store._collection.count()}")
    
    return store.as_retriever(
        search_kwargs={"k": 5}
    )