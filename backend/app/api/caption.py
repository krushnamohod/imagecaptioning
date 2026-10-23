"""Image captioning API routes."""

from io import BytesIO

from fastapi import APIRouter, HTTPException, Request, UploadFile, status
from PIL import Image, UnidentifiedImageError

from app.config import MAX_FILE_SIZE_MB
from app.models.caption import CaptionResponse
from app.services.blip_service import BlipService

router = APIRouter()
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


@router.post("/caption", response_model=CaptionResponse)
async def caption_image(request: Request, file: UploadFile) -> CaptionResponse:
    """Generate a caption for an uploaded JPEG, PNG, or WEBP image."""
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
                    detail="Unsupported image type. Upload a JPEG, PNG, or WEBP image.",
                )
            source_image.verify()

        with Image.open(BytesIO(content)) as source_image:
            image = source_image.convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is not a valid image.",
        ) from None

    blip_service: BlipService = request.app.state.blip_service
    return CaptionResponse(caption=blip_service.generate_caption(image))
