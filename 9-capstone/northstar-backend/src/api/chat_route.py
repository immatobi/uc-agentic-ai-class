from fastapi import APIRouter, Request
from ..schemas.chat_schema import ChatRequest, ChatResponse, Source

router = APIRouter()

@router.post("/v1/chat", response_model=ChatResponse)
def chat(body: ChatRequest, req: Request):
    graph = req.app.state.graph
    
    result = graph.invoke(
        {
            "question": body.question,
            "customer_id": body.customer_id or "",
            "thread_id": body.thread_id or "",
            "messages": [],
            "route": "general",
            "documents": [],
            "answer": "",
            "review": None,
            "revision_count": 0,
            "confidence": 0.0,
            "priority": "normal",
            "assigned_team": "",
            "sources": [],
            "memory_updates": [],
            "final_answer": "",
        },
        config={
            "configurable": {
                "thread_id": body.thread_id or ""
            }
        }
    )

    sources = [
        Source(
            source=doc.metadata.get("source", "unknown"),
            content_preview=doc.page_content[:250]
        )

        for doc in result["documents"]
    ]

    return ChatResponse(
        error=False,
        errors=[],
        data={
            "question": body.question,
            "customer_id": result["customer_id"],
            "thread_id": result["thread_id"],
            "route": result["route"],
            "answer": result["final_answer"],
            "review": result["review"],
            "confidence": result["confidence"],
            "priority": result["priority"],
            "assigned_team": result["assigned_team"],
            "sources": sources,
            "memory_updates": result["memory_updates"],
        },
        message="successful",
        status=200,
    )