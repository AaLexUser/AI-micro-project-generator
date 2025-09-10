from __future__ import annotations

from aipg.configs.app_config import AppConfig

from .adapters import ChromaDbAdapter, GeminiEmbeddingAdapter
from .service import RagService


def build_rag_service(config: AppConfig) -> RagService:
    k_candidates = config.rag.k_candidates
    collection_name = config.rag.collection_name
    chroma_path = config.rag.chroma_path
    embedding_model = config.rag.embedding_model
    embedding_base_url = config.rag.embedding_base_url or config.llm.base_url
    embedding_api_key = config.rag.embedding_api_key or config.llm.api_key

    vector_store = ChromaDbAdapter(
        collection_name=collection_name, persist_dir=chroma_path
    )
    embedder = GeminiEmbeddingAdapter(
        api_key=embedding_api_key,
        base_url=embedding_base_url,
        model_name=embedding_model,
    )

    return RagService(
        embedder=embedder,
        vector_store=vector_store,
        k_candidates=k_candidates,
    )
