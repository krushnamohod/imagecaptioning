"""Offline coverage for caption templates and original-size output."""

import inspect
import unittest
from io import BytesIO

from PIL import Image

from app.api.image import create_captioned_image
from app.services.image_renderer import (
    CANVAS_PRESETS,
    TEMPLATES,
    ImageRenderingError,
    render_captioned_image,
)

EXPECTED_TEMPLATES = {
    "gradient_overlay", "instagram_creative", "linkedin_professional",
    "facebook_informative", "x_concise", "minimal_footer",
}


class ImageRendererTests(unittest.TestCase):
    def setUp(self) -> None:
        self.image = Image.new("RGB", (640, 400), "#477c9b")

    def render(self, caption="A calm lake at sunrise", language="English", template=None, canvas_preset="original"):
        kwargs = {"canvas_preset": canvas_preset}
        if template is not None:
            kwargs["template"] = template
        content = render_captioned_image(self.image, caption, language, **kwargs)
        result = Image.open(BytesIO(content))
        result.load()
        self.assertEqual(result.format, "PNG")
        return result

    def test_templates_canvas_and_exact_dimensions(self):
        self.assertEqual(TEMPLATES, EXPECTED_TEMPLATES)
        self.assertEqual(CANVAS_PRESETS, {"original"})
        for template in TEMPLATES:
            with self.subTest(template=template):
                rendered = self.render(template=template)
                self.assertEqual(rendered.size, self.image.size)
        with self.assertRaises(ImageRenderingError):
            render_captioned_image(self.image, "caption", "English", canvas_preset="square")

    def test_service_and_endpoint_default_to_gradient_overlay(self):
        implicit = render_captioned_image(self.image, "A calm lake", "English")
        explicit = render_captioned_image(self.image, "A calm lake", "English", "gradient_overlay")
        self.assertEqual(implicit, explicit)
        self.assertEqual(
            inspect.signature(create_captioned_image).parameters["template"].default.default,
            "gradient_overlay",
        )

    def test_short_platform_captions_use_compact_panels(self):
        for template in ("instagram_creative", "linkedin_professional", "facebook_informative", "x_concise"):
            with self.subTest(template=template):
                rendered = self.render(template=template)
                changed_rows = sum(
                    rendered.getpixel((self.image.width // 2, y)) != self.image.getpixel((self.image.width // 2, y))
                    for y in range(self.image.height)
                )
                self.assertLessEqual(changed_rows, self.image.height * 0.20)

    def test_long_captions_wrap_and_keep_dimensions(self):
        caption = "A calm lake at sunrise with mountains in the distance " * 30
        for template in TEMPLATES:
            with self.subTest(template=template):
                self.assertEqual(self.render(caption, template=template).size, self.image.size)

    def test_hindi_and_marathi_shape_in_all_templates(self):
        samples = (
            ("\u0938\u0941\u0902\u0926\u0930 \u0938\u0941\u092c\u0939 \u0915\u093e \u0926\u0943\u0936\u094d\u092f", "Hindi"),
            ("\u0938\u0941\u0902\u0926\u0930 \u0938\u0915\u093e\u0933\u091a\u0947 \u0926\u0943\u0936\u094d\u092f", "Marathi"),
        )
        for caption, language in samples:
            for template in TEMPLATES:
                with self.subTest(language=language, template=template):
                    self.assertEqual(self.render(caption, language, template).size, self.image.size)


if __name__ == "__main__":
    unittest.main()
