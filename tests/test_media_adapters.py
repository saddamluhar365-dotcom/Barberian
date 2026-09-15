from barberian.media_adapters import ElevenLabsAdapter, ReplicateAdapter, RunwayAdapter


def test_replicate_prediction_payload():
    adapter = ReplicateAdapter("x", model="owner/model")
    payload = adapter.build_payload({"prompt": "a cat"})
    assert payload["version"] == "owner/model"
    assert payload["input"]["prompt"] == "a cat"


def test_runway_generation_payload():
    adapter = RunwayAdapter("x", model="gen3")
    payload = adapter.build_payload({"prompt": "a cinematic shot"})
    assert payload["promptText"] == "a cinematic shot"


def test_elevenlabs_payload():
    adapter = ElevenLabsAdapter("x", voice_id="voice")
    payload = adapter.build_payload({"text": "hello"})
    assert payload["text"] == "hello"
