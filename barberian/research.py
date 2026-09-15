"""Multi-source research orchestration with deduplication and source scoring."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Callable, Iterable


@dataclass(slots=True, frozen=True)
class ResearchSource:
    url: str
    title: str = ""
    excerpt: str = ""
    quality: float = 0.0


@dataclass(slots=True)
class ResearchResult:
    question: str
    queries: list[str] = field(default_factory=list)
    sources: list[ResearchSource] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)


class ResearchEngine:
    def __init__(self, search: Callable[[str], Iterable[ResearchSource]] | None = None, max_workers: int = 4) -> None:
        self.search = search
        self.max_workers = max(1, int(max_workers))

    def plan(self, question: str) -> list[str]:
        text = question.strip()
        if not text:
            raise ValueError("research question is required")
        return [text, f"{text} evidence", f"{text} primary source"]

    def run(self, question: str) -> ResearchResult:
        queries = self.plan(question)
        sources: list[ResearchSource] = []
        if self.search:
            with ThreadPoolExecutor(max_workers=min(self.max_workers, len(queries))) as pool:
                futures = [pool.submit(self.search, query) for query in queries]
                for future in as_completed(futures):
                    sources.extend(future.result())
        by_url: dict[str, ResearchSource] = {}
        for source in sources:
            current = by_url.get(source.url)
            if current is None or source.quality > current.quality:
                by_url[source.url] = source
        ordered = sorted(by_url.values(), key=lambda item: (-item.quality, item.url))
        findings = [source.excerpt or source.title for source in ordered if source.excerpt or source.title]
        return ResearchResult(question=question.strip(), queries=queries, sources=ordered, findings=findings)
