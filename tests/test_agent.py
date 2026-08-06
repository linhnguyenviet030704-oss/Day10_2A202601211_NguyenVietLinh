from __future__ import annotations

import unittest

from core.config import load_settings
from retrieval.agent import run_agent_question
from retrieval.index import SearchResult


class FakeIndex:
    def __init__(self) -> None:
        self.record = {
            "paper_id": "paper-1",
            "title": "Paper One",
            "content": "Title: Paper One\nSummary: First sentence. Second sentence.",
            "metadata": {
                "paper_id": "paper-1",
                "title": "Paper One",
                "published": "2026-08-01",
                "authors_joined": "Ada Lovelace",
                "categories_joined": "AI",
                "summary": "First sentence. Second sentence.",
                "abs_url": "",
                "pdf_url": "",
            },
        }

    def lookup(self, value: str):
        if value.strip().lower() in {"paper one", "paper-1"}:
            return self.record
        return None

    def search(self, query: str, top_k: int | None = None):
        return [
            SearchResult(
                paper_id="paper-1",
                title="Paper One",
                score=1.0,
                content=self.record["content"],
                metadata=self.record["metadata"],
            )
        ]


class FakeAgent:
    def __init__(self, settings, index) -> None:
        self._fallback_settings = settings
        self._fallback_index = index

    def invoke(self, payload):
        raise RuntimeError("simulated llm failure")


class AgentTests(unittest.TestCase):
    def test_run_agent_question_falls_back_to_local_qa_when_agent_invoke_fails(self) -> None:
        settings = load_settings()
        index = FakeIndex()
        agent = FakeAgent(settings, index)

        answer = run_agent_question(agent, "Who authored the paper 'Paper One'?")

        self.assertEqual(answer, "Ada Lovelace")


if __name__ == "__main__":
    unittest.main()
