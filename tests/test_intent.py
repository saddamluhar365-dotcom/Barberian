from barberian.intent import infer_capability


def test_intent_infers_major_capabilities():
    assert infer_capability("research latest AI news") == "research"
    assert infer_capability("generate an image of a mountain") == "image"
    assert infer_capability("write Python code") == "code"
    assert infer_capability("make a video") == "video"
