from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

from core.config import load_settings
from retrieval.index import LocalEmbeddingIndex


class FakeEmbeddings:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector_for(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector_for(text)

    @staticmethod
    def _vector_for(text: str) -> list[float]:
        lowered = text.lower()
        if "alpha" in lowered:
            return [1.0, 0.0]
        return [0.0, 1.0]


class IndexTests(unittest.TestCase):
    def test_build_and_load_index_persist_collection_and_top_k_search(self) -> None:
        df = pd.DataFrame(
            [
                {
                    "paper_id": "paper-1",
                    "title": "Alpha Paper",
                    "text_for_embedding": "alpha context",
                    "published": "2026-08-01",
                    "authors_joined": "Ada Lovelace",
                    "categories_joined": "AI",
                    "summary": "Alpha summary.",
                    "abs_url": "https://example.com/alpha",
                    "pdf_url": "https://example.com/alpha.pdf",
                },
                {
                    "paper_id": "paper-2",
                    "title": "Beta Paper",
                    "text_for_embedding": "beta context",
                    "published": "2026-07-15",
                    "authors_joined": "Grace Hopper",
                    "categories_joined": "Systems",
                    "summary": "Beta summary.",
                    "abs_url": "https://example.com/beta",
                    "pdf_url": "https://example.com/beta.pdf",
                },
            ]
        )

        base_settings = load_settings()
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
            tmp_path = Path(tmp_dir)
            manifest_path = tmp_path / "custom embeddings.json"
            settings = replace(
                base_settings,
                paths=replace(
                    base_settings.paths,
                    chroma_dir=tmp_path / "chroma",
                    embeddings_json=tmp_path / "papers_embeddings.json",
                ),
            )

            with patch("retrieval.index.MiniLMEmbeddings", FakeEmbeddings):
                built = LocalEmbeddingIndex.build(df, settings, embeddings_output_path=manifest_path)

                self.assertEqual(built.collection_name, "custom-embeddings")
                self.assertTrue(manifest_path.exists())

                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                self.assertEqual(manifest["embedding_model"], settings.embedding_model)
                self.assertEqual(manifest["collection_name"], "custom-embeddings")
                self.assertEqual(len(manifest["documents"]), 2)

                results = built.search("alpha question", top_k=1)
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0].paper_id, "paper-1")
                self.assertEqual(results[0].title, "Alpha Paper")
                self.assertGreaterEqual(results[0].score, 0.99)
                self.assertEqual(built.lookup("paper-2")["title"], "Beta Paper")
                self.assertEqual(built.lookup("Alpha Paper")["paper_id"], "paper-1")

                loaded = LocalEmbeddingIndex.load(settings, embeddings_path=manifest_path)
                loaded_results = loaded.search("beta question", top_k=2)
                self.assertEqual([item.paper_id for item in loaded_results], ["paper-2", "paper-1"])


if __name__ == "__main__":
    unittest.main()
