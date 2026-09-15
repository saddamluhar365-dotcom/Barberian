from barberian.drive import folder_plan


def test_drive_folder_plan_contains_required_artifact_layers():
    folders = folder_plan()
    assert "AI AGENT/Videos/Raw" in folders
    assert "AI AGENT/Videos/Final" in folders
    assert "AI AGENT/Artifacts" in folders
