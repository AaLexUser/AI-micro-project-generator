import logging
import uuid
from typing import List

from aipg.domain import Project, Topic2Project
from aipg.rag.ports import EmbeddingPort, RetrievedItem, VectorStorePort

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
            raise ValueError("k_candidates must be positive (got %d)" % k_candidates)

    async def try_to_get(self, topic: str) -> List[Topic2Project]:
        """
        Try to retrieve a micro project for the given topic.
        Returns List[Topic2Project] if found, [] if not found.
        """
        embeddings = await self.embedder.embedding_processor([topic])
        if not embeddings:
            raise RuntimeError(f"Failed to generate embedding for topic: '{topic}'")
        topic_embedding = embeddings[0]
        candidates: List[RetrievedItem] = await self.vector_store.query(
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

    async def save(self, topic: str, micro_project: Project) -> None:
        logger.info(f"RAG save initiated for topic: '{topic}'")

        # Validate that micro_project content is not empty
        content = micro_project.raw_markdown.strip()
        if not content or content in ["", "<!-- -->", "<!-- -->", "<!--  -->"]:
            logger.warning(
                f"Empty or placeholder content detected for topic '{topic}' "
                f"and project '{micro_project.topic}': content='{micro_project.raw_markdown[:100]}...'"
            )
            raise RuntimeError(
                f"Cannot save empty or placeholder content for topic '{topic}' "
                f"and project '{micro_project.topic}'. Content must contain meaningful project data."
            )

        embeddings = await self.embedder.embedding_processor([topic])
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
        deterministic_id = uuid.uuid5(uuid.NAMESPACE_URL, content_for_hash).hex
        logger.debug("Generated deterministic ID: %s", deterministic_id)

        await self.vector_store.add(
            ids=[deterministic_id],
            embeddings=[topic_embedding],
            metadatas=[{"topic": topic, "project_md": raw_markdown}],
        )
        logger.info(
            f"RAG save completed: successfully saved micro project for topic '{topic}'"
        )
