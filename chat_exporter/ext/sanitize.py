import html
import re
from urllib.parse import urlsplit

SAFE_URL_SCHEMES = frozenset({"http", "https"})

# Browsers ignore control characters and whitespace in a scheme ("java\tscript:"), so strip them before checking.
_IGNORED_URL_CHARS = re.compile(r"[\x00-\x20\x7f]")
_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")


def escape(value) -> str:
    """Escapes text for use in HTML text or a quoted attribute value."""
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def normalise_text(content) -> str:
    """Returns text HTML-escaped exactly once, for use in HTML text (not attributes).

    Callers historically passed either raw or already-escaped text. Unescaping first makes both safe:
    escaped input renders the same, and raw input can no longer inject markup.
    """
    if content is None:
        return ""
    return html.escape(html.unescape(str(content)), quote=False)


def safe_url(value, schemes=SAFE_URL_SCHEMES) -> str:
    """Returns the URL escaped for a quoted attribute, or "" if it isn't an absolute URL with an allowed scheme."""
    if value is None:
        return ""
    url = _CONTROL_CHARS.sub("", str(value)).strip()
    if not url:
        return ""

    try:
        parts = urlsplit(_IGNORED_URL_CHARS.sub("", url))
    except ValueError:
        return ""

    if parts.scheme.lower() not in schemes or not parts.netloc:
        return ""
    return html.escape(url, quote=True)
