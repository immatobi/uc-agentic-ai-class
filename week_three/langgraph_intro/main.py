from langgraph.graph import StateGraph, START, END
from typing import TypedDict

from pydantic import BaseModel, Field

# Create the state schema
class AgentState(TypedDict):
    message: str
    name: str
    age: int


# Create Node
def message_node(state: AgentState) -> dict:
    message = state.get('message', "Default message")
    
    return {
        "message": message,
        "age": 31
    }

# Create the graph
graph = StateGraph(AgentState)

# Add nodes
graph.add_node("messenger", message_node)

# add the START edge
graph.add_edge(START, "messenger")
graph.add_edge("messenger", END)

# Run the graph
# -> Compile the graph

workflow = graph.compile()

# Invoke the graph
initState = {
    "message": "Welcome to lang graph",
    "name": "James",
    "age": 26
}
result = workflow.invoke(initState)

print(result)
