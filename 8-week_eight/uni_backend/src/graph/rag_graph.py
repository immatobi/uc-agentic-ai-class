from typing import Literal

from langchain_core.documents import Document
from langgraph.graph import StateGraph, START, END
from ..schemas.graph_schema import AgentState
from ..services.llm_service import get_llm
from langchain_core.vectorstores import VectorStoreRetriever

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
    if state.route not in {"knowledge", "general"}:
        return "general"
    return state.route

# Retrieve docs node
# Usage: graph.add_node("retrieve_docs_node", retrieve_docs_node(retriever))
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
            f"Source: {doc.metadata.get('source')}\nContent: {doc.page_content}"
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

# Graph workflow builder
def build_graph(retriever: VectorStoreRetriever):
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
