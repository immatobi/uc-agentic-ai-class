from pydantic import BaseModel, Field
from typing import Any, Literal, List, Optional
from langchain_core.documents import Document

TECHNICAL = "technical_support"
BILLING = "billing_support"
SECURITY = "security_team"
CUSTOMER = "customer_success"
ENGINEERING = "engineering_on_call"

class ReviewResult(BaseModel):
    score: int = Field(description="Quality score from 1 to 10")
    passed: bool = Field(description="A boolean property that tells whether the plan is good enough")
    feedback: str = Field(description="Specific feedback for improvement")

class AgentState(BaseModel):
    question: str
    customer_id: str
    thread_id: str
    messages: list[Any]
    route: Literal[
        "knowledge", 
        "troubleshooting",
        "escalation",
        "onboarding",
        "general"
    ]
    documents: List[Document]
    answer: str
    review: Optional[ReviewResult]
    revision_count: int
    confidence: float
    priority: Literal["low", "normal", "urgent"]
    assigned_team: str
    sources: list[Any]
    memory_updates: list[Any]
    final_answer: str