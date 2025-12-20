"""
Input Sanitization Utilities
Centralized input sanitization for security across all routers.

Prevents XSS, HTML injection, and other input-based attacks.
"""

import re
from typing import Optional

import bleach

# Characters that are safe in most contexts
SAFE_PUNCTUATION = ".,!?;:'\"()-_/@#$%&*+=<>[]{}|\\~`"


def sanitize_text(
    text: Optional[str],
    max_length: int = 2000,
    strip_html: bool = True,
    preserve_newlines: bool = True,
) -> str:
    """
    Sanitize user-provided text input.

    Args:
        text: The text to sanitize
        max_length: Maximum allowed length (truncate if exceeded)
        strip_html: If True, removes all HTML tags
        preserve_newlines: If True, preserves \\n and \\r characters

    Returns:
        Sanitized string, safe for display and storage
    """
    if not text:
        return ""

    # Remove HTML tags if requested
    if strip_html:
        text = bleach.clean(text, tags=[], attributes={}, strip=True)

    # Remove null bytes and control characters
    if preserve_newlines:
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    else:
        text = ''.join(char for char in text if ord(char) >= 32 or char == '\t')

    # Truncate to max length
    if len(text) > max_length:
        text = text[:max_length]

    return text.strip()


def sanitize_html(
    text: Optional[str],
    allowed_tags: list = None,
    max_length: int = 10000,
) -> str:
    """
    Sanitize HTML content, allowing only safe tags.

    Use this for rich text fields that legitimately need HTML.

    Args:
        text: The HTML text to sanitize
        allowed_tags: List of allowed HTML tags (default: basic formatting)
        max_length: Maximum allowed length

    Returns:
        Sanitized HTML string
    """
    if not text:
        return ""

    if allowed_tags is None:
        # Safe subset of HTML tags for rich text
        allowed_tags = [
            'p', 'br', 'b', 'i', 'u', 'strong', 'em',
            'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'blockquote', 'pre', 'code', 'hr',
        ]

    # Clean with allowed tags
    text = bleach.clean(
        text,
        tags=allowed_tags,
        attributes={},
        strip=True,
    )

    # Remove null bytes
    text = text.replace('\x00', '')

    # Truncate
    if len(text) > max_length:
        text = text[:max_length]

    return text.strip()


def sanitize_identifier(
    text: Optional[str],
    max_length: int = 100,
    allow_spaces: bool = False,
) -> str:
    """
    Sanitize identifiers (IDs, slugs, names used in URLs/queries).

    More restrictive than sanitize_text - only allows alphanumeric,
    underscore, hyphen, and optionally spaces.

    Args:
        text: The identifier to sanitize
        max_length: Maximum allowed length
        allow_spaces: If True, allows spaces (useful for names)

    Returns:
        Sanitized identifier string
    """
    if not text:
        return ""

    # Strip HTML first
    text = bleach.clean(text, tags=[], attributes={}, strip=True)

    # Define allowed pattern
    if allow_spaces:
        pattern = r'[^a-zA-Z0-9_\-\s]'
    else:
        pattern = r'[^a-zA-Z0-9_\-]'

    # Remove disallowed characters
    text = re.sub(pattern, '', text)

    # Collapse multiple spaces/underscores
    text = re.sub(r'[\s_]+', '_' if not allow_spaces else ' ', text)

    # Truncate
    if len(text) > max_length:
        text = text[:max_length]

    return text.strip()


def sanitize_email(email: Optional[str]) -> str:
    """
    Basic email sanitization.

    Note: This does basic cleanup, not full validation.
    Use pydantic EmailStr for full validation.
    """
    if not email:
        return ""

    # Remove HTML tags
    email = bleach.clean(email, tags=[], attributes={}, strip=True)

    # Remove whitespace and null bytes
    email = email.replace('\x00', '').strip()

    # Basic length check
    if len(email) > 320:  # RFC 5321 limit
        email = email[:320]

    return email.lower()


def sanitize_url(url: Optional[str]) -> str:
    """
    Sanitize URL input.

    Prevents javascript: and data: URLs that could execute code.
    """
    if not url:
        return ""

    # Strip HTML tags
    url = bleach.clean(url, tags=[], attributes={}, strip=True)

    # Remove whitespace
    url = url.strip()

    # Block dangerous URL schemes
    url_lower = url.lower()
    dangerous_schemes = ['javascript:', 'data:', 'vbscript:', 'file:']
    for scheme in dangerous_schemes:
        if url_lower.startswith(scheme):
            return ""

    # Limit length
    if len(url) > 2048:
        url = url[:2048]

    return url


def sanitize_search_query(query: Optional[str], max_length: int = 200) -> str:
    """
    Sanitize search queries.

    Removes special characters that could affect search behavior
    while preserving meaningful search terms.
    """
    if not query:
        return ""

    # Strip HTML
    query = bleach.clean(query, tags=[], attributes={}, strip=True)

    # Remove characters that could affect regex/SQL (extra safety)
    # Keep alphanumeric, spaces, and common punctuation
    query = re.sub(r'[^\w\s\-.\'"!?,]', '', query, flags=re.UNICODE)

    # Collapse multiple spaces
    query = re.sub(r'\s+', ' ', query)

    # Truncate
    if len(query) > max_length:
        query = query[:max_length]

    return query.strip()
