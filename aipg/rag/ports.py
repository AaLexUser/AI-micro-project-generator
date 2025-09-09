from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class RetrievedItem:
    topic: str
    micro_project: str
    metadata: Optional[dict] = None


@dataclass
class EmbeddingPort(ABC):
    @abstractmethod
    def embedding_processor(self, texts: List[str]) -> List[List[float]]: ...


@dataclass
class VectorStorePort(ABC):
    @abstractmethod
    def add(
        self, ids: List[str], embeddings: List[List[float]], metadatas: List[dict]
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def query(self, embedding: List[float], k: int) -> List[RetrievedItem]:
        raise NotImplementedError
