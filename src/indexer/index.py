
import asyncio
import argparse

from autogen_core.memory import Memory
from wela_agent.config_loader import get_wela_config
from indexer.simple_document_indexer import SimpleDocumentIndexer

async def main():
    parser = argparse.ArgumentParser(description="Index AutoGen documentation")
    parser.add_argument("--source", help="URL of the document to index", action='append', required=True)
    args = parser.parse_args()
    sources = args.source

    config = get_wela_config("config.yaml")
    rag_memory: Memory = config.runtime["rag"]

    async def index_autogen_docs() -> None:
        indexer = SimpleDocumentIndexer(memory=rag_memory)
        chunks: int = await indexer.index_documents(sources, 1024)
        print(f"Indexed {chunks} chunks from {len(sources)} documents.")

    await index_autogen_docs()

    await rag_memory.close()

if __name__ == "__main__":
    asyncio.run(main())
