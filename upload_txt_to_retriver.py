
import os
import sys
import yaml

from typing import Any
from typing import Dict
from typing import List
from qdrant_client import QdrantClient

from wela_agents.schema.document.document import Document
from wela_agents.embedding.text_embedding import TextEmbedding
from wela_agents.embedding.openai_embedding import OpenAIEmbedding
from wela_agents.retriever.qdrant_retriever import QdrantRetriever

def split_text_by_paragraphs(text: str, max_chars: int) -> List[str]:
    paragraphs = []
    current_para = []

    for line in text.splitlines():
        if not line.strip():
            continue

        current_para.append(line)

        if line.strip().endswith(('。', '!', '?', '.', '！', '？')) or len(line) > 50:
            if current_para:
                paragraphs.append('\n'.join(current_para))
                current_para = []

    if current_para:
        paragraphs.append('\n'.join(current_para))

    if not paragraphs:
        paragraphs = [line for line in text.splitlines() if line.strip()]

    result = []
    current_group = []
    current_count = 0

    for para in paragraphs:
        para_length = len(para)

        if para_length > max_chars:
            if current_group:
                result.append('\n'.join(current_group))
                current_group = []
                current_count = 0
            result.append(para)
            continue

        if current_count + para_length <= max_chars:
            current_group.append(para)
            current_count += para_length
        else:
            if current_group:
                result.append('\n'.join(current_group))
            current_group = [para]
            current_count = para_length

    if current_group:
        result.append('\n'.join(current_group))

    return result

def load_files_from_directory(directory_path):
    docs = []
    for filename in os.listdir(directory_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(directory_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    results = split_text_by_paragraphs(content, 2000)
                    docs = [Document(
                        page_content=result,
                        metadata={
                            "filename": filename
                        }
                    ) for result in results]
                    docs.extend(docs)
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
    if config.get("retriever").get("embedding").get("type") == "openai":
        embedding = OpenAIEmbedding(
            model_name=config.get("retriever").get("embedding").get("model_name"),
            base_url=config.get("retriever").get("embedding").get("base_url"),
            api_key=config.get("retriever").get("embedding").get("api_key")
        )
    else:
        embedding = TextEmbedding(model="iic/nlp_gte_sentence-embedding_chinese-small")

    qdrant_client = QdrantClient(
        url = url,
        api_key = api_key
    )
    retriever = QdrantRetriever(retriever_key, embedding=embedding, qdrant_client=qdrant_client, vector_size=config.get("retriever").get("vector_size"))
    retriever.add_documents(docs)
