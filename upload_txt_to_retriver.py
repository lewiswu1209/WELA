
import os
import sys
import yaml

from typing import Any
from typing import Dict
from qdrant_client import QdrantClient

from wela_agents.schema.document.document import Document
from wela_agents.retriever.qdrant_retriever import QdrantRetriever

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

def load_config(config_file_path: str = "config.yaml") -> Dict[str, Any]:
    config = None
    with open(os.path.join(os.path.realpath(os.path.dirname(sys.argv[0])), config_file_path), encoding="utf-8") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    return config

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python upload_txt_to_retriver.py <directory_path>")
        sys.exit(1)

    directory_path = sys.argv[1]
    docs = load_files_from_directory(directory_path)
    config = load_config()

    retriever_key = config.get("retriever").get("retriever_key", "retriever")
    url = config.get("retriever").get("qdrant").get("url")
    api_key = config.get("retriever").get("qdrant").get("api_key")

    qdrant_client = QdrantClient(
        url = url,
        api_key = api_key
    )
    retriever = QdrantRetriever(retriever_key, qdrant_client=qdrant_client)
    retriever.add_documents(docs)
