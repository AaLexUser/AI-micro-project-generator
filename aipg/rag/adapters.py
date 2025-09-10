from typing import Callable, List, Mapping, Optional, Sequence, Union

from google.genai import Client

from aipg.rag.ports import EmbeddingPort, RetrievedItem, VectorStorePort
from aipg.state import Project

try:
    import chromadb
except ImportError:
    chromadb = None # type: ignore

try:
    from google import genai
except ImportError:
    genai = None  # type: ignore


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
            ids=list(ids), 
            embeddings=list(embeddings), 
            metadatas=list(metadatas)
        )

    def query(self, embedding: List[float], k: int) -> List[RetrievedItem]:
        res = self.collection.query(
            # Wrap the single embedding in a list for the API
            query_embeddings=[embedding], n_results=k, include=["metadatas"]
        )
        items: List[RetrievedItem] = []
        metadatas = res.get("metadatas") or []
        if metadatas:
            for meta in metadatas[0]:
                topic = meta.get("topic", "")
                micro_project = meta.get("micro_project", "")
                
                # Reconstruct Project from metadata
                if isinstance(micro_project, dict):
                    try:
                        micro_project = Project(**micro_project)
                    except (TypeError, ValueError):
                        continue  # Skip items that can't be deserialized
                elif not isinstance(micro_project, Project):
                    continue  # Skip items that aren’t valid Project instances

                items.append(
                    RetrievedItem(
                        topic=str(topic),
                        micro_project=micro_project,
                        metadata=dict(meta) if meta else None
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
                    "You are a precise similarity rater. Given a query and a list of candidate topics, "
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
            float_scores = [float(x) for x in scores]
            # Ensure we have the right number of scores
            if len(float_scores) != len(candidates):
                return [0.0 for _ in candidates]
            return float_scores
        except Exception:
            return [0.0 for _ in candidates]

    return rank
