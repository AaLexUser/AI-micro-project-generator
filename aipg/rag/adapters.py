import logging
from typing import List, Mapping, Optional, Sequence, Union, cast

from aipg.exceptions import OutputParserException
from aipg.rag.ports import EmbeddingPort, RetrievedItem, VectorStorePort

try:
    import chromadb
except ImportError:
    chromadb = None  # type: ignore

try:
    from google import genai
    from google.genai import Client
except ImportError:
    genai = None  # type: ignore

logger = logging.getLogger(__name__)


class ChromaDbAdapter(VectorStorePort):
    def __init__(self, collection_name: str, persist_dir: Optional[str] = None) -> None:
        if chromadb is None:
            raise ImportError("chromadb is not installed")

        self.collection_name = collection_name
        self.persist_dir = persist_dir
        self._client = None
        self._collection = None

    async def _get_client(self):
        """Get or create the async client."""
        if self._client is None:
            if self.persist_dir:
                # For persistent storage, we still need to use the sync client
                # as AsyncHttpClient doesn't support local persistence yet
                import asyncio
                from concurrent.futures import ThreadPoolExecutor

                def create_sync_client():
                    return chromadb.PersistentClient(path=self.persist_dir)

                loop = asyncio.get_running_loop()
                with ThreadPoolExecutor() as executor:
                    sync_client = await loop.run_in_executor(
                        executor, create_sync_client
                    )
                self._client = sync_client
            else:
                # Use AsyncHttpClient for remote connections
                self._client = await chromadb.AsyncHttpClient()
        return self._client

    async def _get_collection(self):
        """Get or create the collection."""
        if self._collection is None:
            client = await self._get_client()
            if self.persist_dir:
                # For sync client, run in executor
                import asyncio
                from concurrent.futures import ThreadPoolExecutor

                def get_collection():
                    return client.get_or_create_collection(
                        name=self.collection_name, metadata={"hnsw:space": "cosine"}
                    )

                loop = asyncio.get_running_loop()
                with ThreadPoolExecutor() as executor:
                    self._collection = await loop.run_in_executor(
                        executor, get_collection
                    )
            else:
                # For async client
                self._collection = await client.get_or_create_collection(
                    name=self.collection_name, metadata={"hnsw:space": "cosine"}
                )
        return self._collection

    async def add(
        self,
        ids: Sequence[str],
        embeddings: Sequence[Sequence[float]],
        metadatas: Sequence[Mapping[str, Union[str, int, float, bool]]],
    ) -> None:
        # Validate that all sequences have the same length
        ids_len = len(ids)
        embeddings_len = len(embeddings)
        metadatas_len = len(metadatas)

        if not (ids_len == embeddings_len == metadatas_len):
            raise ValueError(
                f"Length mismatch: ids={ids_len}, embeddings={embeddings_len}, metadatas={metadatas_len}. "
                "All sequences must have the same length."
            )

        collection = await self._get_collection()

        if self.persist_dir:
            # For sync client, run in executor
            import asyncio
            from concurrent.futures import ThreadPoolExecutor

            def add_to_collection():
                collection.add(
                    ids=list(ids),
                    embeddings=list(embeddings),
                    metadatas=list(metadatas),
                )

            loop = asyncio.get_running_loop()
            with ThreadPoolExecutor() as executor:
                await loop.run_in_executor(executor, add_to_collection)
        else:
            # For async client
            await collection.add(
                ids=list(ids), embeddings=list(embeddings), metadatas=list(metadatas)
            )

    async def query(self, embedding: List[float], k: int) -> List[RetrievedItem]:
        collection = await self._get_collection()

        if self.persist_dir:
            # For sync client, run in executor
            import asyncio
            from concurrent.futures import ThreadPoolExecutor

            def query_collection():
                return collection.query(
                    query_embeddings=embedding,
                    n_results=k,
                    include=["metadatas"],
                )

            loop = asyncio.get_running_loop()
            with ThreadPoolExecutor() as executor:
                res = await loop.run_in_executor(executor, query_collection)
        else:
            # For async client
            res = await collection.query(
                query_embeddings=embedding,
                n_results=k,
                include=["metadatas"],
            )

        items: List[RetrievedItem] = []
        metadatas = res.get("metadatas") or []
        if metadatas:
            for meta in metadatas[0]:
                topic = meta.get("topic", "")
                project_md = meta.get("project_md", "")

                # Parse raw markdown to reconstruct Project
                if project_md and isinstance(project_md, str):
                    try:
                        from aipg.prompting.utils import parse_project_markdown

                        micro_project = parse_project_markdown(project_md)
                    except OutputParserException as e:
                        # Skip items that can't be parsed
                        logger.warning(
                            f"Failed to parse raw markdown for topic '{topic}': {e}"
                        )
                        continue
                else:
                    continue

                items.append(
                    RetrievedItem(
                        topic=str(topic),
                        micro_project=micro_project,
                        metadata=dict(meta) if meta else None,
                    )
                )
        return items


class GeminiEmbeddingAdapter(EmbeddingPort):
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: str = "gemini-embedding-001",
        client: Optional[object] = None,
    ) -> None:
        if client is not None:
            self.client = client
        else:
            if genai is None:
                raise ImportError("Genai not available")
            self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.base_url = base_url

    async def embedding_processor(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if genai is None:
            raise ImportError("Genai not available")
        self.client = cast(Client, self.client)

        # Use the async aio module for embedding
        try:
            result = await self.client.aio.models.embed_content(
                model=self.model_name, contents=texts
            )
        except AttributeError:
            # Fallback to sync method in executor if aio is not available
            import asyncio
            from concurrent.futures import ThreadPoolExecutor

            def sync_embed():
                return self.client.models.embed_content(
                    model=self.model_name, contents=texts
                )

            loop = asyncio.get_running_loop()
            with ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(executor, sync_embed)

        if not result.embeddings:
            return []
        return [
            vectors.values
            for vectors in result.embeddings
            if vectors.values is not None
        ]
