
from fastapi import APIRouter, HTTPException, Request
from groq import GroqError

from app.models.content import (
    ContentGenerationRequest,
    ContentGenerationResponse,
)
from app.services.groq_service import GroqService

router = APIRouter(prefix="/content", tags=["Content Generation"])


@router.post(
    "/generate",
    response_model=ContentGenerationResponse,
)
def generate_content(
    payload: ContentGenerationRequest,
    request: Request,
) -> ContentGenerationResponse:
    """Generate platform-specific content from a BLIP image caption."""

    try:
        service = getattr(request.app.state, "groq_service", None)

        if service is None:
            service = GroqService()
            request.app.state.groq_service = service

        caption = service.generate_caption(
            image_caption=payload.image_caption,
            platform=payload.platform,
            language=payload.language,
            style=payload.style,
        )

        return ContentGenerationResponse(caption=caption)

    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail="Content generation is not configured correctly.",
        ) from exc

    except GroqError as exc:
        raise HTTPException(
            status_code=502,
            detail="The content-generation provider failed. Please try again.",
        ) from exc
