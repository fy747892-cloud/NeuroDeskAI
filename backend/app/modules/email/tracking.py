import base64
import html
import re
import uuid
from urllib.parse import quote

from app.core.config import settings

# A minimal 1x1 transparent PNG, used as the invisible open-tracking pixel.
_TRACKING_PIXEL_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)
TRACKING_PIXEL_PNG: bytes = base64.b64decode(_TRACKING_PIXEL_PNG_B64)

_URL_PATTERN = re.compile(r"https?://\S+")


def _tracking_base_url() -> str:
    return settings.oauth_redirect_base_url.rstrip("/")


def build_pixel_url(*, message_id: uuid.UUID) -> str:
    return f"{_tracking_base_url()}/api/v1/email/track/{message_id}/pixel.png"


def build_click_url(*, message_id: uuid.UUID, target_url: str) -> str:
    return f"{_tracking_base_url()}/api/v1/email/track/{message_id}/click?url={quote(target_url, safe='')}"


def build_html_body(*, message_id: uuid.UUID, plain_text: str) -> str:
    """Turn a plain-text email body into a tracked HTML version: escapes the
    text (it's user-authored, never trust it as HTML), wraps any bare links
    through the click-tracking redirect, and appends an invisible open-tracking
    pixel at the end.

    URLs are matched against the raw, unescaped text (so the tracked redirect
    is built from the real URL) and everything else is escaped independently —
    escaping the whole body first would corrupt matched URLs (e.g. "&" query
    separators become "&amp;"), and linkifying first would leave the
    surrounding plain text unescaped, an HTML-injection risk.
    """
    pieces: list[str] = []
    last_end = 0
    for match in _URL_PATTERN.finditer(plain_text):
        pieces.append(html.escape(plain_text[last_end : match.start()]))
        original_url = match.group(0)
        tracked_url = build_click_url(message_id=message_id, target_url=original_url)
        pieces.append(f'<a href="{html.escape(tracked_url)}">{html.escape(original_url)}</a>')
        last_end = match.end()
    pieces.append(html.escape(plain_text[last_end:]))

    body_html = "".join(pieces).replace("\n", "<br>\n")
    pixel_url = html.escape(build_pixel_url(message_id=message_id))

    return (
        f"<html><body>{body_html}"
        f'<img src="{pixel_url}" width="1" height="1" alt="" style="display:none" />'
        f"</body></html>"
    )
