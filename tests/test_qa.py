from __future__ import annotations

import unittest

from core.config import load_settings
from retrieval.index import SearchResult
from retrieval.qa import answer_question


class FakeIndex:
    def __init__(self) -> None:
        self.records = {
            "10.70121/001c.158711": {
                "paper_id": "10.70121/001c.158711",
                "title": "Medical RAG Paper",
                "content": "Title: Medical RAG Paper\nSummary: Correct first sentence. Second sentence.",
                "metadata": {
                    "paper_id": "10.70121/001c.158711",
                    "title": "Medical RAG Paper",
                    "published": "2026-03-15",
                    "authors_joined": "Eason Ni",
                    "categories_joined": "",
                    "summary": "Correct first sentence. Second sentence.",
                    "abs_url": "",
                    "pdf_url": "",
                },
            },
            "wrong-paper": {
                "paper_id": "wrong-paper",
                "title": "Wrong Paper",
                "content": "Title: Wrong Paper\nSummary: Wrong sentence.",
                "metadata": {
                    "paper_id": "wrong-paper",
                    "title": "Wrong Paper",
                    "published": "2026-01-01",
                    "authors_joined": "Wrong Author",
                    "categories_joined": "Wrong Category",
                    "summary": "Wrong sentence.",
                    "abs_url": "",
                    "pdf_url": "",
                },
            },
        }

    def lookup(self, value: str):
        needle = value.strip().lower()
        for record in self.records.values():
            if needle in {record["paper_id"].lower(), record["title"].lower()}:
                return record
        return None

    def search(self, query: str, top_k: int | None = None):
        return [
            SearchResult(
                paper_id="wrong-paper",
                title="Wrong Paper",
                score=0.9,
                content=self.records["wrong-paper"]["content"],
                metadata=self.records["wrong-paper"]["metadata"],
            ),
            SearchResult(
                paper_id="10.70121/001c.158711",
                title="Medical RAG Paper",
                score=0.8,
                content=self.records["10.70121/001c.158711"]["content"],
                metadata=self.records["10.70121/001c.158711"]["metadata"],
            ),
        ]


class QATests(unittest.TestCase):
    def test_answer_question_prefers_exact_paper_id_lookup(self) -> None:
        settings = load_settings()
        index = FakeIndex()

        result = answer_question(
            "Look up paper_id 10.70121/001c.158711 and summarize it in one sentence.",
            settings=settings,
            index=index,
        )

        self.assertEqual(result.answer, "Correct first sentence.")
        self.assertEqual(result.retrieved_doc_ids[0], "10.70121/001c.158711")

    def test_answer_question_returns_unknown_for_missing_categories(self) -> None:
        settings = load_settings()
        index = FakeIndex()

        result = answer_question(
            "What categories does the paper 'Medical RAG Paper' belong to?",
            settings=settings,
            index=index,
        )

        self.assertEqual(result.answer, "I don't know from the indexed corpus.")


if __name__ == "__main__":
    unittest.main()
