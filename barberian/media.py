"""Media pipeline contracts and FFmpeg-friendly job manifests."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class MediaJob:
    id: str
    kind: str
    input_artifacts: list[str] = field(default_factory=list)
    output_artifact: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"


class MediaPipeline:
    def validate_video(self, metadata: dict[str, Any]) -> tuple[bool, list[str]]:
        errors: list[str] = []
        for field_name in ("duration_ms", "width", "height"):
            if metadata.get(field_name, 0) <= 0:
                errors.append(f"invalid {field_name}")
        if metadata.get("audio_sync_ms", 0) > 100:
            errors.append("audio/video sync exceeds tolerance")
        return not errors, errors

    def quality_gate(self, score: float, threshold: float = 0.75) -> bool:
        return float(score) >= threshold
