import os
import requests
from .base import BaseVisionProvider, RateLimitError, ProviderError

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent"


class GeminiProvider(BaseVisionProvider):

    def __init__(self):
        self.keys = self._load_keys()
        self.current_index = 0
        self.model = os.getenv("GEMINI_MODEL", GEMINI_MODEL)

    def _load_keys(self) -> list:
        keys = []
        index = 1
        while True:
            key = os.getenv(f"GEMINI_APIKEY_{index}")
            if not key:
                break
            keys.append(key)
            index += 1
        if not keys:
            single_key = os.getenv("GEMINI_APIKEY")
            if single_key:
                keys.append(single_key)
        return keys

    @property
    def name(self) -> str:
        return "gemini"

    def is_available(self) -> bool:
        return bool(self.keys)

    def _next_key(self) -> str:
        key = self.keys[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.keys)
        return key

    def analyze(self, image_b64: str, mime_type: str, prompt: str) -> str:
        if not self.is_available():
            raise ProviderError("No GEMINI_APIKEY keys set in .env")
        last_error = None
        for _ in range(len(self.keys)):
            api_key = self._next_key()
            payload = {
                "contents": [{
                    "parts": [
                        {"inline_data": {"mime_type": mime_type, "data": image_b64}},
                        {"text": prompt}
                    ]
                }]
            }
            response = requests.post(
                GEMINI_API_URL % self.model,
                params={"key": api_key},
                json=payload,
                timeout=30
            )
            if response.status_code == 429:
                last_error = RateLimitError(f"Gemini key #{self.current_index} rate limited")
                continue
            if response.status_code != 200:
                raise ProviderError(f"Gemini error {response.status_code}: {response.text}")
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        raise last_error or RateLimitError("All Gemini keys rate limited")
