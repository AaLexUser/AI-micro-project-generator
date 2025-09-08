from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, List, Optional, Protocol, Tuple


@dataclass
class RetrievedItem:
    issue: str
    micro_project: str
    metadata: Optional[dict] = None


class EmbeddingPort(Protocol):
    def embed(self, texts: List[str]) -> List[List[float]]:  # pragma: no cover
        ...


class VectorStorePort(ABC):
    @abstractmethod
    def add(self, ids: List[str], embeddings: List[List[float]], metadatas: List[dict]):
        raise NotImplementedError

    @abstractmethod
    def query(self, embedding: List[float], k: int) -> List[RetrievedItem]:
        raise NotImplementedError

