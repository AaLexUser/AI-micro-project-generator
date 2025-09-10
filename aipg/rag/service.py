import hashlib
import logging
from typing import List

from aipg.rag.ports import EmbeddingPort, RetrievedItem, VectorStorePort
from aipg.state import Project, Topic2Project

logger = logging.getLogger(__name__)


class RagService:
    def __init__(
        self,
        embedder: EmbeddingPort,
        vector_store: VectorStorePort,
        k_candidates: int = 5,
    ) -> None:
        self.embedder = embedder
        self.vector_store = vector_store
        self.k_candidates = k_candidates

        if k_candidates <= 0:
            raise ValueError("k_candidates must be positive")

    def try_to_get(self, topic: str) -> List[Topic2Project]:
        """
        Try to retrieve a micro project for the given topic.
        Returns List[Topic2Project] if found, [] if not found.
        """
        embeddings = self.embedder.embedding_processor([topic])
        if not embeddings:
            raise RuntimeError(f"Failed to generate embedding for topic: '{topic}'")
        topic_embedding = embeddings[0]
        candidates: List[RetrievedItem] = self.vector_store.query(
            embedding=topic_embedding, k=self.k_candidates
        )
        topic_candidates = [candidate.topic for candidate in candidates]
        if topic_candidates:
            result = [
                Topic2Project(topic=candidate.topic, project=candidate.micro_project)
                for candidate in candidates
            ]
            logger.info(
                f"RAG search successful: found {len(result)} matching projects for topic '{topic}'"
            )
            logger.debug(f"Found topics: {topic_candidates}")
            return result

        logger.info(
            f"RAG search completed: no matching projects found for topic '{topic}'"
        )
        return []

    def save(self, topic: str, micro_project: Project) -> None:
        logger.info(f"RAG save initiated for topic: '{topic}'")

        embeddings = self.embedder.embedding_processor([topic])
        if not embeddings:
            raise RuntimeError(f"Failed to generate embedding for topic: '{topic}'")

        topic_embedding = embeddings[0]
        logger.debug(
            f"Generated embedding for topic '{topic}' (dimension: {len(topic_embedding)})"
        )

        # Store only the raw markdown for simplicity
        raw_markdown = micro_project.raw_markdown
        logger.debug(
            f"Storing raw markdown for topic '{topic}' (length: {len(raw_markdown)} chars)"
        )

        # Generate deterministic unique ID from topic and raw_markdown
        content_for_hash = f"{topic}:{raw_markdown}"
        deterministic_id = hashlib.sha1(content_for_hash.encode("utf-8")).hexdigest()
        logger.debug(f"Generated deterministic ID: {deterministic_id}")

        self.vector_store.add(
            ids=[deterministic_id],
            embeddings=[topic_embedding],
            metadatas=[{"topic": topic, "project_md": raw_markdown}],
        )
        logger.info(
            f"RAG save completed: successfully saved micro project for topic '{topic}'"
        )
