"""Lightweight intent-to-capability routing before provider selection."""

RULES = (
    ("research", ("research", "deep research", "investigate", "sources", "fact check")),
    ("search", ("search", "find online", "look up", "latest news")),
    ("image", ("generate image", "create image", "draw", "picture", "image")),
    ("video", ("generate video", "create video", "make a video", "video")),
    ("audio", ("tts", "text to speech", "voice", "audio", "sound")),
    ("code", ("code", "program", "debug", "python", "javascript", "typescript")),
    ("github", ("github", "pull request", "commit", "repository", "repo")),
    ("files", ("file", "document", "artifact", "upload", "download")),
    ("automation", ("schedule", "automate", "recurring", "every day", "every hour")),
)


def infer_capability(text: str) -> str:
    lowered = text.strip().lower()
    for capability, phrases in RULES:
        if any(phrase in lowered for phrase in phrases):
            return capability
    return "llm"
