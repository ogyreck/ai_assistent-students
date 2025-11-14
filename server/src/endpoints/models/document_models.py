from pydantic import BaseModel, Field


class UploadDocumentResponse(BaseModel):
    message: str = Field(..., description="Статус загрузки")
    chunks_count: int = Field(..., description="Количество созданных чанков")
    session_id: str = Field(..., description="ID сессии пользователя")