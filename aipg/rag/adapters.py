from __future__ import annotations

from typing import List, Optional, Callable

try:  # Optional dependency at runtime
    import chromadb  # type: ignore
except Exception:  # pragma: no cover - import-time optionality
    chromadb = None  # type: ignore

try:  # Optional dependency at runtime
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover - import-time optionality
    OpenAI = None  # type: ignore

from .ports import EmbeddingPort, VectorStorePort, RetrievedItem


class ChromaVectorStore(VectorStorePort):
    def __init__(
        self,
        collection_name: str = "micro_projects",
        persist_dir: Optional[str] = None,
    ) -> None:
        if chromadb is None:  # pragma: no cover
            raise ImportError("chromadb is not installed")

        if persist_dir:
            client = chromadb.PersistentClient(path=persist_dir)
        else:
            client = chromadb.Client()

        self.collection = client.get_or_create_collection(
            name=collection_name, metadata={"hnsw:space": "cosine"}
        )

    def add(self, ids: List[str], embeddings: List[List[float]], metadatas: List[dict]):
        self.collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas)

    def query(self, embedding: List[float], k: int) -> List[RetrievedItem]:
        res = self.collection.query(
            query_embeddings=[embedding], n_results=k, include=["metadatas"]
        )
        items: List[RetrievedItem] = []
        metadatas = res.get("metadatas") or []
        if metadatas:
            for meta in metadatas[0]:
                issue = meta.get("issue", "")
                micro_project = meta.get("micro_project", "")
                items.append(RetrievedItem(issue=issue, micro_project=micro_project, metadata=meta))
        return items


class OpenAIEmbeddingAdapter(EmbeddingPort):
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "text-embedding-3-small",
        client: Optional[object] = None,
    ) -> None:
        if client is not None:
            self.client = client
        else:
            if OpenAI is None:  # pragma: no cover
                raise ImportError("openai is not installed")
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def embed(self, texts: List[str]) -> List[List[float]]:
        resp = self.client.embeddings.create(model=self.model, input=texts)
        return [d.embedding for d in resp.data]


def llm_ranker_from_client(llm_query: Callable[[list[dict] | str], Optional[str]]) -> Callable[[str, List[str]], List[float]]:
    def rank(query: str, candidates: List[str]) -> List[float]:
        if not candidates:
            return []
        numbered = "\n".join([f"{i+1}. {c}" for i, c in enumerate(candidates)])
        prompt = [
            {
                "role": "system",
                "content": (
                    "You are a precise similarity rater. Given a query and a list of candidate issues, "
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

