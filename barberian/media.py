"""Media production contracts, FFmpeg manifests and deterministic QC gates."""

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
        if metadata.get("fps", 0) <= 0:
            errors.append("invalid fps")
        if metadata.get("codec") == "":
            errors.append("missing codec")
        return not errors, errors

    def quality_gate(self, score: float, threshold: float = 0.75) -> bool:
        return 0.0 <= float(score) and float(score) >= threshold

    def build_video_manifest(self, inputs: list[str], *, fps: int = 30, width: int = 1920, height: int = 1080, output: str = "final.mp4") -> dict[str, Any]:
        if not inputs:
            raise ValueError("at least one input clip is required")
        if fps <= 0 or width <= 0 or height <= 0:
            raise ValueError("video dimensions and fps must be positive")
        return {
            "inputs": list(inputs),
            "fps": int(fps),
            "width": int(width),
            "height": int(height),
            "output": output,
            "codec": "libx264",
            "audio_codec": "aac",
            "pix_fmt": "yuv420p",
            "qc": {"require_audio_sync_ms": 100, "min_quality_score": 0.75, "reject_blank_frames": True, "reject_corrupt_media": True},
        }

    def ffmpeg_concat_command(self, manifest: dict[str, Any]) -> list[str]:
        inputs = manifest.get("inputs", [])
        if not inputs:
            raise ValueError("manifest contains no inputs")
        command = ["ffmpeg", "-y"]
        for item in inputs:
            command.extend(["-i", item])
        filters = "".join(f"[{i}:v:0][{i}:a:0]" for i in range(len(inputs))) + f"concat=n={len(inputs)}:v=1:a=1[v][a]"
        command.extend(["-filter_complex", filters, "-map", "[v]", "-map", "[a]", "-r", str(manifest.get("fps", 30)), "-c:v", manifest.get("codec", "libx264"), "-c:a", manifest.get("audio_codec", "aac"), "-pix_fmt", manifest.get("pix_fmt", "yuv420p"), manifest.get("output", "final.mp4")])
        return command
