"""VTOP built-in captcha extraction and solving."""

from __future__ import annotations

import base64
import io
import json
import logging
from functools import lru_cache
from importlib import resources
from typing import Any

from PIL import Image

from vtop_mcp.exceptions import CaptchaSolveError

logger = logging.getLogger(__name__)

CHAR_WIDTH = 30
CHAR_HEIGHT = 30
CAPTCHA_LENGTH = 6


@lru_cache(maxsize=1)
def _load_bitmaps() -> dict[str, list[list[int]]]:
    path = resources.files("vtop_mcp.data").joinpath("bitmaps.json")
    raw = path.read_text(encoding="utf-8")
    data: dict[str, Any] = json.loads(raw)
    return {str(k): v for k, v in data.items()}


def decode_captcha_image(b64_jpeg: str) -> Image.Image:
    try:
        data = base64.b64decode(b64_jpeg)
        return Image.open(io.BytesIO(data)).convert("RGB")
    except Exception as exc:
        raise CaptchaSolveError("Could not decode captcha image") from exc


def _segment_bitmap(image: Image.Image) -> list[list[list[int]]]:
    """Split captcha into six 30x30 binary grids (red text on white)."""
    width, height = image.size
    if width < CAPTCHA_LENGTH or height < 4:
        raise CaptchaSolveError("Captcha image too small")

    slice_width = width // CAPTCHA_LENGTH
    segments: list[list[list[int]]] = []
    for index in range(CAPTCHA_LENGTH):
        left = index * slice_width
        box = image.crop((left, 0, left + slice_width, height))
        resized = box.resize((CHAR_WIDTH, CHAR_HEIGHT), Image.Resampling.BILINEAR)
        grid: list[list[int]] = []
        for y in range(CHAR_HEIGHT):
            row: list[int] = []
            for x in range(CHAR_WIDTH):
                red, green, blue = resized.getpixel((x, y))
                row.append(1 if red > 160 and green < 120 and blue < 120 else 0)
            grid.append(row)
        segments.append(grid)
    return segments


def _score(a: list[list[int]], b: list[list[int]]) -> float:
    total = 0
    matches = 0
    for row_a, row_b in zip(a, b):
        for left, right in zip(row_a, row_b):
            total += 1
            if left == right:
                matches += 1
    return matches / total if total else 0.0


def _match_segment(segment: list[list[int]], templates: dict[str, list[list[int]]]) -> str:
    best_char = "?"
    best_score = -1.0
    for char, template in templates.items():
        if len(template) != CHAR_HEIGHT:
            continue
        score = _score(segment, template)
        if score > best_score:
            best_score = score
            best_char = char
    if best_score < 0.45:
        raise CaptchaSolveError(f"Low captcha confidence ({best_score:.2f})")
    return best_char


def solve_captcha_image(image: Image.Image) -> str:
    templates = _load_bitmaps()
    chars: list[str] = []
    for segment in _segment_bitmap(image):
        chars.append(_match_segment(segment, templates))
    text = "".join(chars).upper()
    if len(text) != CAPTCHA_LENGTH:
        raise CaptchaSolveError("Unexpected captcha length")
    return text


def solve_captcha_base64(b64_jpeg: str) -> str:
    image = decode_captcha_image(b64_jpeg)
    try:
        return solve_captcha_image(image)
    except CaptchaSolveError:
        return _ddddocr_fallback(image)


def _ddddocr_fallback(image: Image.Image) -> str:
    try:
        import ddddocr
    except ImportError as exc:
        raise CaptchaSolveError(
            "Bitmap solve failed and optional ddddocr is not installed"
        ) from exc

    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    ocr = ddddocr.DdddOcr(show_ad=False)
    text = ocr.classification(buf.getvalue())
    cleaned = "".join(ch for ch in text.upper() if ch.isalnum())
    if len(cleaned) != CAPTCHA_LENGTH:
        raise CaptchaSolveError("ddddocr captcha length mismatch")
    return cleaned
