from pydantic import BaseModel
from typing import List, Any
from ..utils.enums_util import PriorityEnum

class ChatRequest(BaseModel):
    question: str
    thread_id: str
    customer_id: str

class Source(BaseModel):
    source: str
    content_preview: str

class ChatResponseData(BaseModel):
    question: str
    customer_id: str
    thread_id: str
    route: str
    answer: str
    review: Any
    confidence: float
    priority: str
    assigned_team: str
    sources: List[Source]
    memory_updates: list[Any]

class ChatResponse(BaseModel):
    error: bool
    errors: list[str]
    data: ChatResponseData
    message: str
    status: int
    