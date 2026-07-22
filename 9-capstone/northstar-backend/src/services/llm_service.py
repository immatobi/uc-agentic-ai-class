from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

# Define llm
def get_llm(provider: str = "anthropic") -> ChatAnthropic:
    if provider == "anthropic":
        llm = ChatAnthropic(
            model="claude-sonnet-4-6",
            temperature=0
        )
    elif provider == "google":
        llm = ChatGoogleGenerativeAI(
            model="gemini-3.1-pro-preview",
            temperature=0
        )
    return llm

def get_llm_text(content) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []

        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("text", "")))
            else:
                text = getattr(item, "text", None)
                if text:
                    parts.append(str(text))

        return "\n".join(parts)

    return str(content)