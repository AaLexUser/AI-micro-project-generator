from typing import Callable, List, Mapping, Optional, Sequence, Union

from aipg.rag.ports import EmbeddingPort, RetrievedItem, VectorStorePort

try:  # Optional dependency at runtime
    import chromadb  # type: ignore
except Exception:  # pragma: no cover - import-time optionality
    chromadb = None  # type: ignore

try:  # Optional dependency at runtime
    from google import genai  # type: ignore
except Exception:  # pragma: no cover - import-time optionality
    genai = None  # type: ignore


class ChromaDbAdapter(VectorStorePort):
    def __init__(self, collection_name: str, persist_dir: Optional[str] = None) -> None:
        if chromadb is None:  # pragma: no cover
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
        self.collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas)

    def query(self, embedding: List[float], k: int) -> List[RetrievedItem]:
        query_embeddings: Sequence[Sequence[float]] = [embedding]
        res = self.collection.query(
            query_embeddings=query_embeddings, n_results=k, include=["metadatas"]
        )
        items: List[RetrievedItem] = []
        metadatas = res.get("metadatas") or []
        if metadatas:
            for meta in metadatas[0]:
                topic = meta.get("topic", "")
                micro_project = meta.get("micro_project", "")
                items.append(
                    RetrievedItem(
                        topic=str(topic), micro_project=micro_project, metadata=meta
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

    def embedding_processor(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        result = self.client.models.embed_content(model=self.model_name, contents=texts)
        return [vectors.values for vectors in result.embeddings]


def llm_ranker_from_client(
    llm_query: Callable[[list[dict] | str], Optional[str]],
) -> Callable[[str, List[str]], List[float]]:
    def rank(query: str, candidates: List[str]) -> List[float]:
        if not candidates:
            return []
        numbered = "\n".join([f"{i + 1}. {c}" for i, c in enumerate(candidates)])
        prompt = [
            {
                "role": "system",
                "content": (
                    "You are a precise similarity rater. Given a query and a list of candidate topic, "
                    "return a JSON array of floats in [0,1] representing semantic similarity for each candidate."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Query: {query}\nCandidates:\n{numbered}\n\n"
                    "Return only JSON like [0.12, 0.5, 0.99]."
                ),
            },
        ]
        output = llm_query(prompt) or "[]"
        try:
            import json

            scores = json.loads(output)
            if not isinstance(scores, list):
                raise ValueError("Invalid scores format")
            return [float(x) for x in scores]
        except Exception:
            return [0.0 for _ in candidates]

    return rank
