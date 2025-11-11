from __future__ import annotations

from io import BytesIO
from typing import Iterable

import cv2
import numpy as np
from PIL import Image, ImageOps


def load_image(data: bytes) -> Image.Image:
    """Load bytes into a normalized RGB PIL image."""
    image = Image.open(BytesIO(data))
    if image.mode != "RGB":
        image = image.convert("RGB")
    return ImageOps.exif_transpose(image)


def detect_table_column_centers(image: Image.Image) -> list[float]:
    """
    Attempt to detect column centers by identifying vertical grid lines.
    Works best for screenshots that preserve the table borders.
    """
    cv_img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    height, width = cv_img.shape

    # Invert so grid lines become white, then isolate vertical structures.
    _, binary = cv2.threshold(cv_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel_size = max(10, height // 40)
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_size))
    vertical_lines = cv2.erode(binary, vertical_kernel, iterations=2)
    vertical_lines = cv2.dilate(vertical_lines, vertical_kernel, iterations=2)

    contours, _ = cv2.findContours(vertical_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return []

    line_centers: list[float] = []
    min_height = height * 0.5
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if h < min_height:
            continue
        line_centers.append(x + w / 2)

    if not line_centers or len(line_centers) < 2:
        return []

    line_centers = sorted(line_centers)
    deduped: list[float] = []
    for center in line_centers:
        if not deduped or center - deduped[-1] > 5:
            deduped.append(center)

    if len(deduped) < 2:
        return []

    # Column centers live midway between consecutive vertical lines.
    column_centers = [(deduped[i] + deduped[i + 1]) / 2 for i in range(len(deduped) - 1)]
    return column_centers


def chunk(iterable: Iterable, size: int):
    """Yield successive chunks from iterable."""
    bucket = []
    for item in iterable:
        bucket.append(item)
        if len(bucket) == size:
            yield bucket
            bucket = []
    if bucket:
        yield bucket
