
import os

from qdrant_client import QdrantClient
from schema.document.document import Document
from retriever.qdrant_retriever import QdrantRetriever

def load_files_from_directory(directory_path):
    docs = []
    for filename in os.listdir(directory_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(directory_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    doc = Document(
                        page_content=content,
                        metadata={"filename": filename}
                    )
                    docs.append(doc)
            except Exception as e:
                print(f"Error reading file {filename}: {e}")
    return docs

if __name__ == "__main__":
    directory_path = "path/to/your/text/files"
    docs = load_files_from_directory(directory_path)

    qdrant_client = QdrantClient(
        url="https://xxxxxx-xxxxx-xxxxx-xxxx-xxxxxxxxx.us-east.aws.cloud.qdrant.io",
        api_key="<your-api-key>"
    )
    retriever = QdrantRetriever("retriever", qdrant_client=qdrant_client)
    retriever.add_documents(docs)
