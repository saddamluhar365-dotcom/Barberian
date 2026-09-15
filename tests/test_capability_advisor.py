from barberian.capabilities import CapabilityRegistry
from barberian.capability_advisor import CapabilityAdvisor


def test_capability_advisor_reports_missing_capability_and_catalog_suggestions():
    registry = CapabilityRegistry()
    advisor = CapabilityAdvisor(registry)
    result = advisor.assess(["llm", "video", "unknown"])
    assert "video" in result.missing
    assert "unknown" in result.unknown
    assert result.suggestions["video"]
