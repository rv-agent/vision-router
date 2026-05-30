"""Vision Router — analyze images via Gemini/OpenRouter with auto-fallback."""
import os, sys
from dotenv import load_dotenv

# Load .env from project root
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
load_dotenv(_env_path)

from .core.preprocessor import preprocess_image
from .core.router import route


def analyze_image(path: str, prompt: str = "Describe this image in detail") -> dict:
    """Analyze an image using configured providers with auto-fallback.

    Args:
        path: Path to image file
        prompt: Analysis prompt

    Returns:
        dict with keys: success, provider, result, error
    """
    if not os.path.exists(path):
        return {"success": False, "provider": None, "result": None,
                "error": f"File not found: {path}"}
    b64, mime = preprocess_image(path)
    return route(b64, mime, prompt)
