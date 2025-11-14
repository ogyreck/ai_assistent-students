import sys
import os

import uvicorn

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from endpoints.api.api import router as chat_router
from utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Student Assistant API",
    description="API 4;O G0B-0AA8AB5=B0 ABC45=B>2",
    version="0.1.0"
)

app.include_router(chat_router)


@app.get("/")
async def root():
    return {"message": "Student Assistant API is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":

    logger.info("Starting Student Assistant API server")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None
    )