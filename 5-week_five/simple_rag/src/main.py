from dotenv import load_dotenv
from langchain_chroma import Chroma, Ve
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Payment for the Professional Track
# Vacepay & VaceBooks
# For RAG must i use a Vector Database?
# How do I build a RAG with Agents?
# What other Databases can we use?
# What if i ask something not embedded but related, will LLM give the response?

# Define our knowledge base
# How do we retrieve docs from database, GCS, AWS, CDN
docs = [
    "UnlimitedCode is an AI education company.",
    "This is the method of cooking rice and beans",
    "UnlimitedCode helps you move to the next level in agentic coding",
    "Blood transfusion helps you get blood to your system",
    "Our bootcamp teaches AI Agents."
]

# Convert plain strings into langchain document object
documents = [
    Document(page_content=text)
    for text in docs
]

# Create the embeddings for the document object
def get_embedding() -> GoogleGenerativeAIEmbeddings:
    embed = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001"
    )
    return embed

# Store document in chroma vector database
def create_vector(documents: list[Document], embeddings: GoogleGenerativeAIEmbeddings) -> Chroma:
    store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )
    print(f"Vector collections created: {store._collection.count()}")
    return store

def do_uery(store: Chroma):

    # Convert vector store to retriever object
    retriever = store.as_retriever(
        search_kwargs={"k": 2}
    )

    query = "What does the bootcamp teach?"
    results = retriever.invoke(query)

    for i, doc in enumerate(results, start=0):
        print(f"\nResult {i}: ")
        print(doc.page_content)

def do_similarity(store: Chroma, query: str):
    
    similar_docs = store.similarity_search(query, k=3)

    for i, doc in enumerate(similar_docs):
        print(f"Document {i+1}: \n{doc.page_content}")
        print("\n============================\n")

def do_degree_score(store: Chroma, query: str):

    results = store.similarity_search_with_score(query, k=5)

    for doc, score in results:
        print(f"Score: {score}")
        print(f"Document: {doc.page_content}")
        print("------------------------------------")

def main() -> None:
    load_dotenv()
    embeddings = get_embedding()
    vector_store = create_vector(documents, embeddings)

    do_degree_score(vector_store, "Rice cooking methods?")

if __name__ == "__main__":
    main()
