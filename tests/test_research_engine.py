from barberian.research import ResearchEngine, ResearchSource


def test_research_engine_expands_queries_and_deduplicates_sources():
    def search(query):
        return [ResearchSource("https://a.example", title=query, quality=0.8), ResearchSource("https://b.example", quality=0.6)]

    engine = ResearchEngine(search=search)
    result = engine.run("history of tea")
    assert len(result.sources) == 2
    assert len(result.findings) >= 1


def test_research_plan_rejects_empty_question():
    try:
        ResearchEngine().plan(" ")
    except ValueError:
        return
    raise AssertionError("empty question must fail")
