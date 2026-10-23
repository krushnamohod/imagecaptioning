"""In-memory social media caption layouts rendered with Pillow."""

from io import BytesIO
from pathlib import Path
import os

from PIL import Image, ImageDraw, ImageFont

from app.config import SUPPORTED_LANGUAGES

TEMPLATES = {
    "minimal_footer", "gradient_overlay", "instagram_creative",
    "linkedin_professional", "facebook_informative", "x_concise",
}
CANVAS_PRESETS = {"original"}
FONT_ENV = "CAPTION_FONT_PATH"
FONT_CANDIDATES = (
    Path(os.environ.get(FONT_ENV, "")),
    Path(r"C:\Windows\Fonts\Nirmala.ttc"),
    Path(r"C:\Windows\Fonts\arial.ttf"),
    Path("/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
)
DEVANAGARI = range(0x0900, 0x0980)


class ImageRenderingError(ValueError):
    """The requested caption cannot be rendered with available font support."""


def _font(size: int, devanagari: bool) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    from PIL import features

    if devanagari and not features.check("raqm"):
        raise ImageRenderingError("Devanagari rendering requires Pillow RAQM shaping support.")
    for path in FONT_CANDIDATES:
        if path.is_file():
            try:
                font = ImageFont.truetype(str(path), size, layout_engine=ImageFont.Layout.RAQM)
                if devanagari and font.getmask("\u0915").getbbox() is None:
                    continue
                return font
            except (OSError, ValueError):
                continue
    if devanagari:
        raise ImageRenderingError(
            "No Devanagari-capable font was found. Set CAPTION_FONT_PATH to a Noto Sans Devanagari font."
        )
    return ImageFont.load_default()


def _wrap(text: str, draw: ImageDraw.ImageDraw, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    lines: list[str] = []

    def split_word(word: str) -> list[str]:
        pieces: list[str] = []
        piece = ""
        for char in word:
            if piece and draw.textbbox((0, 0), piece + char, font=font)[2] > max_width:
                pieces.append(piece)
                piece = char
            else:
                piece += char
        if piece:
            pieces.append(piece)
        return pieces

    for paragraph in text.splitlines() or [text]:
        line = ""
        for word in paragraph.split():
            if draw.textbbox((0, 0), word, font=font)[2] > max_width:
                if line:
                    lines.append(line)
                    line = ""
                pieces = split_word(word)
                lines.extend(pieces[:-1])
                line = pieces[-1] if pieces else ""
                continue
            candidate = f"{line} {word}".strip()
            if line and draw.textbbox((0, 0), candidate, font=font)[2] > max_width:
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
    return lines or [""]


def _canvas(image: Image.Image, preset: str) -> Image.Image:
    """Return the original pixel dimensions without resizing or orientation transforms."""
    if preset != "original":
        raise ImageRenderingError("Only the original canvas preset is supported.")
    return image.convert("RGB")


def _measure(caption: str, image: Image.Image, devanagari: bool, template: str):
    width, height = image.size
    margin_factor = 0.022 if template in {"linkedin_professional", "facebook_informative"} else 0.018
    margin = max(8, round(min(width, height) * margin_factor))
    size_factor = {
        "instagram_creative": 0.034,
        "linkedin_professional": 0.028,
        "facebook_informative": 0.030,
        "x_concise": 0.032,
    }.get(template, 0.034)
    max_font = min(46, max(18, round(width * size_factor)))
    min_font = 12
    draw = ImageDraw.Draw(image)
    available_width = max(1, width - 2 * margin - (2 * margin if template in {"instagram_creative", "linkedin_professional", "facebook_informative", "x_concise"} else 0))
    for size in range(max_font, min_font - 1, -2):
        font = _font(size, devanagari)
        lines = _wrap(caption, draw, font, available_width)
        box = font.getbbox("Ag")
        line_height = max(size, box[3] - box[1]) + max(1, round(size * 0.08))
        text_height = len(lines) * line_height
        padding_y = max(5, round(size * 0.30))
        height_needed = text_height + padding_y * 2
        height_needed += margin * 2 + 8 if template in {"linkedin_professional", "facebook_informative"} else 0
        if height_needed <= height:
            return draw, font, lines, line_height, margin, padding_y, height_needed
    raise ImageRenderingError("Caption is too long to fit without clipping at the minimum readable font size.")


def _draw_minimal(image, draw, font, lines, line_height, margin, padding_y, block_height, language):
    width, height = image.size
    top = height - block_height
    image.alpha_composite(Image.new("RGBA", (width, block_height), (7, 12, 18, 198)), (0, top))
    draw = ImageDraw.Draw(image)
    _draw_lines(draw, font, lines, margin, top + padding_y, line_height, language)


def _draw_gradient(image, draw, font, lines, line_height, margin, padding_y, block_height, language):
    width, height = image.size
    top = height - block_height
    gradient_strip = Image.new("RGBA", (1, block_height))
    pixels = gradient_strip.load()
    for y in range(block_height):
        alpha = round(215 * (y / max(1, block_height - 1)) ** 0.65)
        pixels[0, y] = (5, 10, 16, alpha)
    gradient = gradient_strip.resize((width, block_height))
    image.alpha_composite(gradient, (0, top))
    draw = ImageDraw.Draw(image)
    _draw_lines(draw, font, lines, margin, top + padding_y, line_height, language)


def _draw_instagram(image, draw, font, lines, line_height, margin, padding_y, block_height, language):
    width, height = image.size
    top = height - block_height
    panel = Image.new("RGBA", (width, block_height), (27, 20, 43, 226))
    image.alpha_composite(panel, (0, top))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, top, width, top + 4), fill=(255, 87, 119, 255))
    dot = max(6, round(margin * 0.55))
    draw.ellipse((width - margin - dot, top + padding_y, width - margin, top + padding_y + dot), fill=(255, 185, 73, 255))
    _draw_lines(draw, font, lines, margin, top + padding_y + 2, line_height, language)


