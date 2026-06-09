from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

# Payment for the Professional Track
# Vacepay & VaceBooks
# For RAG must i use a Vector Database?
# How do I build a RAG with Agents?
# What other Databases can we use?
# What if i ask something not embedded but related, will LLM give the response?

# Define our knowledge base
# How do we retrieve docs from database, GCS, AWS, CDN
docs = [
    "Unlimited Code is an AI education company.",
    "Our bootcamp teaches AI Agents.",
    "Students build AI production systems."
]

# Convert plain strings into langchain document object

documents = [
    Document(page_content=text)
    for text in docs
]

# Create embedding model
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small"
)

# Store document in chroma vector database
vector_store = Chroma.from_documents(
    documents=documents,
    embedding=embeddings,
)

vector_store

def main() -> None:
    load_dotenv()
    print("Learner Support project is ready.")


if __name__ == "__main__":
    main()
