from pydantic import BaseModel
from typing import List

class ChatRequest(BaseModel):
    question: str

class Source(BaseModel):
    source: str
    content_preview: str

class ChatResponse(BaseModel):
    question: str
    route: str
    answer: str
    review: str
    sources: List[Source]