from dataclasses import dataclass
from enum import Enum
from typing import Optional, List

from google import genai
from openai.types import VectorStore
from posthog import api_key

from rag.ports import EmbeddingPort, VectorStorePort, RetrievedItem


class SourceEnum(Enum):
    RETRIEVED = 1
    GENERATED = 2


@dataclass
class RagResult:
    micro_project: str
    source: SourceEnum
    matched_topic: Optional[str]


class RagService:
    def __init__(
        self,
        embedder: EmbeddingPort,
        vector_store: VectorStorePort,
        similarity_threshold: float = 0.7,
        k_candidates: int = 5,
    ) -> None:
        self.embedder = embedder
        self.vector_store = vector_store
        self.similarity_threshold = similarity_threshold
        self.k_candidates = k_candidates
    def get_or_create_micro_project(self, topic: str) -> RagResult:
        issue_embedding = self.embedder.embed([topic])[0]
        candidates: List[RetrievedItem] = self.vector_store.query(
            embedding=issue_embedding, k=self.k_candidates
        )

#
#
# client = genai.Client(api_key="AIzaSyAHleRL_CaZUARvh4wTAs8ZDpgegDMCGAM")
# text = ["vector", "huector", "bebektor"]
# result = client.models.embed_content(
#     model="gemini-embedding-001", contents=text
# )
#
# print([k.values for k in result.embeddings])
