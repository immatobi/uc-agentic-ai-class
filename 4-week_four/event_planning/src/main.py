from dotenv import load_dotenv
from typing import TypedDict, Literal, Optional
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from pydantic import BaseModel, Field
import requests
import os
import pprint

def get_llm() -> ChatAnthropic:
    llm = ChatAnthropic(
        model="gpt-4.1-mini",
        temperature=0,
        top_p=1
    )
    return llm

# Define the schema structure
# Example event to plan
# I am organizing an outdoor AI bootcamp networking session tomorrow evening in Lagos, Nigeria
# for beginner developers and working professionals. Help me prepare a readiness plan
class EventDetails(BaseModel):
    event_type: str = Field(description="The type of event. for example: bootcamp class, outdor meetup")
    city: str = Field(description="city or location where the event will happen")
    country: Optional[str] = Field(description="Country if provided")
    date_or_time: Optional[str] = Field(default=None, description="Event date and/or time if provided")
    audience: Optional[str] = Field(default=None, description="Who the event is for")
    is_outdoor: bool = Field(description="whether weather is likely important for this event")
    metadata: list[str] = Field(default_factory=list, description="Important missing details")

class ReviewResult(BaseModel):
    score: int = Field(description="Quality score from 1 to 10")
    passed: bool = Field(description="A boolean property that tells whether the plan is good enough")
    feedback: str = Field(description="Specific feedback for improvement")

# Define the workflow state or graph

class AgentState(BaseModel):
    user_request: str
    event_details: Optional[EventDetails]
    weather_report: Optional[str]
    plan: Optional[str]
    review: Optional[ReviewResult]
    revision_count: int
    final_answer: Optional[str]

