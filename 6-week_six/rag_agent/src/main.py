import os
from typing import Any, TypedDict, Literal, List
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel

FOLDER_PATH="./.docs/knowledge"
load_dotenv()

class AgentState(BaseModel):
    question: str
    route: str
    documents: List[Document]
    answer: str
    review: str
    final_answer: str

# Define llm
def get_llm() -> ChatAnthropic:
    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        temperature=0
    )
    return llm

# Load all documents
def load_documents(folder_path: str) -> List[Document]:
    documents = []

    for filename in os.listdir(folder_path): 
        if filename.endswith('.txt'):
            file_path = os.path.join(folder_path, filename)

            with open(file_path, 'r', encoding="utf-8") as file:
                text = file.read()
                doc = Document(
                    page_content=text,
                    metadata={
                        "source": filename
                    }
                )

                documents.append(doc)

    return documents

# Chunk all the documents
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

# Store document in chroma vector database
def create_vector(chunks: list[Document], embeddings: GoogleGenerativeAIEmbeddings) -> Chroma:
    store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        # persist_directory="./chroma_db"
    )
    print(f"Vector collections created: {store._collection.count()}")
    return store

# Define workflow nodes & functions
# -----------------------------------------------------------

# Question router node
def question_router_node(state: AgentState) -> dict:
    question = state.question
    llm = get_llm()

    prompt = f"""
    You are a routing assistant.

    Decide whether the user question requires university knowledge documents.

    Route as:
    - "knowledge" if the question is about university policies, tuition, housing, registration, financial aid, student
    services, international students, career services, GPA, attendance, or campus support.
    - "general" if the question is a general question unrelated to the university.

    Question:
    {question}

    Return only one word: knowledge or general.
    """

    response = llm.invoke(prompt)
    route = response.content.strip().lower()

    return {
        "route": route
    }

# Route Decision
def route_decision(state: AgentState) -> Literal["knowledge", "general"]:
    return state.route

# Retrieve docs node
# Usage: graph.add_node("retrieve_docs", retrieve_docs_node(retriever))
def retrieve_docs_node(retriever: VectorStoreRetriever):
    def make_docs_node(state: AgentState) -> dict:
        question = state.question
        documents = retriever.invoke(question)
        return {"documents": documents}

    return make_docs_node

# Generate grounded RAG answer node
def knowledge_answer_node(state: AgentState) -> dict:
    question = state.question
    documents = state.documents
    llm = get_llm()

    # Define the context -> The Augmentation part
    context = "\n\n".join(
        [
            f"Source: { doc.metadata.get("source") }\nContent: {doc.page_content}"
            for doc in documents
        ]
    )

    prompt = f"""
    You are a university student services AI assistant.

    Answer the user's question using ONLY the context below.

    Rules:
    - Do not invent information.
    - If the answer is not found in the context, say:
      "I could not find this information in the university knowledge base."
    - Mention the source document when possible.
    - Be clear and helpful.

    User Question:
    {question}

    Context:
    {context}
    """

    response = llm.invoke(prompt)

    return {
        "answer": response.content
    }

# Generate general answer to general questions
def general_answer_node(state: AgentState) -> dict:
    question = state.question
    llm = get_llm()

    prompt = f"""
    Answer the user's general question clearly and briefly.

    Question:
    {question}
    """

    response = llm.invoke(prompt)

    return {
        "answer": response.content,
        "documents": []
    }

# Review answer node
def review_answer_node(state: AgentState) -> dict:
    question = state.question
    answer = state.answer
    documents = state.documents
    llm = get_llm()

    if state.route == 'general':
        return {
            "review": "General answer. No document grounding required"
        }

    # Define the context -> The Augmentation part
    context = "\n\n".join(
        [doc.page_content for doc in documents]
    )

    prompt = f"""
    You are reviewing a RAG answer.

    Check whether the answer is grounded in the retrieved context.

    Question:
    {question}

    Retrieved Context:
    {context}

    Generated Answer:
    {answer}

    Return one of the following:
    - PASS: if the answer is supported by the context.
    - FAIL: if the answer includes unsupported claims.
    - MISSING: if the retrieved context does not contain enough information.
    """

    response = llm.invoke(prompt)

    return {
        "review": response.content,
    }

# Finalize node
def finalize_node(state: AgentState) -> dict:
    answer = state.answer
    review = state.review

    if "FAIL" in review.upper():
        final_answer = """
        I could not find enough information in the university knowledge base to answer this question accurately.
        Please contact the appropiate university office for clarification.
        """
    else:
        final_answer = answer
    
    return {
        "final_answer": final_answer
    }

def build_workflow(retriever: VectorStoreRetriever):
    builder = StateGraph(AgentState)

    # Add the nodes
    builder.add_node("question_router_node", question_router_node)
    builder.add_node("retrieve_docs_node", retrieve_docs_node(retriever))
    builder.add_node("knowledge_answer_node", knowledge_answer_node)
    builder.add_node("general_answer_node", general_answer_node)
    builder.add_node("review_answer_node", review_answer_node)
    builder.add_node("finalize_node", finalize_node)

    # Build the workflow
    builder.add_edge(START, "question_router_node")

    builder.add_conditional_edges(
        "question_router_node",
        route_decision,
        {
            "knowledge": "retrieve_docs_node",
            "general": "general_answer_node"
        }
    )

    builder.add_edge("retrieve_docs_node", "knowledge_answer_node")
    builder.add_edge("knowledge_answer_node", "review_answer_node")
    builder.add_edge("general_answer_node", "review_answer_node")
    builder.add_edge("review_answer_node", "finalize_node")
    builder.add_edge("finalize_node", END)

    graph = builder.compile()

    return graph

def ask_question(question: str, graph: Any):

    result = graph.invoke(
        {
            "question": question,
            "route": "",
            "documents": [],
            "answer": "",
            "review": "",
            "final_answer": "",
        }
    )

    print("\nQUESTION:")
    print(question)

    print("\nROUTE:")
    print(result["route"])

    print("\nANSWER:")
    print(result["final_answer"])

    print("\nREVIEW:")
    print(result["review"])

    print("\nSOURCES:")
    for doc in result["documents"]:
        print("-", doc.metadata.get("source"))

    print("\n" + "====================================================================")

def main() -> None:

    # from IPython.display import Image, display
    # display(Image(graph.get_graph().draw_mermaid_png()))
    
    raw_documents = load_documents(FOLDER_PATH)
    documents = chunk_documents(raw_documents)
    embedding = get_embedding()
    vector_store = create_vector(documents, embedding)

    # Retrieve with K:5
    retriever = vector_store.as_retriever(
        search_kwargs={"k": 5}
    )
    graph = build_workflow(retriever)
    ask_question("What is course registration about?", graph)

if __name__ == "__main__":
    main()
