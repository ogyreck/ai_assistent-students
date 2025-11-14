from typing import Optional

from service.QdrantService import QdrantService
from service.RerankerService import RerankerService
from service.СhunksService import ChunkProcessor
from service.LLMService import LLMService
from utils.logger import get_logger

log = get_logger("ServiceManager")


class ServiceManager:

    _instance: Optional['ServiceManager'] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not ServiceManager._initialized:
            log.info("Инициализация всех сервисов...")
            self._qdrant_service: Optional[QdrantService] = None
            self._reranker_service: Optional[RerankerService] = None
            self._chunk_processor: Optional[ChunkProcessor] = None
            self._llm_service: Optional[LLMService] = None
            ServiceManager._initialized = True

    def initialize(self):
        log.info("Загрузка ML-моделей и инициализация сервисов...")

        log.info("1/4 Инициализация QdrantService...")
        self._qdrant_service = QdrantService()

        log.info("2/4 Инициализация RerankerService...")
        self._reranker_service = RerankerService()

        log.info("3/4 Инициализация ChunkProcessor...")
        self._chunk_processor = ChunkProcessor()

        log.info("4/4 Инициализация LLMService...")
        self._llm_service = LLMService()

        log.info("Все сервисы успешно инициализированы и готовы к работе!")

    @property
    def qdrant_service(self) -> QdrantService:
        if self._qdrant_service is None:
            raise RuntimeError("QdrantService не инициализирован. Вызовите initialize() сначала.")
        return self._qdrant_service

    @property
    def reranker_service(self) -> RerankerService:
        if self._reranker_service is None:
            raise RuntimeError("RerankerService не инициализирован. Вызовите initialize() сначала.")
        return self._reranker_service

    @property
    def chunk_processor(self) -> ChunkProcessor:
        if self._chunk_processor is None:
            raise RuntimeError("ChunkProcessor не инициализирован. Вызовите initialize() сначала.")
        return self._chunk_processor

    @property
    def llm_service(self) -> LLMService:
        if self._llm_service is None:
            raise RuntimeError("LLMService не инициализирован. Вызовите initialize() сначала.")
        return self._llm_service


service_manager = ServiceManager()