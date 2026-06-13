from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import Recursive

def main() -> None:
    load_dotenv()
    print("Learner Support project is ready.")


if __name__ == "__main__":
    main()
