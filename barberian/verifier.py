"""Output verification gates."""

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(slots=True, frozen=True)
class Verification:
    passed: bool
    checks: dict[str, bool]
    issues: list[str]


class Verifier:
    def verify(self, output: Any, checks: dict[str, Callable[[Any], bool]] | None = None) -> Verification:
        checks = checks or {"not_none": lambda value: value is not None}
        results: dict[str, bool] = {}
        issues: list[str] = []
        for name, check in checks.items():
            try:
                results[name] = bool(check(output))
            except Exception as exc:
                results[name] = False
                issues.append(f"{name}: {exc}")
            if not results[name] and name not in issues:
                issues.append(name)
        return Verification(passed=all(results.values()), checks=results, issues=issues)