def _draw_linkedin(image, draw, font, lines, line_height, margin, padding_y, block_height, language):
    width, height = image.size
    panel_height = block_height - margin * 2
    top = height - margin - panel_height
    panel = Image.new("RGBA", (width - margin * 2, panel_height), (246, 248, 250, 246))
    image.alpha_composite(panel, (margin, top))
    draw = ImageDraw.Draw(image)
    draw.rectangle((margin, top, margin + 4, top + panel_height), fill=(31, 91, 132, 255))
    _draw_lines(draw, font, lines, margin + 12, top + padding_y, line_height, language, fill=(28, 48, 64, 255))


def _draw_facebook(image, draw, font, lines, line_height, margin, padding_y, block_height, language):
    width, height = image.size
    panel_height = block_height - margin * 2
    top = height - margin - panel_height
    panel = Image.new("RGBA", (width - margin * 2, panel_height), (250, 247, 239, 248))
    image.alpha_composite(panel, (margin, top))
    draw = ImageDraw.Draw(image)
    marker = max(6, round(line_height * 0.30))
    draw.rounded_rectangle((margin + 10, top + padding_y, margin + 10 + marker, top + padding_y + marker), radius=3, fill=(61, 112, 190, 255))
    _draw_lines(draw, font, lines, margin + 20 + marker, top + padding_y, line_height, language, fill=(37, 48, 62, 255))


def _draw_x(image, draw, font, lines, line_height, margin, padding_y, block_height, language):
    width, height = image.size
    top = height - block_height
    image.alpha_composite(Image.new("RGBA", (width, block_height), (13, 17, 23, 238)), (0, top))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, top, 5, height), fill=(214, 238, 64, 255))
    _draw_lines(draw, font, lines, margin + 3, top + padding_y, line_height, language)


def _draw_lines(draw, font, lines, x, y, line_height, language, fill=(250, 252, 255, 255)):
    script_language = {"Hindi": "hi", "Marathi": "mr"}.get(language, "en")
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill, language=script_language)
        y += line_height


def render_captioned_image(
    image: Image.Image,
    caption: str,
    language: str,
    template: str = "gradient_overlay",
    canvas_preset: str = "original",
) -> bytes:
    """Render a caption using a social layout and return PNG bytes."""
    if language not in SUPPORTED_LANGUAGES:
        raise ImageRenderingError("Unsupported language.")
    if template not in TEMPLATES:
        raise ImageRenderingError("Unsupported template.")
    if canvas_preset not in CANVAS_PRESETS:
        raise ImageRenderingError("Unsupported canvas preset.")
    if not caption or not caption.strip():
        raise ImageRenderingError("Caption must not be empty.")
    caption = caption.strip()
    devanagari = language in {"Hindi", "Marathi"}
    base = _canvas(image, canvas_preset).convert("RGBA")
    measured = _measure(caption, base, devanagari, template)
    draw, font, lines, line_height, margin, padding_y, block_height = measured
    layouts = {
        "minimal_footer": _draw_minimal,
        "gradient_overlay": _draw_gradient,
        "instagram_creative": _draw_instagram,
        "linkedin_professional": _draw_linkedin,
        "facebook_informative": _draw_facebook,
        "x_concise": _draw_x,
    }
    layouts[template](base, draw, font, lines, line_height, margin, padding_y, block_height, language)
    output = BytesIO()
    base.convert("RGB").save(output, format="PNG", optimize=True)
    return output.getvalue()
