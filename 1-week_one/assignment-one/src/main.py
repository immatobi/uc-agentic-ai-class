import os
import sys
from pathlib import Path
from datetime import UTC, datetime, timedelta
from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from newsapi import NewsApiClient
import yaml
import json

PROVIDER_FACTORIES = {
    "anthropic": ChatAnthropic,
    "openai": ChatOpenAI,
}

def load_agent_config() -> dict:
    """Load the YAML config for the news agent."""
    config_path = Path(__file__).resolve().parent.parent / "config" / "news_agent.yml"
    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)

def build_model(config: dict):
    """Build the configured chat model."""
    provider = config.get("provider", "").strip().lower()
    model_name = config.get("model")

    if provider not in PROVIDER_FACTORIES:
        supported = ", ".join(sorted(PROVIDER_FACTORIES))
        raise ValueError(
            f"Unsupported provider '{provider}'. Supported providers: {supported}."
        )
    if not model_name:
        raise ValueError("The agent config must define a model name.")

    model_class = PROVIDER_FACTORIES[provider]
    return model_class(
        model=model_name,
        temperature=config.get("temperature", 0.0),
        max_tokens=config.get("max_tokens"),
    )

def build_agent():
    """Build a LangChain agent from YAML configuration."""
    config = load_agent_config()
    model = build_model(config)
    return create_agent(
        model=model,
        tools=[get_news],
        system_prompt=config.get("system_prompt", ""),
    )

def get_news(
    query: str,
    language: str = "en",
    page_size: int = 5,
    sort_by: str = "publishedAt",
) -> str:
    """Fetch recent articles for a topic from News API.

    This function is shaped to work well as a LangChain tool:
    its inputs are simple primitives and it returns a compact string.
    """
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        raise ValueError("NEWS_API_KEY is not set.")

    if not query.strip():
        raise ValueError("query must not be empty.")

    bounded_page_size = max(1, min(page_size, 10))
    normalized_query = " ".join(query.split())
    since = (datetime.now(UTC) - timedelta(days=30)).date().isoformat()
    startup_terms = (
        '(startup OR startups OR founder OR founders OR funding OR '
        'venture capital OR VC OR accelerator OR incubator OR tech)'
    )
    enriched_query = (
        normalized_query
        if "startup" in normalized_query.lower()
        else f"{normalized_query} AND {startup_terms}"
    )

    newsapi = NewsApiClient(api_key=api_key)
    response = newsapi.get_everything(
        q=enriched_query,
        language=language,
        sort_by=sort_by,
        page=1,
        page_size=bounded_page_size,
        from_param=since,
    )

    articles = response.get("articles", [])
    if not articles:
        return (
            f"No recent startup news articles found for '{normalized_query}' "
            f"in the last 30 days."
        )

    lines = [
        f"Top {len(articles)} recent startup news results for '{normalized_query}' "
        f"(search query: {enriched_query}; since: {since}):"
    ]
    for index, article in enumerate(articles, start=1):
        title = article.get("title") or "Untitled"
        source = article.get("source", {}).get("name") or "Unknown source"
        author = article.get("author") or "Unknown author"
        published_at = article.get("publishedAt") or "Unknown date"
        url = article.get("url") or "No URL"
        description = article.get("description") or "No description available."
        lines.append(
            f"{index}. {title} | {source} | {author} | {published_at}\n"
            f"   {description}\n"
            f"   {url}"
        )

    return "\n\n".join(lines)

def build_user_prompt(config: dict, query: str) -> str:
    """Render the configured user prompt for a query."""
    return config["user_prompt_template"].format(query=query)

def build_agent_inputs(prompt: str) -> dict:
    return {
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

def run_agent(query: str, config: dict):
    agent = build_agent()
    prompt = build_user_prompt(config, query)
    inputs = build_agent_inputs(prompt)

    return agent.invoke(inputs)

def extract_stream_text(chunk) -> str:
    content = getattr(chunk, "content", "")

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(part.get("text", ""))
        return "".join(text_parts)

    return ""

def extract_message_text(message_content) -> str:
    """Flatten LangChain message content into text."""
    content = message_content

    if isinstance(content, list):
        text_parts = [
            part["text"]
            for part in content
            if isinstance(part, dict) and part.get("type") == "text" and part.get("text")
        ]
        content = "\n".join(text_parts)

    return str(content).strip()

def strip_code_fences(text: str) -> str:
    if text.startswith("```json"):
        return text.removeprefix("```json").removesuffix("```").strip()
    if text.startswith("```"):
        return text.removeprefix("```").removesuffix("```").strip()
    return text

def find_json_payload(text: str) -> str:
    """Extract the first top-level JSON object or array from text."""
    json_decoder = json.JSONDecoder()
    candidate_starts = [index for index, char in enumerate(text) if char in "[{"]

    for start in candidate_starts:
        try:
            _, end = json_decoder.raw_decode(text[start:])
            return text[start : start + end]
        except json.JSONDecodeError:
            continue

    raise ValueError("Could not locate a valid JSON payload in the agent response.")

def validate_json_type(payload, expected_type: str) -> None:
    type_map = {
        "array": list,
        "object": dict,
    }
    expected_python_type = type_map.get(expected_type)
    if expected_python_type is None:
        raise ValueError(f"Unsupported response_format '{expected_type}' in config.")
    if not isinstance(payload, expected_python_type):
        actual_type = type(payload).__name__
        raise ValueError(
            f"Expected a JSON {expected_type}, but the agent returned {actual_type}."
        )

def validate_schema(payload, schema: dict, path: str = "$") -> None:
    schema_type = schema.get("type")

    if schema_type == "array":
        if not isinstance(payload, list):
            raise ValueError(f"{path} must be an array.")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(payload):
                validate_schema(item, item_schema, f"{path}[{index}]")
        return

    if schema_type == "object":
        if not isinstance(payload, dict):
            raise ValueError(f"{path} must be an object.")

        properties = schema.get("properties", {})
        required = schema.get("required", [])
        allow_additional = schema.get("additionalProperties", True)

        for field in required:
            if field not in payload:
                raise ValueError(f"{path}.{field} is required.")

        for key, value in payload.items():
            if key in properties:
                validate_schema(value, properties[key], f"{path}.{key}")
            elif not allow_additional:
                raise ValueError(f"{path}.{key} is not allowed by the schema.")
        return

    if schema_type == "string" and not isinstance(payload, str):
        raise ValueError(f"{path} must be a string.")

def extract_json_output(result: dict, config: dict):
    final_message = result["messages"][-1]
    content = strip_code_fences(extract_message_text(final_message.content))
    content = find_json_payload(content)
    payload = json.loads(content)

    response_format = config.get("response_format")
    if response_format:
        validate_json_type(payload, response_format)

    response_schema = config.get("response_schema")
    if response_schema:
        validate_schema(payload, response_schema)

    return payload

def stream_live_json(query: str, config: dict) -> None:
    agent = build_agent()
    prompt = build_user_prompt(config, query)
    inputs = build_agent_inputs(prompt)

    for chunk, metadata in agent.stream(
        inputs,
        stream_mode="messages",
    ):
        if metadata.get("langgraph_node") != "model":
            continue

        text = extract_stream_text(chunk)
        if not text:
            continue

        sys.stdout.write(text)
        sys.stdout.flush()

    sys.stdout.write("\n")

def main() -> None:
    load_dotenv()
    config = load_agent_config()
    query = "Start up news in Nigeria"
    stream_live_json(query, config)


if __name__ == "__main__":
    main()
