"""Fine-tuned BLIP image captioning service."""

import torch
from PIL import Image
from transformers import BlipForConditionalGeneration, BlipProcessor

from app.config import BLIP_MODEL_PATH


class BlipService:
    """Loads the configured BLIP model once and uses it for captioning."""

    def __init__(self) -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.processor = BlipProcessor.from_pretrained(str(BLIP_MODEL_PATH))
        self.model = BlipForConditionalGeneration.from_pretrained(str(BLIP_MODEL_PATH))
        self.model.to(self.device)
        self.model.eval()

    def generate_caption(self, image: Image.Image) -> str:
        """Generate a caption for an RGB PIL image using beam search."""
        inputs = self.processor(images=image, return_tensors="pt")
        inputs = {name: tensor.to(self.device) for name, tensor in inputs.items()}

        with torch.no_grad():
            output = self.model.generate(**inputs, num_beams=5, max_new_tokens=50)

        return self.processor.decode(output[0], skip_special_tokens=True).strip()
