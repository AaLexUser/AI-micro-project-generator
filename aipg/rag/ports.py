from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from aipg.state import Project


@dataclass
class RetrievedItem:
    topic: str
    micro_project: Project
    metadata: Optional[dict] = None


@dataclass
class EmbeddingPort(ABC):
    @abstractmethod
    async def embedding_processor(self, texts: List[str]) -> List[List[float]]: ...


@dataclass
class VectorStorePort(ABC):
    @abstractmethod
    async def add(
        self, ids: List[str], embeddings: List[List[float]], metadatas: List[dict]
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def query(self, embedding: List[float], k: int) -> List[RetrievedItem]:
        raise NotImplementedError
