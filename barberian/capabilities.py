"""Capability registry independent of provider implementation details."""

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class Capability:
    name: str
    description: str
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()


DEFAULT_CAPABILITIES = (
    Capability("llm", "Text reasoning and generation"),
    Capability("vision", "Image understanding"),
    Capability("search", "Web search"),
    Capability("web_extract", "Fetch and extract web content"),
    Capability("research", "Multi-source research and synthesis"),
    Capability("image", "Image generation and transformation"),
    Capability("video", "Video generation and rendering"),
    Capability("audio", "Audio and speech generation"),
    Capability("ocr", "Optical character recognition"),
    Capability("translation", "Language translation"),
    Capability("embeddings", "Embedding and semantic retrieval"),
    Capability("code", "Code generation and execution"),
    Capability("github", "Repository and development workflows"),
    Capability("files", "Artifact and file operations"),
    Capability("automation", "Scheduled and recurring execution"),
)


class CapabilityRegistry:
    def __init__(self, capabilities=DEFAULT_CAPABILITIES) -> None:
        self._items = {item.name: item for item in capabilities}

    def get(self, name: str) -> Capability | None:
        return self._items.get(name.strip().lower())

    def list(self) -> list[Capability]:
        return [self._items[key] for key in sorted(self._items)]
