"""
Rule-based extraction of `experience_level` and `tech_stack` from a
job's title and description. Runs once per job at ingestion time (see
job_ingestion_service.py) -- not at query/filter time -- so filtering
is just a plain column lookup, no text scanning on every search.

This is deliberately rule-based (keyword matching), not LLM-based --
see the taxonomy module's docstring for the reasoning and the known
precision/recall tradeoffs. If this ever proves too lossy in practice,
the upgrade path is swapping this module's internals for an LLM call
without touching its callers -- both functions' signatures would stay
the same.
"""

import re
from functools import lru_cache

from app.core.tech_taxonomy import CASE_SENSITIVE_TERMS, EXPERIENCE_LEVEL_PATTERNS, TECH_TAXONOMY
from app.utils.html_text import strip_html


def _build_boundary_pattern(term: str) -> str:
    """
    Build a regex fragment for `term` that only matches when no
    alphanumeric character is immediately adjacent on either side.

    This is deliberately NOT `\\b` (word boundary): `\\b` behaves oddly
    around terms containing symbols (e.g. "C++", "C#", ".NET") because
    a symbol is already a non-word character, so a plain `\\b` boundary
    exists right next to it regardless of what follows. Using explicit
    lookaround for "no alphanumeric adjacent" gives consistent behavior
    for both plain-word terms (Python, React) and symbol-containing
    ones (C++, C#) alike.
    """
    escaped = re.escape(term)
    return rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])"


@lru_cache(maxsize=1)
def _compiled_tech_patterns() -> list[tuple[str, re.Pattern]]:
    """
    Build (canonical_name, compiled_pattern) pairs once and cache them --
    compiling ~80 regexes per job during ingestion would be wasteful
    when the taxonomy itself never changes at runtime. `lru_cache` with
    no arguments (aside from the implicit none here) makes this
    effectively a lazy singleton: compiled on first use, reused for
    every subsequent job in the batch and across all future calls in
    this process.
    """
    compiled: list[tuple[str, re.Pattern]] = []

    for canonical, aliases in TECH_TAXONOMY.items():
        all_terms = [canonical, *aliases]
        fragments = [_build_boundary_pattern(term) for term in all_terms]
        combined_pattern = "|".join(fragments)

        flags = 0 if canonical in CASE_SENSITIVE_TERMS else re.IGNORECASE
        compiled.append((canonical, re.compile(combined_pattern, flags)))

    return compiled


def extract_tech_stack(title: str, description_html: str | None) -> list[str]:
    """
    Return the sorted list of canonical tech-stack tags found in the
    job's title and description. Deduplicated by construction (each
    canonical tag is checked once); sorted alphabetically so storage
    and API responses are deterministic rather than depending on
    taxonomy dict ordering.
    """
    description_text = strip_html(description_html)
    combined_text = f"{title}\n{description_text}"

    matched: set[str] = set()
    for canonical, pattern in _compiled_tech_patterns():
        if pattern.search(combined_text):
            matched.add(canonical)

    return sorted(matched)


def extract_experience_level(title: str) -> str | None:
    """
    Return the single best-matching experience-level bucket for a job
    title, or None if the title has no explicit level signal.

    Checked in the priority order defined by EXPERIENCE_LEVEL_PATTERNS
    (most senior/specific first) -- on the rare title that contains
    more than one signal (e.g. "Senior Engineering Manager"), the more
    senior/specific bucket wins rather than whichever happened to be
    checked first.
    """
    lowered_title = title.lower()

    for level, patterns in EXPERIENCE_LEVEL_PATTERNS.items():
        for pattern in patterns:
            boundary_pattern = _build_boundary_pattern(pattern)
            if re.search(boundary_pattern, lowered_title, re.IGNORECASE):
                return level

    return None
