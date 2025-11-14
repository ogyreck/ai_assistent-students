from typing import List, Dict
from service.document_parser import DocumentTextExtractor
from service.СhunksService import ChunkProcessor
from service.QdrantService import QdrantService
from utils.logger import get_logger

logger = get_logger(__name__)


class PDFProcessor:
    def __init__(self):
        self.extractor = DocumentTextExtractor()
        self.chunk_processor = ChunkProcessor()
        self.qdrant_service = QdrantService()
        logger.info("PDFProcessor initialized")

    def process_pdf(self, file_bytes: bytes, filename: str, session_id: str) -> int:
        try:
            logger.info(f"Processing PDF document: {filename} for session {session_id}")

            text = self.extractor(file_bytes, filename=filename)
            logger.info(f"Extracted {len(text)} characters from PDF")

            chunks_text = self.chunk_processor.create_chunks_with_overlap(text)
            logger.info(f"Created {len(chunks_text)} chunks")

            chunks = []
            for chunk_text in chunks_text:
                chunks.append({
                    "text": chunk_text,
                    "url": f"session://{session_id}",
                    "title": filename,
                })

            chunks_count = self.qdrant_service.add_chunks_directly(chunks)
            logger.info(f"Added {chunks_count} chunks to Qdrant for session {session_id}")

            return chunks_count

        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise