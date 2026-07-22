from typing import List
from pydantic import BaseModel
from langchain_core.documents import Document

class AgentState(BaseModel):
    question: str
    route: str
    documents: List[Document]
    answer: str
    review: str
    final_answer: str