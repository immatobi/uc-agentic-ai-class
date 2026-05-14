import os
from pathlib import Path
from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from newsapi import NewsApiClient
import yaml
import json


def get_news(
    query: str,
    language: str = "en",
    page_size: int = 5,
    sort_by: str = "relevancy",
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
    newsapi = NewsApiClient(api_key=api_key)
    response = newsapi.get_everything(
        q=query,
        language=language,
        sort_by=sort_by,
        page=1,
        page_size=bounded_page_size,
    )

    articles = response.get("articles", [])
    if not articles:
        return f"No news articles found for '{query}'."

    lines = [f"Top {len(articles)} news results for '{query}':"]
    for index, article in enumerate(articles, start=1):
        title = article.get("title") or "Untitled"
        source = article.get("source", {}).get("name") or "Unknown source"
        published_at = article.get("publishedAt") or "Unknown date"
        url = article.get("url") or "No URL"
        description = article.get("description") or "No description available."
        lines.append(
            f"{index}. {title} | {source} | {published_at}\n"
            f"   {description}\n"
            f"   {url}"
        )

    return "\n\n".join(lines)

def load_agent_config() -> dict:
    """Load the YAML config for the news agent."""
    config_path = Path(__file__).resolve().parent.parent / "config" / "news_agent.yml"
    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)

def build_agent():
    """Build a LangChain agent from YAML configuration."""
    config = load_agent_config()
    # model = ChatOpenAI(
    #     model=config["model"],
    #     temperature=config.get("temperature", 0.0),
    #     max_tokens=config.get("max_tokens"),
    # )
    model = ChatAnthropic(
        model="claude-sonnet-4-0",
        temperature=config.get("temperature", 0.0),
        max_tokens=config.get("max_tokens"),
    )
    return create_agent(
        model=model,
        tools=[get_news],
        system_prompt=config.get("system_prompt", ""),
    )

def run_agent(query: str):
    config = load_agent_config()
    agent = build_agent()
    prompt = config["user_prompt_template"].format(query=query)
    inputs = {
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    return agent.invoke(inputs)

def extract_json_output(result: dict):
    final_message = result["messages"][-1]
    content = final_message.content

    if isinstance(content, list):
        text_parts = [part["text"] for part in content if part.get("type") == "text"]
        content = "\n".join(text_parts)

    content = content.strip()

    if content.startswith("```json"):
        content = content.removeprefix("```json").removesuffix("```").strip()
    elif content.startswith("```"):
        content = content.removeprefix("```").removesuffix("```").strip()

    return json.loads(content)

def main() -> None:
    load_dotenv()
    result = run_agent("Start up news in Nigeria")
    output = extract_json_output(result)
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
