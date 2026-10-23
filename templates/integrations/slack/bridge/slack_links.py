"""Slack message links -> (channel, thread ts). Shared by the bridge and neo-say."""

from __future__ import annotations

import re

LINK_RE = re.compile(r"https://[\w.-]+\.slack\.com/archives/([A-Z0-9]+)/p(\d{10})(\d{6})(\?[^|>\s]*)?")


def thread_from_link(text: str) -> tuple[str, str] | None:
    """First Slack message link in the text -> (channel, thread ts). A reply link
    (?thread_ts=...) resolves to its thread, any other link to the message itself."""
    match = LINK_RE.search(text)
    if not match:
        return None
    channel, ts = match.group(1), f"{match.group(2)}.{match.group(3)}"
    thread = re.search(r"thread_ts=(\d+\.\d+)", match.group(4) or "")
    return channel, thread.group(1) if thread else ts
