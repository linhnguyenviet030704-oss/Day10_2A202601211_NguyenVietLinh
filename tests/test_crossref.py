from __future__ import annotations

from dataclasses import asdict, replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from core.config import load_settings
from ingestion.crossref import PaperRecord, fetch_source_records, load_raw_records, parse_crossref_payload


class FakeResponse:
    def __init__(self, payload: dict):
        self.status = 200
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class CrossrefTests(unittest.TestCase):
    def test_parse_crossref_payload_normalizes_record_schema(self) -> None:
        payload = {
            "message": {
                "items": [
                    {
                        "DOI": "10.1000/example",
                        "title": ["  Agentic   RAG for  Papers  "],
                        "abstract": "<jats:p>Study of <b>RAG</b> systems.</jats:p>",
                        "author": [
                            {"given": "Ada", "family": "Lovelace"},
                            {"name": "Research Group"},
                        ],
                        "subject": ["Artificial Intelligence", "Information Retrieval"],
                        "published": {"date-parts": [[2026, 2, 3]]},
                        "indexed": {"date-time": "2026-02-04T05:06:07Z"},
                        "URL": "https://doi.org/10.1000/example",
                        "link": [{"content-type": "application/pdf", "URL": "https://example.org/paper.pdf"}],
                        "container-title": ["Journal of Useful Results"],
                    },
                    {
                        "title": ["missing doi should be skipped"],
                    },
                ]
            }
        }

        records = parse_crossref_payload(payload)

        self.assertEqual(len(records), 1)
        self.assertEqual(
            records[0],
            PaperRecord(
                paper_id="10.1000/example",
                title="Agentic RAG for Papers",
                summary="Study of RAG systems.",
                authors=["Ada Lovelace", "Research Group"],
                categories=["Artificial Intelligence", "Information Retrieval"],
                primary_category="Artificial Intelligence",
                published="2026-02-03",
                updated="2026-02-04T05:06:07Z",
                abs_url="https://doi.org/10.1000/example",
                pdf_url="https://example.org/paper.pdf",
                comment="Journal of Useful Results",
            ),
        )

    def test_fetch_source_records_saves_raw_response_and_parsed_records(self) -> None:
        payload = {
            "message": {
                "items": [
                    {
                        "DOI": "10.1000/fetch",
                        "title": ["Fetch me"],
                        "abstract": "<jats:p>Saved to disk.</jats:p>",
                        "author": [{"given": "Lin", "family": "Nguyen"}],
                        "subject": ["Data Engineering"],
                        "published-print": {"date-parts": [[2026, 1, 15]]},
                        "deposited": {"date-time": "2026-01-16T00:00:00Z"},
                        "URL": "https://doi.org/10.1000/fetch",
                    }
                ]
            }
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            settings = load_settings()
            patched_paths = replace(
                settings.paths,
                raw_api_response=root / "data" / "raw" / "crossref_response.json",
                raw_records_json=root / "data" / "raw" / "crossref_records.json",
            )
            patched_settings = replace(settings, paths=patched_paths)

            with patch("ingestion.crossref.urlopen", return_value=FakeResponse(payload)) as mock_get:
                records = fetch_source_records(patched_settings)

            self.assertEqual(mock_get.call_count, 1)
            self.assertEqual(len(records), 1)
            self.assertTrue(patched_settings.paths.raw_api_response.exists())
            self.assertTrue(patched_settings.paths.raw_records_json.exists())
            round_trip = load_raw_records(patched_settings.paths.raw_records_json)
            self.assertEqual(round_trip, records)

    def test_load_raw_records_maps_json_back_to_dataclass(self) -> None:
        record = PaperRecord(
            paper_id="10.1000/load",
            title="Load Test",
            summary="Load from JSON.",
            authors=["Test Author"],
            categories=["Testing"],
            primary_category="Testing",
            published="2026-03-01",
            updated="2026-03-02T00:00:00Z",
            abs_url="https://doi.org/10.1000/load",
            pdf_url="",
            comment="Unit Tests",
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "records.json"
            path.write_text(json.dumps([asdict(record)]), encoding="utf-8")

            loaded = load_raw_records(path)

        self.assertEqual(loaded, [record])


if __name__ == "__main__":
    unittest.main()
