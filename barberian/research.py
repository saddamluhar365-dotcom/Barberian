"""Research orchestration contracts; concrete search/fetch adapters plug in here."""

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable


@dataclass(slots=True, frozen=True)
class ResearchSource:
    url: str
    title: str = ""
    excerpt: str = ""
    quality: float = 0.0


@dataclass(slots=True)
class ResearchResult:
    question: str
    sources: list[ResearchSource] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)


class ResearchEngine:
    def __init__(self, search: Callable[[str], Iterable[ResearchSource]] | None = None) -> None:
        self.search = search

    def plan(self, question: str) -> list[str]:
        text = question.strip()
        if not text:
            raise ValueError("research question is required")
        return [text]

    def run(self, question: str) -> ResearchResult:
        queries = self.plan(question)
        sources: list[ResearchSource] = []
        for query in queries:
            if self.search:
                sources.extend(self.search(query))
        deduped = {source.url: source for source in sources}
        return ResearchResult(question=question.strip(), sources=list(deduped.values()))
