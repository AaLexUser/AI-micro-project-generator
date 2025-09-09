from typing import List, Optional

from rag.ports import VectorStorePort, RetrievedItem, EmbeddingPort

try:  # Optional dependency at runtime
    import chromadb  # type: ignore
except Exception:  # pragma: no cover - import-time optionality
    chromadb = None  # type: ignore

try:  # Optional dependency at runtime
    from google import genai  # type: ignore
except Exception:  # pragma: no cover - import-time optionality
    genai = None  # type: ignore

class ChromaDbAdapter(VectorStorePort):
    def __init__(
        self,
        collection_name: str,
        persist_dir: Optional[str] = None,


                 ):
        pass

    def query(self, embedding: List[float], k: int) -> List[RetrievedItem]:
        raise NotImplementedError

    def add(self, ids: List[str], embeddings: List[List[float]], metadatas: List[dict]) -> None:
        raise NotImplementedError

class GeminiEmbeddingAdapter(EmbeddingPort):
    def __init__(self,
        api_key: str = None,
        base_url: str = None,
        model_name: str = "gemini-embedding-001",
        client: Optional[object] = None)->None:
        if client is None:
            self.client = client
        else:
            if genai is None:
                raise ImportError("Genai not available")
            self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.base_url = base_url

    def embedding_processor(self, texts: List[str]) ->List[List[float]]:
        result = self.client.models.embed_content(model=self.model_name,contents = texts)
        return [vectors.values for vectors in result.embeddings]


