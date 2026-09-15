from barberian.media import MediaPipeline


def test_video_manifest_contains_quality_controls():
    manifest = MediaPipeline().build_video_manifest(["a.mp4", "b.mp4"], fps=30, width=1920, height=1080)
    assert manifest["fps"] == 30
    assert manifest["inputs"] == ["a.mp4", "b.mp4"]
    assert manifest["qc"]["require_audio_sync_ms"] == 100


def test_bad_video_metadata_fails_validation():
    ok, errors = MediaPipeline().validate_video({"duration_ms": 0, "width": 1920, "height": 1080})
    assert not ok
    assert "invalid duration_ms" in errors
