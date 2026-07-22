from langchain_anthropic import ChatAnthropic

# Define llm
def get_llm() -> ChatAnthropic:
    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        temperature=0
    )
    return llm