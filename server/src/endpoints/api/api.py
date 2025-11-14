from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional

from endpoints.models.models import ChatResponse
from agent.chat_agent import ChatAgent
from service.pdf_processor import PDFProcessor
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

chat_agent = ChatAgent()
pdf_processor = PDFProcessor()


@router.post("/message", response_model=ChatResponse)
async def chat(
    session_id: str = Form(...),
    message: str = Form(...),
    file: Optional[UploadFile] = File(None)
) -> ChatResponse:
    logger.info(f"Received chat request for session: {session_id}")

    try:
        if file:
            if not file.filename.lower().endswith('.pdf'):
                logger.error(f"Invalid file format: {file.filename}")
                raise HTTPException(status_code=400, detail="Only PDF files are supported")

            file_bytes = await file.read()
            logger.info(f"Processing uploaded PDF: {file.filename}")

            chunks_count = pdf_processor.process_pdf(
                file_bytes=file_bytes,
                filename=file.filename,
                session_id=session_id
            )

            logger.info(f"PDF processed: {chunks_count} chunks added to database")

        response_text = chat_agent.chat(
            session_id=session_id,
            message=message
        )

        logger.info(f"Successfully processed chat request for session: {session_id}")

        return ChatResponse(
            response=response_text,
            session_id=session_id
        )

    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")