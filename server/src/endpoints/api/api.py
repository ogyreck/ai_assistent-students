from fastapi import APIRouter, HTTPException

from endpoints.models.models import ChatRequest, ChatResponse
from agent.chat_agent import ChatAgent
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

chat_agent = ChatAgent()


@router.post("/message", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    logger.info(f"Received chat request for session: {request.session_id}")

    try:
        response_text = chat_agent.chat(
            session_id=request.session_id,
            message=request.message
        )

        logger.info(f"Successfully processed chat request for session: {request.session_id}")

        return ChatResponse(
            response=response_text,
            session_id=request.session_id
        )

    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")