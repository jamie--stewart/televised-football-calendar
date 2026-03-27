import re
from dataclasses import dataclass, field


@dataclass
class ParsedQuery:
    must_include: list[str] = field(default_factory=list)
    must_exclude: list[str] = field(default_factory=list)
    exact_phrases: list[str] = field(default_factory=list)
    optional_terms: list[str] = field(default_factory=list)

    def to_upstream_query(self) -> str:
        parts = self.must_include + self.exact_phrases
        if not parts:
            parts = self.optional_terms
        return " ".join(parts)

    @property
    def is_empty(self) -> bool:
        return not (self.must_include or self.must_exclude or self.exact_phrases or self.optional_terms)


_TOKEN_RE = re.compile(
    r'"([^"]*)"'  # "quoted phrase"
    r"|(\+\S+)"  # +must_include
    r"|(-\S+)"  # -must_exclude
    r"|(\S+)"  # bare word
)


def parse_query(raw: str) -> ParsedQuery:
    query = ParsedQuery()
    for match in _TOKEN_RE.finditer(raw):
        phrase, plus, minus, bare = match.groups()
        if phrase is not None:
            query.exact_phrases.append(phrase)
        elif plus is not None:
            query.must_include.append(plus[1:])
        elif minus is not None:
            query.must_exclude.append(minus[1:])
        elif bare is not None:
            query.optional_terms.append(bare)
    return query


def filter_results(results: list[dict], query: ParsedQuery) -> list[dict]:
    filtered = []
    for result in results:
        title = result.get("title", "").lower()

        if any(term.lower() not in title for term in query.must_include):
            continue

        if any(term.lower() in title for term in query.must_exclude):
            continue

        if any(phrase.lower() not in title for phrase in query.exact_phrases):
            continue

        filtered.append(result)

    if query.optional_terms:
        filtered.sort(
            key=lambda r: sum(1 for t in query.optional_terms if t.lower() in r.get("title", "").lower()),
            reverse=True,
        )

    return filtered
