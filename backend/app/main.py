"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from app.api.generate import router as generate_router
from app.api.history import router as history_router


from app.api.caption import router as caption_router
from app.api.content import router as content_router
from app.api.image import router as image_router
from app.services.blip_service import BlipService
from app.config import HISTORY_DB_PATH
from app.services.history_service import HistoryRepository


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    history_repository = HistoryRepository(HISTORY_DB_PATH)
    history_repository.initialize()
    app.state.history_repository = history_repository
    app.state.blip_service = BlipService()
    yield


app = FastAPI(title="Image Captioning API", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

app.include_router(content_router, prefix="/api/v1")
app.include_router(caption_router, prefix="/api/v1")
app.include_router(generate_router, prefix="/api/v1")
app.include_router(image_router, prefix="/api/v1")
app.include_router(history_router, prefix="/api/v1")
