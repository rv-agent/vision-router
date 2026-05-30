# vision-router

## Description
Image analysis via Google AI Studio (Gemini) + OpenRouter with auto-fallback and multi-key rotation.

## When to load this skill
- User asks to analyze an image/screenshot
- User asks "what's in this image" or "describe this picture"
- Agent needs to extract text from an image
- Agent needs to understand a UI screenshot, diagram, or chart

## Installation (one-time)
```bash
cd /path/to/vision-router && pip install -e .
```
Config via Web UI: `vision serve` → http://localhost:5050 → Settings

## Usage

### CLI
```bash
vision analyze <image_path> "<prompt>"
```

### Python
```python
from vision import analyze_image

result = analyze_image(image_path, prompt)
if result["success"]:
    text = result["result"]      # string
    provider = result["provider"] # "gemini" or "openrouter"
```

## Cleanup Rule (REQUIRED)
- **Delete the image file immediately after analyzing.**
- `os.remove(image_path)` right after getting the result.
- Exception: only if user explicitly asks to keep the file.

```python
result = analyze_image("screenshot.png", "describe")
os.remove("screenshot.png")  # DO NOT SKIP
```

## When NOT to use
- Content is already text → process directly, skip vision
- DOM/HTML extractable via CDP → use CDP, cheaper
- PDF with extractable text → use pdfplumber first

## Notes
- Auto-compresses images to 1024×1024 (saves tokens)
- Gemini: `gemini-3.1-flash-lite` (default, cheapest)
- OpenRouter: `openrouter/free` (auto-picks free vision model)
- 35 API keys total (15 Gemini + 20 OpenRouter), auto round-robin
- Fallback order set in .env or Web UI Settings
