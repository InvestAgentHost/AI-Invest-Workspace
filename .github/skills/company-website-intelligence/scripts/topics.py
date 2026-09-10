"""Single source of truth for the fixed information-topic taxonomy.

`discover_urls.py`, `fetch_page.py`, `assemble_report.py`, and
`validate_report.py` all import this module instead of re-declaring topic
ids/keywords/table schemas, so the taxonomy documented in
`references/topic-taxonomy.md` only needs to be kept in sync with one file.

All 8 topics are mandatory — there is no optional-topic concept. ESG &
Sustainability and Careers & Culture were dropped from the taxonomy entirely
(not just made optional) because they are out of scope for this skill's
intended use.

`keywords` here are a lightweight hint, not an enforced classifier: they
back `guess_topic()`, used by `discover_urls.py`/`fetch_page.py` to pre-label
a URL's most likely topic in `urls.json`/`pages.jsonl` so the Agent has a
starting point when picking what to read next. The Agent's own judgment when
reading a page's actual content is authoritative, not this guess.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Topic:
    id: str
    title: str
    # None => the topic is a prose section only; otherwise the shared table name
    # in TABLE_SCHEMAS that this topic's structured rows live in.
    table: str | None
    # Minimum number of "Key Facts" bullets (prose topics) or table rows
    # (table topics) for the topic to count as `covered` rather than `partial`.
    min_key_facts: int
    # Lowercase keyword hints used by classify_sections.py's rule-based
    # pre-filter. Not authoritative — the Agent reclassifies during Phase 5.
    keywords: tuple[str, ...] = field(default_factory=tuple)


TOPICS: tuple[Topic, ...] = (
    Topic(
        "products_and_segments", "Business Units & Products", "business_units", 4,
        ("products", "solutions", "services", "platform", "offerings", "segments", "division", "business unit", "department"),
    ),
    Topic(
        "company_overview", "Company Overview", None, 3,
        ("about us", "who we are", "our history", "founded", "headquartered", "mission", "our company"),
    ),
    Topic(
        "leadership_and_governance", "Leadership & Governance", "leadership", 3,
        ("board of directors", "executive team", "leadership", "management team", "ceo", "cfo", "chief executive", "governance"),
    ),
    Topic(
        "news_and_announcements", "News & Announcements", "timeline", 3,
        ("press release", "news", "newsroom", "announces", "announcement"),
    ),
    Topic(
        "strategy_partnerships_ma", "Strategy, Partnerships & M&A", "timeline", 2,
        ("partnership", "collaborat", "acquisition", "acquires", "merger", "joint venture", "strategic alliance"),
    ),
    Topic(
        "ir_documents_index", "Investor Relations Documents Index", "ir_documents", 3,
        ("investor relations", "annual report", "proxy statement", "earnings presentation", "sec filings", "shareholder"),
    ),
    Topic(
        "customers_and_case_studies", "Customers & Case Studies", None, 2,
        ("case study", "customer story", "our clients", "success story", "testimonial"),
    ),
    Topic(
        "contact_and_global_presence", "Contact & Global Presence", None, 2,
        ("contact us", "our offices", "locations", "headquarters", "global presence"),
    ),
)

TOPICS_BY_ID: dict[str, Topic] = {topic.id: topic for topic in TOPICS}

TABLE_SCHEMAS: dict[str, set[str]] = {
    "business_units": {"unit_name", "description", "key_products_or_services", "evidence_refs"},
    "leadership": {"name", "title", "role_type", "bio_summary", "evidence_refs"},
    "timeline": {"date", "category", "title", "summary", "evidence_refs"},
    "ir_documents": {"document_title", "document_type", "url", "evidence_refs"},
}

# Substring match (case-insensitive) against a URL to exclude it from
# discovery/fetch entirely — financial-report/filing pages belong to
# company-deep-investment-research's ten_k capability, not this skill.
EXCLUDED_PATH_KEYWORDS: tuple[str, ...] = (
    "10-k", "10k", "10-q", "10q", "8-k", "8k",
    "sec-filing", "sec-filings", "annual-report", "proxy-statement", "edgar",
    "financial-report", "financial-reports",
)


def is_excluded_path(url: str) -> bool:
    lowered = url.casefold()
    return any(keyword in lowered for keyword in EXCLUDED_PATH_KEYWORDS)


def guess_topic(haystack: str) -> str | None:
    """Best-effort topic label for a URL (optionally + a page title) —
    a starting hint for the Agent, not an authoritative classification."""

    lowered = haystack.casefold()
    best_id: str | None = None
    best_score = 0
    for topic in TOPICS:
        score = sum(lowered.count(keyword) for keyword in topic.keywords)
        if score > best_score:
            best_score = score
            best_id = topic.id
    return best_id
