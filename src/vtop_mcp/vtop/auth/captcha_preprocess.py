"""Image variants for VTOP captcha OCR."""

from __future__ import annotations

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


def red_stroke_grayscale(image: Image.Image) -> Image.Image:
    """Emphasize red captcha strokes on a white background."""
    rgb = image.convert("RGB")
    width, height = rgb.size
    gray = Image.new("L", (width, height))
    pixels = gray.load()
    source = rgb.load()
    for y in range(height):
        for x in range(width):
            red, green, blue = source[x, y]
            stroke = red - max(green, blue)
            pixels[x, y] = 255 if stroke > 35 else 0
    return gray


def preprocess_variants(image: Image.Image) -> list[Image.Image]:
    """Return RGB images to try with bitmap / ddddocr solvers."""
    rgb = image.convert("RGB")
    red_bin = red_stroke_grayscale(rgb)
    variants: list[Image.Image] = [rgb, red_bin.convert("RGB")]

    inverted = ImageOps.invert(red_bin)
    variants.append(inverted.convert("RGB"))

    contrast = ImageEnhance.Contrast(red_bin).enhance(2.5)
    variants.append(contrast.convert("RGB"))

    sharpened = rgb.filter(ImageFilter.SHARPEN)
    variants.append(sharpened)

    return variants
