
from groq import Groq

from app.config import GROQ_API_KEY, GROQ_MODEL


class GroqService:
    """Generate platform-specific content using the Groq API."""

    def __init__(self) -> None:
        if not GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is missing. Configure it in backend/.env."
            )

        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = GROQ_MODEL

    def generate_caption(
        self,
        image_caption: str,
        platform: str,
        language: str,
        style: str,
    ) -> str:
        """Generate an original social media caption from a BLIP description."""

        system_prompt = (
            "You are a multilingual social media copywriter, not a translator. "
            "Write original, natural content in the requested language. "
            "Follow the requested platform and style. "
            "Stay faithful to the supplied image description. "
            "Do not invent unsupported people, actions, locations, or events. "
            "Return only the requested caption, without explanations."
        )

        user_prompt = (
            f"Image description: {image_caption}\n"
            f"Platform: {platform}\n"
            f"Output language: {language}\n"
            f"Writing style: {style}\n\n"
            "Write one suitable social media caption. "
            "Use natural language and relevant emojis when appropriate. "
            "For Instagram, include at most three relevant hashtags. "
            "For other platforms, use hashtags only when appropriate."
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_completion_tokens=800,
        )

        content = response.choices[0].message.content

        if not content or not content.strip():
            raise RuntimeError("Groq returned an empty caption.")

        return content.strip()
