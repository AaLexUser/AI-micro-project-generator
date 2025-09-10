from __future__ import annotations

from aipg.configs.app_config import AppConfig
from aipg.llm import LLMClient

from .adapters import ChromaDbAdapter, GeminiEmbeddingAdapter, llm_ranker_from_client
from .service import RagService


def build_rag_service(config: AppConfig, llm: LLMClient) -> RagService:
    rag = getattr(config, "rag", None)
    similarity_threshold = getattr(rag, "similarity_threshold", 0.7)
    k_candidates = getattr(rag, "k_candidates", 5)
    collection_name = getattr(rag, "collection_name", "micro_projects")
    chroma_path = getattr(rag, "chroma_path", None)
    embedding_model = getattr(rag, "embedding_model", "gemini-embedding-001")
    embedding_base_url = getattr(rag, "embedding_base_url", None) or config.llm.base_url
    embedding_api_key = getattr(rag, "embedding_api_key", None) or config.llm.api_key

    vector_store = ChromaDbAdapter(
        collection_name=collection_name, persist_dir=chroma_path
    )
    embedder = GeminiEmbeddingAdapter(
        api_key=embedding_api_key,
        base_url=embedding_base_url,
        model_name=embedding_model,
    )
    ranker = llm_ranker_from_client(llm.query)

    return RagService(
        embedder=embedder,
        vector_store=vector_store,
        ranker=ranker,
        similarity_threshold=similarity_threshold,
        k_candidates=k_candidates,
    )
