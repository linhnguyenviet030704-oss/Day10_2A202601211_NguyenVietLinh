from __future__ import annotations

from dataclasses import asdict, dataclass
from html import unescape
import json
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json


CROSSREF_API_URL = "https://api.crossref.org/works"


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _pick_first_text(value: object) -> str:
    if isinstance(value, list):
        for item in value:
            text = normalize_whitespace(str(item))
            if text:
                return text
        return ""
    if value is None:
        return ""
    return normalize_whitespace(str(value))


def _strip_markup(text: str) -> str:
    if not text:
        return ""
    without_tags = re.sub(r"<[^>]+>", " ", text)
    return normalize_whitespace(unescape(without_tags))


def _extract_authors(item: dict) -> list[str]:
    authors: list[str] = []
    for author in item.get("author", []):
        if not isinstance(author, dict):
            continue
        name = normalize_whitespace(
            " ".join(part for part in [author.get("given", ""), author.get("family", "")] if part)
        )
        if not name:
            name = _pick_first_text(author.get("name"))
        if name and name not in authors:
            authors.append(name)
    return authors


def _extract_categories(item: dict) -> list[str]:
    categories: list[str] = []
    for category in item.get("subject", []):
        name = normalize_whitespace(str(category))
        if name and name not in categories:
            categories.append(name)
    return categories


def _date_parts_to_iso(value: dict | None) -> str:
    if not isinstance(value, dict):
        return ""
    date_parts = value.get("date-parts")
    if not isinstance(date_parts, list) or not date_parts:
        return ""
    first = date_parts[0]
    if not isinstance(first, list) or not first:
        return ""
    parts = [str(int(part)) for part in first[:3] if isinstance(part, int)]
    if not parts:
        return ""
    if len(parts) >= 1:
        parts[0] = parts[0].zfill(4)
    if len(parts) >= 2:
        parts[1] = parts[1].zfill(2)
    if len(parts) >= 3:
        parts[2] = parts[2].zfill(2)
    return "-".join(parts)


def _extract_published(item: dict) -> str:
    for key in ("published-print", "published-online", "published", "issued", "created"):
        published = _date_parts_to_iso(item.get(key))
        if published:
            return published
    return ""


def _extract_updated(item: dict) -> str:
    for key in ("indexed", "deposited", "created", "issued"):
        value = item.get(key)
        if not isinstance(value, dict):
            continue
        date_time = _pick_first_text(value.get("date-time"))
        if date_time:
            return date_time
        date_value = _date_parts_to_iso(value)
        if date_value:
            return date_value
    return ""


def _extract_pdf_url(item: dict) -> str:
    for link in item.get("link", []):
        if not isinstance(link, dict):
            continue
        content_type = normalize_whitespace(str(link.get("content-type", ""))).lower()
        if content_type == "application/pdf":
            return _pick_first_text(link.get("URL"))
    return ""


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    items = payload.get("message", {}).get("items", [])
    if not isinstance(items, list):
        return []

    records: list[PaperRecord] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        paper_id = _pick_first_text(item.get("DOI"))
        title = _pick_first_text(item.get("title"))
        if not paper_id or not title:
            continue

        categories = _extract_categories(item)
        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=_strip_markup(_pick_first_text(item.get("abstract"))),
                authors=_extract_authors(item),
                categories=categories,
                primary_category=categories[0] if categories else "",
                published=_extract_published(item),
                updated=_extract_updated(item),
                abs_url=_pick_first_text(item.get("URL")),
                pdf_url=_extract_pdf_url(item),
                comment=_pick_first_text(item.get("container-title")) or _pick_first_text(item.get("publisher")),
            )
        )
    return records


def _build_request(settings: Settings) -> Request:
    query = urlencode(
        {
            "query": settings.source_query,
            "filter": settings.source_filter,
            "rows": settings.max_results,
        }
    )
    return Request(
        f"{CROSSREF_API_URL}?{query}",
        headers={
            "Accept": "application/json",
            "User-Agent": "day10-data-observability-lab/0.1",
        },
    )


def _fetch_payload(settings: Settings, retries: int = 3) -> dict:
    request = _build_request(settings)
    for attempt in range(retries):
        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code not in {429, 503} or attempt == retries - 1:
                raise
            time.sleep(attempt + 1)
        except URLError:
            if attempt == retries - 1:
                raise
            time.sleep(attempt + 1)
    raise RuntimeError("Crossref fetch failed after retries.")


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    payload = _fetch_payload(settings)
    write_json(settings.paths.raw_api_response, payload)
    records = parse_crossref_payload(payload)
    write_json(settings.paths.raw_records_json, [asdict(record) for record in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    return [PaperRecord(**item) for item in read_json(path)]
