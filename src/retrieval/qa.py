from __future__ import annotations

from dataclasses import dataclass
import re

from core.config import Settings
from core.utils import first_sentence, normalize_whitespace
from retrieval.index import LocalEmbeddingIndex, SearchResult


@dataclass(frozen=True)
class AnswerResult:
    question: str
    answer: str
    retrieved_doc_ids: list[str]
    retrieved_contexts: list[str]
    retrieved_titles: list[str]


_DOI_PATTERN = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", re.IGNORECASE)


def _value_or_unknown(value: str) -> str:
    cleaned = normalize_whitespace(value)
    return cleaned or "I don't know from the indexed corpus."


def _extract_exact_match(question: str, index: LocalEmbeddingIndex) -> dict | None:
    title_match = re.search(r"'([^']+)'", question)
    if title_match:
        exact = index.lookup(title_match.group(1))
        if exact:
            return exact

    doi_match = _DOI_PATTERN.search(question)
    if not doi_match:
        return None
    return index.lookup(doi_match.group(0).rstrip(".,;:!?"))


def _extract_answer(question: str, top_result: SearchResult) -> str:
    lowered = question.lower()
    metadata = top_result.metadata
    if "who authored" in lowered or "list the authors" in lowered:
        return _value_or_unknown(str(metadata.get("authors_joined", "")))
    if "when was" in lowered or "publication date" in lowered or "published on" in lowered:
        return _value_or_unknown(str(metadata.get("published", "")))
    if "what categories" in lowered:
        return _value_or_unknown(str(metadata.get("categories_joined", "")))
    return _value_or_unknown(first_sentence(str(metadata.get("summary", ""))))


def answer_question(question: str, settings: Settings, index: LocalEmbeddingIndex, top_k: int | None = None) -> AnswerResult:
    exact = _extract_exact_match(question, index)
    retrieved = index.search(question, top_k=top_k)
    if exact:
        exact_result = SearchResult(
            paper_id=exact["paper_id"],
            title=exact["title"],
            score=1.0,
            content=exact["content"],
            metadata=exact["metadata"],
        )
        deduped = [exact_result] + [item for item in retrieved if item.paper_id != exact_result.paper_id]
        retrieved = deduped[: (top_k or settings.top_k)]
    if not retrieved:
        answer = "I don't know from the indexed corpus."
    else:
        answer = _extract_answer(question, retrieved[0])
    return AnswerResult(
        question=question,
        answer=answer,
        retrieved_doc_ids=[item.paper_id for item in retrieved],
        retrieved_contexts=[item.content for item in retrieved],
        retrieved_titles=[item.title for item in retrieved],
    )
