import os
from typing import Any, TypedDict, Literal, List, Annotated
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages

load_dotenv()

# Create the state schema
class AgentState(BaseModel):
    # messages: list
    messages: Annotated[list, add_messages]

# Define llm
def get_llm() -> ChatAnthropic:
    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        temperature=0
    )
    return llm

# Create node
def chat_bot(state: AgentState) -> dict:
    llm = get_llm()
    response = llm.invoke(state.messages)

    return {
        "messages": [response]
    }

# Create graph
graph = StateGraph(AgentState)

# Add nodes
graph.add_node("chat_bot", chat_bot)

# Add Edges
graph.add_edge(START, "chat_bot")
graph.add_edge("chat_bot", END)

# Create memory ( Short Term )
memory = InMemorySaver()
workflow = graph.compile( checkpointer = memory )

# visualize
workflow.get_graph().draw_mermaid_png(output_file_path="chat_bot.png")

def main() -> None:

    # Begin conversation
    config = {
        "configurable": {
            "thread_id": "user-1"
        }
    }

    print("AI Chat Started. Type exit or quit to stop.\n")

    while True:
       user_input = input("You: ")

       if user_input.lower() in ['exit', 'quit']:
           print("Goodbye!")
           break
       result = workflow.invoke(
           {
               "messages": [
                   {
                       "role": "user",
                       "content": user_input
                   }
               ]
           },
           config=config
       )

       ai_message = result["messages"][-1]
       print(f"AI: {ai_message.content}\n")

    #    print("CHECKPOINT")
    #    print(workflow.get_state(config).values["messages"])
    #    print()


if __name__ == "__main__":
    main()
