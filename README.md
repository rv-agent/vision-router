# Vision Router

Multi-provider image analysis with auto-fallback and key rotation.

## Agent Instructions

When you (the agent) need to analyze an image/screenshot:

1. **CLI:** `vision analyze <image_path> "<prompt>"`
2. **Python:** `analyze_image(path, prompt)`
3. **Check result:** `result["success"]`, `result["provider"]`, `result["result"]`
4. **Required:** Delete the image file after analysis with `os.remove(path)`.
   - Exception: only if the user explicitly asks to keep the file.

## Install

```bash
git clone <url> && cd vision-router
chmod +x install.sh && ./install.sh
# Or: pip install -r requirements.txt && pip install -e .
```

## CLI

```bash
vision analyze screenshot.png "Describe this image"
```

## Python

```python
from vision import analyze_image

result = analyze_image("screenshot.png", "what do you see?")
if result["success"]:
    text = result["result"]      # analysis text
    provider = result["provider"] # "gemini" or "openrouter"
else:
    error = result["error"]

os.remove("screenshot.png")  # REQUIRED cleanup
```

## Web UI (for settings)

```bash
vision serve
# Open http://localhost:5050 → Settings → paste keys → Save
```

## Output Format

```json
{
  "success": true,
  "provider": "gemini",
  "result": "The image shows...",
  "error": null
}
```

## Behavior

- **Auto-fallback:** Tries all Gemini keys → if exhausted → tries OpenRouter → if all exhausted → error
- **Multi-key rotation:** Round-robin through all keys per provider
- **Image compression:** Auto-resized to max 1024×1024 before sending (token efficient)

## Config

All via `.env` in project root. Can be edited via Web UI Settings tab.
