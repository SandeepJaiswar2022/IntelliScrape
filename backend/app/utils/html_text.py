"""
HTML-to-plain-text helpers, built on BeautifulSoup.

Used in two places:
  1. app/services/job_extraction_service.py -- strips HTML before
     running tech-stack keyword matching, so we're matching against
     real words, not tag names or attribute values.
  2. app/api/v1/endpoints/jobs.py -- turns the stored raw
     `description_html` into safe, renderable plain text for API
     responses (both the short list-view preview and the full detail
     view), without ever needing to render raw HTML in the frontend.
     Deliberately not preserved: rich formatting (bold, links, bullet
     structure) from the original posting. This is a conscious MVP
     simplification -- it avoids needing an HTML sanitization library
     (e.g. DOMPurify) and dangerouslySetInnerHTML on the frontend
     entirely. Worth revisiting only if losing that formatting turns
     out to actually matter to users.

Computed at read time (API response building), not stored -- the
database keeps `description_html` as the single source of truth, and
plain text is a cheap derived view rather than duplicated, potentially
stale, stored data.
"""
from html import unescape
from bs4 import BeautifulSoup


def strip_html(html: str | None) -> str:
    """
    Convert HTML to whitespace-normalized plain text.
    Returns an empty string for None/empty input rather than raising --
    callers never need to special-case a missing description.
    """
    if not html:
        return ""

    # Convert &lt; &gt; &amp; &#39; into real characters
    html = unescape(html)

    soup = BeautifulSoup(html, "html.parser")

    # Insert an explicit newline after each BLOCK-level element's
    # content, before extracting text. This is deliberately narrower
    # than passing separator="\n" to get_text() directly -- that
    # naive approach inserts a newline between EVERY tag's text,
    # including inline ones like <b>/<strong>/<a>, which breaks
    # sentences like "We use <b>Python</b>, Django" into
    # "We use\nPython\n, Django" -- a real bug caught by testing
    # against an actual job description containing inline tags.
    # Only line-breaking at true block boundaries keeps inline
    # emphasis from fragmenting the surrounding sentence.
    block_tags = ["p", "div", "li", "br", "h1", "h2", "h3", "h4", "h5", "h6", "tr"]
    for tag in soup.find_all(block_tags):
        tag.append("\n")

    text = soup.get_text()

    # Collapse 3+ blank lines down to a max of one blank line, and strip
    # trailing whitespace from each line -- keeps paragraph breaks
    # (useful for the detail page) without leaving huge gaps.
    lines = [line.strip() for line in text.splitlines()]
    cleaned_lines: list[str] = []
    for line in lines:
        if line or (cleaned_lines and cleaned_lines[-1] != ""):
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()


def truncate_text(text: str, max_length: int) -> str:
    """
    Truncate to at most `max_length` characters, breaking on a word
    boundary rather than mid-word, with a trailing ellipsis. Returns
    the text unchanged if it's already short enough.
    """
    if len(text) <= max_length:
        return text

    truncated = text[:max_length].rsplit(" ", 1)[0]
    return f"{truncated}…"
