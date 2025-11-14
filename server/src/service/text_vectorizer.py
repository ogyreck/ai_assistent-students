import httpx
from typing import List, Optional, Callable
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance


class TextVectorizer:
    """
    Векторизация через внешнее API (например, OpenAI / Cohere / custom).
    Работает без локальных ML-библиотек.
    """

    def __init__(
        self,
        vector_size: int,
        max_context_length: int = 40_000,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        collection_name: str = "document_chunks",
        timeout: float = 30.0,
    ):
        """
        :param vectorize_fn: функция, которая принимает строку и возвращает список float (вектор)
        :param vector_size: размер вектора (например, 1536 для text-embedding-3-small)
        :param max_context_length: порог длины текста для векторизации
        """
        self.vector_size = vector_size
        self.max_context_length = max_context_length
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.collection_name = collection_name
        self.client = QdrantClient(":memory:")
        self.chunks: List[str] = []
        self._vectorized = False
        self.timeout = timeout

    def __call__(self, text: str) -> "TextVectorizer":
        if not isinstance(text, str):
            raise TypeError("Input must be a string")

        if len(text) <= self.max_context_length:
            self._vectorized = False
            self.chunks = []
            return self

        # Нарезка
        self.chunks = self._chunk_text(text)

        # Удаляем старую коллекцию
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass

        # Создаём новую
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE)
        )

        # Векторизация и загрузка
        points = []
        for i, chunk in enumerate(self.chunks):
            vector = self.vectorize_fn(chunk)
            if len(vector) != self.vector_size:
                raise ValueError(f"Вектор chunk #{i} имеет размер {len(vector)}, ожидался {self.vector_size}")
            points.append(PointStruct(id=i, vector=vector, payload={"chunk": chunk}))

        self.client.upsert(collection_name=self.collection_name, points=points)
        self._vectorized = True
        return self

    def vectorize_fn(text: str) -> List[float]:
        response = httpx.post(
            "https://api.openai.com/v1/embeddings",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={"input": text, "model": OPENAI_EMBEDDING_MODEL},
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]


    def _chunk_text(self, text: str) -> List[str]:
        chunks = []
        start = 0
        step = self.chunk_size - self.chunk_overlap
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk)
            start += step
        return chunks

    def is_vectorized(self) -> bool:
        return self._vectorized

    def search(self, query: str, k: int = 5) -> List[dict]:
        if not self._vectorized:
            return []
        query_vector = self.vectorize_fn(query)
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=k
        )
        return [{"chunk": hit.payload["chunk"], "score": hit.score} for hit in results]