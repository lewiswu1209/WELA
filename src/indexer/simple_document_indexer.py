
import aiohttp
import aiofiles
import html2text

from typing import List
from readability import Document
from autogen_core.memory import Memory
from autogen_core.memory import MemoryContent
from autogen_core.memory import MemoryMimeType

class SimpleDocumentIndexer:

    def __init__(self, memory: Memory, chunk_size: int = 1500) -> None:
        self.memory = memory
        self.chunk_size = chunk_size

        self.__converter = html2text.HTML2Text()
        self.__converter.ignore_links = False
        self.__converter.ignore_images = False
        self.__converter.body_width = 0

    async def _fetch_content(self, source: str) -> str:
        if source.startswith(("http://", "https://")):
            async with aiohttp.ClientSession() as session:
                async with session.get(source) as response:
                    return await response.text()
        else:
            async with aiofiles.open(source, "r", encoding="utf-8") as f:
                return await f.read()

    def _strip_html(self, text: str) -> str:
        try:
            doc = Document(text)
            content = doc.summary()
        except Exception:
            content = text
        return self.__converter.handle(content)

    def _split_text(self, text: str, chunk_size: int) -> List[str]:
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

        chunks = []
        current_group = []
        current_count = 0

        for para in paragraphs:
            para_length = len(para)

            if para_length > chunk_size:
                if current_group:
                    chunks.append('\n'.join(current_group))
                    current_group = []
                    current_count = 0
                chunks.append(para)
                continue

            if current_count + para_length <= chunk_size:
                current_group.append(para)
                current_count += para_length
            else:
                if current_group:
                    chunks.append('\n'.join(current_group))
                current_group = [para]
                current_count = para_length

        if current_group:
            chunks.append('\n'.join(current_group))

        return chunks

    async def index_documents(self, sources: List[str], chunk_size: int) -> int:
        total_chunks = 0

        for source in sources:
            try:
                content = await self._fetch_content(source)

                # Strip HTML if content appears to be HTML
                if "<" in content and ">" in content:
                    content = self._strip_html(content)

                chunks = self._split_text(content, chunk_size)

                for i, chunk in enumerate(chunks):
                    await self.memory.add(
                        MemoryContent(
                            content=chunk, mime_type=MemoryMimeType.TEXT, metadata={"source": source, "chunk_index": i}
                        )
                    )

                total_chunks += len(chunks)

            except Exception as e:
                print(f"Error indexing {source}: {str(e)}")

        return total_chunks
