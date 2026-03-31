from math import log

from ..mock_data import get_cases, get_knowledge_docs


def _tokenize(text: str) -> list[str]:
    normalized = (
        text.lower()
        .replace("，", " ")
        .replace("。", " ")
        .replace("、", " ")
        .replace(":", " ")
        .replace("/", " ")
        .replace("-", " ")
    )
    return [token for token in normalized.split() if token]


def _score(query_tokens: list[str], document: str) -> float:
    doc_tokens = _tokenize(document)
    if not doc_tokens or not query_tokens:
        return 0.0
    token_counts = {token: doc_tokens.count(token) for token in set(doc_tokens)}
    score = 0.0
    for token in query_tokens:
        if token in token_counts:
            score += 1.0 + log(1 + token_counts[token])
    return round(score, 3)


def retrieve_context(query: str, limit: int = 2) -> dict[str, list[dict[str, str | float]]]:
    query_tokens = _tokenize(query)

    knowledge_hits = []
    for doc in get_knowledge_docs():
        score = _score(query_tokens, f"{doc['name']} {doc['content']}")
        knowledge_hits.append(
            {
                "source": "knowledge",
                "title": doc["name"],
                "score": score,
                "snippet": doc["content"][:160],
            }
        )

    case_hits = []
    for case in get_cases():
        haystack = f"{case['title']} {case['reason']} {' '.join(case['actions'])} {case['retrospective']}"
        score = _score(query_tokens, haystack)
        case_hits.append(
            {
                "source": "case",
                "title": case["title"],
                "score": score,
                "snippet": case["retrospective"],
            }
        )

    knowledge_hits.sort(key=lambda item: item["score"], reverse=True)
    case_hits.sort(key=lambda item: item["score"], reverse=True)
    return {
        "knowledge": knowledge_hits[:limit],
        "cases": case_hits[:limit],
    }

