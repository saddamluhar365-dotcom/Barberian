"""Versioned skill metadata and execution boundaries."""

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(slots=True, frozen=True)
class Skill:
    name: str
    version: str
    description: str = ""
    capabilities: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    tests: tuple[str, ...] = ()


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}
        self._runners: dict[str, Callable[..., Any]] = {}

    def register(self, skill: Skill, runner: Callable[..., Any] | None = None) -> None:
        self._skills[skill.name.strip().lower()] = skill
        if runner:
            self._runners[skill.name.strip().lower()] = runner

    def get(self, name: str) -> Skill | None:
        return self._skills.get(name.strip().lower())

    def list(self) -> list[Skill]:
        return [self._skills[key] for key in sorted(self._skills)]

    def run(self, name: str, *args, **kwargs) -> Any:
        runner = self._runners.get(name.strip().lower())
        if runner is None:
            raise KeyError(f"skill runner not found: {name}")
        return runner(*args, **kwargs)
