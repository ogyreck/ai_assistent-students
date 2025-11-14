import sys
import os

import uvicorn

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from endpoints.api.api import router as chat_router

from utils.logger import get_logger
from server.src.service.ServiceManager import service_manager
from contextlib import asynccontextmanager

logger = get_logger("MAIN")

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

log = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Запуск приложения: инициализация сервисов...")
    service_manager.initialize()
    log.info("Приложение готово к работе!")
    yield
    log.info("Завершение работы приложения")


app = FastAPI(lifespan=lifespan)

app.default_response_class = JSONResponse

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(main_router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=6500,
        timeout_keep_alive=300,
        timeout_graceful_shutdown=30
    )