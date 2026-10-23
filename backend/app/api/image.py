"""Captioned image rendering endpoint."""

from io import BytesIO

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError

from app.config import ALLOWED_MIME_TYPES, MAX_FILE_SIZE_MB, SUPPORTED_LANGUAGES
from app.services.image_renderer import (
    CANVAS_PRESETS,
    TEMPLATES,
    ImageRenderingError,
    render_captioned_image,
)

router = APIRouter(prefix="/image", tags=["Image Rendering"])
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


@router.post("/captioned", response_class=Response)
async def create_captioned_image(
    file: UploadFile = File(...),
    caption: str = Form(..., min_length=1, max_length=2000),
    language: str = Form("English"),
    template: str = Form("gradient_overlay"),
    canvas_preset: str = Form("original"),
) -> Response:
    """Return a captioned PNG using a selectable layout and social canvas.

    Templates: gradient_overlay (default), minimal_footer, instagram_creative,
    linkedin_professional, facebook_informative, and x_concise.
    ``canvas_preset`` accepts only ``original`` (default), which preserves
    the uploaded image's exact pixel dimensions.
    """
    if language not in SUPPORTED_LANGUAGES:
        raise HTTPException(422, detail=f"Unsupported language. Choose from: {SUPPORTED_LANGUAGES}")
    if not caption.strip():
        raise HTTPException(422, detail="Caption must not be empty.")
    if template not in TEMPLATES:
        raise HTTPException(422, detail=f"Unsupported template. Choose from: {sorted(TEMPLATES)}")
    if canvas_preset not in CANVAS_PRESETS:
        raise HTTPException(422, detail=f"Unsupported canvas preset. Choose from: {sorted(CANVAS_PRESETS)}")
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(415, detail="Upload a JPEG, PNG, or WEBP image.")

    content = await file.read(MAX_FILE_SIZE_MB * 1024 * 1024 + 1)
    if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(413, detail=f"Image exceeds the {MAX_FILE_SIZE_MB} MB upload limit.")
    try:
        with Image.open(BytesIO(content)) as source:
            if source.format not in ALLOWED_IMAGE_FORMATS:
                raise HTTPException(415, detail="Upload a JPEG, PNG, or WEBP image.")
            source.verify()
        with Image.open(BytesIO(content)) as source:
            image = source.copy()
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(400, detail="The uploaded file is not a valid image.") from None

    try:
        rendered = render_captioned_image(image, caption, language, template, canvas_preset)
    except ImageRenderingError as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, detail="Captioned image rendering failed.") from exc
    return Response(
        content=rendered,
        media_type="image/png",
        headers={"Content-Disposition": 'inline; filename="captioned-image.png"'},
    )
