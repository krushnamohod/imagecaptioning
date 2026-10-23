
from app.services.groq_service import GroqService

service = GroqService()

caption = service.generate_caption(
    image_caption="A young boy is smiling at the beach.",
    platform="Instagram",
    language="Marathi",
    style="Creative",
)

print("Generated Marathi caption:")
print(caption)
