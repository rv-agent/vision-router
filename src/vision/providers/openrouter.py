import os
import requests
from .base import BaseVisionProvider, RateLimitError, ProviderError

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "google/gemini-3.5-flash"


class OpenRouterProvider(BaseVisionProvider):

    def __init__(self):
        self.keys = self._load_keys()
        self.current_index = 0
        self.model = os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)

    def _load_keys(self) -> list:
        keys = []
        index = 1
        while True:
            key = os.getenv(f"OPENROUTER_APIKEY_{index}")
            if not key:
                break
            keys.append(key)
            index += 1

        if not keys:
            single_key = os.getenv("OPENROUTER_APIKEY")
            if single_key:
                keys.append(single_key)

        return keys

    @property
    def name(self) -> str:
        return "openrouter"

    def is_available(self) -> bool:
        return bool(self.keys)

    def _next_key(self) -> str:
        key = self.keys[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.keys)
        return key

    def analyze(self, image_b64: str, mime_type: str, prompt: str) -> str:
        if not self.is_available():
            raise ProviderError("No OPENROUTER_APIKEY keys set in .env")

        last_error = None

        for _ in range(len(self.keys)):
            api_key = self._next_key()

            payload = {
                "model": self.model,
                "messages": [{
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_b64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }]
            }

            response = requests.post(
                OPENROUTER_API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=30
            )

            if response.status_code == 429:
                last_error = RateLimitError(f"OpenRouter key #{self.current_index} rate limited, rotating...")
                continue

            if response.status_code != 200:
                raise ProviderError(f"OpenRouter error {response.status_code}: {response.text}")

            data = response.json()
            return data["choices"][0]["message"]["content"]

        raise last_error or RateLimitError("All OpenRouter keys rate limited")
