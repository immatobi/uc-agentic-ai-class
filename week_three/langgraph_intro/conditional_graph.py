from langgraph.graph import StateGraph, START, END
from typing import Literal, TypedDict

from pydantic import BaseModel, Field

# Create the state schema
class AgentState(TypedDict):
    score: int
    message: str

def check_score(state: AgentState) -> dict:
    print("Checking Score")
    return {
        "message": f"Your score is {state.get("score")}"
    }

def passed_node(state: AgentState) -> dict:
    return {
        "message": "Congratulations, you passed your exam"
    }

def failed_node(state: AgentState) -> dict:
    return {
        "message": "Sorry! You failed your exam, try again."
    }

def route_by_score(state: AgentState) -> Literal["passed", "failed"]:
    
    if state.get("score") >= 60:
        return "passed"
    return "failed"

graph = StateGraph(AgentState)

# Add nodes
graph.add_node("check_score", check_score)
graph.add_node("passed_node", passed_node)
graph.add_node("failed_node", failed_node)
graph.add_node("route_by_score", route_by_score)

# add the START edge
graph.add_edge(START, "check_score")
graph.add_conditional_edges(
    "check_score",
    route_by_score, {
        "passed": "passed_node",
        "failed": "failed_node"
    }
)
graph.add_edge("passed_node", END)
graph.add_edge("failed_node", END)

workflow = graph.compile()

result = workflow.invoke({
    "score": 45,
    "message": ""
})

print(result)