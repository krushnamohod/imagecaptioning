"""Combined image captioning and content generation API."""

from io import BytesIO
import sqlite3

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status
from groq import GroqError
from PIL import Image, UnidentifiedImageError

from app.config import (
    MAX_FILE_SIZE_MB,
    SUPPORTED_LANGUAGES,
    SUPPORTED_PLATFORMS,
    SUPPORTED_STYLES,
)
from app.models.caption import CaptionResponse
from app.services.image_renderer import TEMPLATES
from app.services.history_service import HistoryRepository
from app.services.blip_service import BlipService
from app.services.groq_service import GroqService

router = APIRouter(prefix="/generate", tags=["Combined Generation"])

ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


@router.post("/")
async def generate_image_content(
    request: Request,
    file: UploadFile = File(...),
    platform: str = Form(...),
    language: str = Form(...),
    style: str = Form(...),
    template: str | None = Form(None),
) -> dict[str, str | None]:
    """Generate and record both captions after successful completion.

    An optional ``template`` selection is stored with the history entry. When
    omitted, the stored visual template is NULL because caption generation does
    not select a rendering template on the caller's behalf.
    """

    # Validate the user's selections.
    if platform not in SUPPORTED_PLATFORMS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported platform. Choose from: {SUPPORTED_PLATFORMS}",
        )

    if language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported language. Choose from: {SUPPORTED_LANGUAGES}",
        )

    if style not in SUPPORTED_STYLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported style. Choose from: {SUPPORTED_STYLES}",
        )

    if template is not None and template not in TEMPLATES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported template. Choose from: {sorted(TEMPLATES)}",
        )

    # Read and validate the uploaded image.
    max_file_size = MAX_FILE_SIZE_MB * 1024 * 1024
    content = await file.read(max_file_size + 1)

    if len(content) > max_file_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image exceeds the {MAX_FILE_SIZE_MB} MB upload limit.",
        )

    try:
        with Image.open(BytesIO(content)) as source_image:
            if source_image.format not in ALLOWED_IMAGE_FORMATS:
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail="Upload a JPEG, PNG, or WEBP image.",
                )
            source_image.verify()

        with Image.open(BytesIO(content)) as source_image:
            image = source_image.convert("RGB")

    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is not a valid image.",
        ) from None

    # Step 1: Generate the base caption using BLIP.
    blip_service: BlipService = request.app.state.blip_service
    base_caption = blip_service.generate_caption(image)

    # Step 2: Generate customized content using Groq.
    try:
        groq_service = getattr(request.app.state, "groq_service", None)

        if groq_service is None:
            groq_service = GroqService()
            request.app.state.groq_service = groq_service

        generated_caption = groq_service.generate_caption(
            image_caption=base_caption,
            platform=platform,
            language=language,
            style=style,
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Content generation is not configured correctly.",
        ) from exc

    except GroqError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The content-generation provider failed. Please try again.",
        ) from exc

    # Persist only after both caption services returned successfully. The
    # template is NULL when the caller did not select one; none is inferred.
    try:
        history_repository: HistoryRepository = request.app.state.history_repository
        history_repository.insert(
            base_caption=base_caption,
            generated_caption=generated_caption,
            platform=platform,
            language=language,
            writing_style=style,
            visual_template=template,
        )
    except (AttributeError, sqlite3.Error) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Caption history is temporarily unavailable.",
        ) from exc

    # Return both captions to the frontend.
    return {
        "base_caption": base_caption,
        "generated_caption": generated_caption,
        "platform": platform,
        "language": language,
        "style": style,
        "visual_template": template,
    }
