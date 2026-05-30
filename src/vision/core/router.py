import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vision.providers.gemini import GeminiProvider
from vision.providers.openrouter import OpenRouterProvider
from vision.providers.base import RateLimitError, ProviderError

PROVIDER_MAP = {
    "gemini": GeminiProvider,
    "openrouter": OpenRouterProvider
}


def get_fallback_order() -> list:
    order = os.getenv("FALLBACK_ORDER", "gemini,openrouter")
    return [p.strip() for p in order.split(",")]


def route(image_b64: str, mime_type: str, prompt: str) -> dict:
    fallback_order = get_fallback_order()
    providers = []

    for name in fallback_order:
        if name in PROVIDER_MAP:
            provider = PROVIDER_MAP[name]()
            if provider.is_available():
                providers.append(provider)

    if not providers:
        return {
            "success": False,
            "provider": None,
            "result": None,
            "error": "No providers configured. Check your .env file."
        }

    last_error = None

    for provider in providers:
        try:
            result = provider.analyze(image_b64, mime_type, prompt)
            return {
                "success": True,
                "provider": provider.name,
                "result": result,
                "error": None
            }
        except RateLimitError as e:
            last_error = str(e)
            print(f"[vision-router] {provider.name} rate limited, trying next provider...")
            continue
        except ProviderError as e:
            last_error = str(e)
            print(f"[vision-router] {provider.name} failed: {e}, trying next provider...")
            continue

    return {
        "success": False,
        "provider": None,
        "result": None,
        "error": f"All providers failed. Last error: {last_error}"
    }
