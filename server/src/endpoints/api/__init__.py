from fastapi import APIRouter
from endpoints.api.api import router as api_router


main_router = APIRouter()

main_router.include_router(api_router)