@tool
def check_weather(location: str) -> str:
    """Get the current weather in a given location using OpenWeatherMap."""
    api_key = os.getenv("OPEN_WEATHER_API_KEY")
    url = os.getenv("OPEN_WEATHER_API_URL")

    if not api_key:
        return "Tool Error: OPEN_WEATHER_API_KEY is not specified"
    if not url:
        return "Tool Error: OPEN_WEATHER_API_URL is not specified"
    
    params = {
        "q": location,
        "appid": api_key,
        "units": "metric",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
    except requests.RequestException as e:
        return f"Weather tool error: { str(e) }"
    
    if response.status_code != 200:
        return f"Could not get weather for {location}. Error: {response.text}"
    
    data = response.json()

    city = data["name"]
    country = data["sys"]["country"]
    temperature = data["main"]["temp"]
    feels_like = data["main"]["feels_like"]
    description = data["weather"][0]["description"]
    humidity = data["main"]["humidity"]
    wind_speed = data["wind"]["speed"]

    return (
        f"Current weather in {city}, {country}: {description}. "
        f"Temperature: {temperature}C. "
        f"Feels like: {feels_like}C. "
        f"Humidity: {humidity}% "
        f"Wind speed: {wind_speed}m/s "
    )


# Node 1: Extract event details into a structured format
def extract_event_details_node(state: AgentState) -> dict:
    llm = get_llm()
    structured_llm = llm.with_structured_output(EventDetails)

    prompt = f"""
    You are an expert event operations assistant.
    Extract structured event details from the user's request.
    User Request:
    {state["user_request"]}

    Rules:
    - Infer only what is reasonable
    - If important details are missing, list them in metadata
    - Decide if weather matters. Weather usually matters for outdoor events, travel, logistics or physical attendance.
    """

    details = structured_llm.invoke(prompt)

    return {
        "event_details": details
    }

# Node 2: Build the check weather node
def check_weather_node(state: AgentState) -> dict:

    details: EventDetails = state["event_details"]

    if not details:
        return {
            "weather_report": "Weather was not checked because event details were missing"
        }
    
    location = details.city
    
    if details.country:
        location = f"{details.city}, {details.country}"

    report = check_weather.invoke({ "location": location })
    print(f"check_weather type: {type(check_weather)}")

    return {
        "weather_report": report
    }

# Node 3: Generate event plan node
def generate_plan_node(state: AgentState) -> dict:

    llm = get_llm()
    details: EventDetails = state["event_details"]
    weather = state["weather_report"] or "Weather was not required or not available"

    prompt = f"""
    You are an expert, most senior event operations planner.
    Create a practical event readiness plan.

    Original User request:
    {state["user_request"]}

    Structured Event Details:
    {details.model_dump() if details else "No structured details available"}

    Weather Information
    { weather }

    Your plan must include:
    1. Event summary
    2. Key assumptions
    3. Preparation checklist
    4. Weather logistics/considerations if relevant
    5. Risks and mitigation
    6. Final recommendation

    Be practical, clear and suitable for someone organizing the event for tomorrow.

    """

    response = llm.invoke(prompt)

    return {
        "plan": response.content
    }

def review_plan_node(state: AgentState) -> dict:

    llm = get_llm()
    structured_llm = llm.with_structured_output(ReviewResult)

    prompt = f"""
    You are a strict quality reviewer.
    Review the event plan below:

    User request:
    {state["user_request"]}

    Plan:
    {state["plan"]}

    Score the plan from 1 to 10.

    The Plan should only pass if:

    1. It answers the user request clearly
    2. It is practical
    3. It includes risks
    4. It uses weather information when relevant
    5. It does not make unsupported clain

    Return structured review only.

    """

    review = structured_llm.input_schema(prompt)

    return {
        "review": review
    }

def revise_plan_node(state: AgentState) -> dict:
    llm = get_llm()
    review = state["review"]

    prompt = f"""
    You are improving an event readiness plan.

    Original user request:
    {state["user_request"]}

    Previous plan:
    {state["plan"]}

    Reviewer feedback:
    {review.feedback if review else "No feedback available"}

    Rewrite the plan to address the feedback.
    Make it clearer, more practical, and more complete.

    """

    response = llm.invoke(prompt)

    return {
        "plan": response.content,
        "revision_count": state["revision_count"] + 1
    }

def finalize_node(state: AgentState) -> dict:

    review: ReviewResult = state["review"]

    final = f"""
    {state["plan"]}

    ---

    Plan quality score: { review.score if review else "Not reviewed" }/10

    Reviewer note:
    { review.feedback if review else "No review feedback available" }

    """

    return {
        "final_answer": final
    }

# Conditional: Build conditional routers
def route_weather_check(state: AgentState) -> Literal["check_weather", "generate_plan"]:

    details: EventDetails = state["event_details"]

    if details and details.is_outdoor:
        return "check_weather"
    return "generate_plan"

def route_after_review(state: AgentState) -> Literal["finalize", "revise_plan"]:

    review: ReviewResult = state["review"]
    count = state["revision_count"]

    if review and review.passed:
        return "finalize"
    
    if count >= 1:
        return "finalize"
    
    return "revise_plan"


# Build graph workflow
def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node("extract_event_details_node", extract_event_details_node)
    builder.add_node("check_weather_node", check_weather_node)
    builder.add_node("generate_plan_node", generate_plan_node)
    builder.add_node("review_plan_node", review_plan_node)
    builder.add_node("revise_plan_node", revise_plan_node)
    builder.add_node("finalize_node", finalize_node)

    builder.add_edge(START, "extract_event_details_node")

    builder.add_conditional_edges(
        "extract_event_details_node",
        route_weather_check,
        {
            "check_weather": "check_weather_node",
            "generate_plan": "generate_plan_node"
        },
    )

    builder.add_edge("check_weather_node", "generate_plan_node")
    builder.add_edge("generate_plan_node", "review_plan_node")

    builder.add_conditional_edges(
        "review_plan_node",
        route_after_review,
        {
            "finalize": "finalize_node",
            "revise_plan": "revise_plan_node"
        },
    )

    builder.add_edge("revise_plan_node", "review_plan_node")
    builder.add_edge("finalize_node", END)

    return builder

# Graph input
inputs = {
    "user_request": """I am organizing an outdoor AI bootcamp networking session tomorrow evening in Lagos, Nigeria for beginner developers and working professionals. Help me prepare a readiness plan.""",
    "event_details": None,
    "weather_report": None,
    "plan": None,
    "review": None,
    "revision_count": 0,
    "final_answer": None
}

def main() -> None:
    load_dotenv()

    # Compile workflow graph
    builder = build_graph()
    graph = builder.compile()

    # Stream graph execution
    for chunk in graph.stream(inputs, stream_mode="updates"):
        print("\n==============================")
        print("GRAPH UPDATE")
        print("==============================")
        # NOTE: each chunk contains the state updates returned by a node, not the entire state and not just the final result.
        # So you get a node-by-node view of the state updates.
        pprint(chunk)

    # Get final answer directly
    # NOTE: graph.invoke() runs the entire graph to completion and returns the final state.
    result = graph.invoke(inputs)

    print("\n\nFINAL ANSWER")
    print("============")
    print(result["final_answer"])

if __name__ == "__main__":
    main()
