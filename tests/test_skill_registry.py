from barberian.skills import Skill, SkillRegistry


def test_skill_registry_keeps_versioned_metadata_and_permissions():
    registry = SkillRegistry()
    skill = Skill("research", "1.0.0", capabilities=("search",), permissions=("web.read",))
    registry.register(skill)
    assert registry.get("research").version == "1.0.0"
    assert registry.get("research").permissions == ("web.read",)
