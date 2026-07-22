from fastapi import APIRouter, Request
from ..schemas.chat_schema import ChatRequest, ChatResponse, Source


router = APIRouter()
# 1:15:58
@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, http_request: Request):

    graph = http_request.app.state.graph
    
    result = graph.invoke(
        {
            "question": request.question,
            "route": "",
            "documents": [],
            "answer": "",
            "review": "",
            "final_answer": "",
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
        question=request.question,
        route=result["route"],
        answer=result["final_answer"],
        review=result["review"],
        sources=sources
    )
    
