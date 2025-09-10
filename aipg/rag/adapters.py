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
        """
        Initialize the ChromaDbAdapter by creating or opening a Chroma collection.
        
        Creates a Chroma client (persistent when persist_dir is provided, otherwise an in-memory client)
        and obtains or creates a collection named collection_name configured to use cosine distance for HNSW.
        
        Parameters:
            collection_name (str): Name of the Chroma collection to create or open.
            persist_dir (Optional[str]): If provided, path used to construct a PersistentClient for on-disk storage;
                if None, a regular in-memory Client is used.
        
        Raises:
            ImportError: If the chromadb package is not installed.
        """
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
        """
        Add vectors and their metadata to the underlying ChromaDB collection.
        
        The sequences are appended to the adapter's collection; corresponding entries in
        ids, embeddings, and metadatas must align by index (i.e., same length and order).
        This is a side-effecting operation that persists the provided items to the
        configured collection.
        """
        self.collection.add(
            ids=list(ids), 
            embeddings=list(embeddings), 
            metadatas=list(metadatas)
        )

    def query(self, embedding: List[float], k: int) -> List[RetrievedItem]:
        """
        Query the Chroma collection with a single embedding and return up to `k` retrieved items.
        
        Performs a k-nearest search using the provided single embedding and extracts item metadata to build RetrievedItem objects. For each result, the method:
        - reads `topic` and `micro_project` from the metadata,
        - if `micro_project` is a dict, attempts to construct a Project from it and skips the result on deserialization failure,
        - skips results where `micro_project` is neither a Project nor a dict that can be deserialized,
        - includes the original metadata dict (or None) on the returned RetrievedItem.
        
        Parameters:
            embedding (List[float]): A single embedding vector used as the query (the method wraps it for the underlying API).
            k (int): Maximum number of results to return.
        
        Returns:
            List[RetrievedItem]: Retrieved items with populated `topic`, `micro_project`, and optional `metadata`. May be empty if no valid items are found or all candidates are skipped.
        """
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
        """
        Initialize the GeminiEmbeddingAdapter.
        
        If a GenAI client instance is provided via `client`, it will be used; otherwise the adapter constructs a GenAI client with the provided `api_key`. The adapter stores `model_name` and `base_url` to be used for embedding requests.
        
        Parameters:
            api_key (Optional[str]): API key used to construct a GenAI client when `client` is not supplied.
            base_url (Optional[str]): Optional base URL for the embedding service (stored for request construction).
            model_name (str): Name of the embedding model to use (default: "gemini-embedding-001").
        
        Raises:
            ImportError: If no `client` is provided and the GenAI library is not available.
        """
        if client is not None:
            self.client = client
        else:
            if genai is None:
                raise ImportError("Genai not available")
            self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.base_url = base_url

    def embedding_processor(self, texts: List[str]) -> List[List[float]]:
        """
        Convert a list of input strings into embedding vectors using the configured GenAI client.
        
        Accepts a list of texts and returns a list of embedding vectors (list of floats) in the same order as the input for entries where the model returned vector values. Returns an empty list if the input is empty or if the model returned no embeddings. Embeddings with None values are omitted from the result.
        """
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
    """
    Create a ranker function that uses an LLM client to score candidate strings for semantic similarity to a query.
    
    The returned rank(query, candidates) callable sends a short two-message prompt (system + user) to the provided llm_query callable that asks the model to return a JSON array of floats in [0, 1], one score per candidate. Candidates are numbered in the prompt. Behavior:
    - If candidates is empty, returns [].
    - On success returns a list of floats with the same length as candidates.
    - If the LLM output is missing, invalid JSON, not a list of numbers, or the list length doesn't match candidates, returns a list of 0.0 values matching candidates' length.
    
    Parameters:
        llm_query: A callable that accepts either a prompt structure (list of message dicts) or a raw string and returns the LLM's textual response (or None). The ranker relies on llm_query producing a JSON array string like "[0.12, 0.5, 0.99]".
    """
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
