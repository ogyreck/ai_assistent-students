from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="ID сессии пользователя")
    message: str = Field(..., description="Сообщение от пользователя")


class ChatResponse(BaseModel):
    response: str = Field(..., description="Ответ от ассистента")
    session_id: str = Field(..., description="ID сессии пользователя")