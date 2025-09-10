import logging
from typing import List, Mapping, Optional, Sequence, Union

from google.genai import Client

from aipg.exceptions import OutputParserException
from aipg.rag.ports import EmbeddingPort, RetrievedItem, VectorStorePort

try:
    import chromadb
except ImportError:
    chromadb = None  # type: ignore

try:
    from google import genai
except ImportError:
    genai = None  # type: ignore

logger = logging.getLogger(__name__)


class ChromaDbAdapter(VectorStorePort):
    def __init__(self, collection_name: str, persist_dir: Optional[str] = None) -> None:
        if chromadb is None:
            raise ImportError("chromadb is not installed")

        if persist_dir:
            client = chromadb.PersistentClient(path=persist_dir)
        else:
            client = chromadb.Client()

        self.collection = client.get_or_create_collection(
            name=collection_name, metadata={"hnsw:space": "cosine"}
        )

    def add(
        self,
        ids: Sequence[str],
        embeddings: Sequence[Sequence[float]],
        metadatas: Sequence[Mapping[str, Union[str, int, float, bool]]],
    ) -> None:
        self.collection.add(
            ids=list(ids), embeddings=list(embeddings), metadatas=list(metadatas)
        )

    def query(self, embedding: List[float], k: int) -> List[RetrievedItem]:
        res = self.collection.query(
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
        client: Optional[Client] = None,
    ) -> None:
        if client is not None:
            self.client = client
        else:
            if genai is None:
                raise ImportError("Genai not available")
            self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.base_url = base_url

    def embedding_processor(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        result = self.client.models.embed_content(model=self.model_name, contents=texts)
        if not result.embeddings:
            return []
        return [
            vectors.values
            for vectors in result.embeddings
            if vectors.values is not None
        ]
