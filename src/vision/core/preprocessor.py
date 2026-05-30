import base64
import io
import os
from PIL import Image

MAX_SIZE = (1024, 1024)
JPEG_QUALITY = 85


def preprocess_image(image_path: str) -> tuple:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    with Image.open(image_path) as img:
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        img.thumbnail(MAX_SIZE, Image.LANCZOS)

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        buffer.seek(0)

        image_b64 = base64.b64encode(buffer.read()).decode("utf-8")

    return image_b64, "image/jpeg"
