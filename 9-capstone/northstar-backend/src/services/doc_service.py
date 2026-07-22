import os
from typing import List
from langchain_core.documents import Document
from pathlib import Path

# Load all documents
def load_documents(folder_path: str | Path) -> List[Document]:
    documents = []

    for filename in os.listdir(folder_path): 
        if filename.endswith('.txt'):
            file_path = os.path.join(folder_path, filename)

            with open(file_path, 'r', encoding="utf-8") as file:
                text = file.read()
                doc = Document(
                    page_content=text,
                    metadata={
                        "source": filename
                    }
                )

                documents.append(doc)

    return documents