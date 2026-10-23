# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Propose a Slack reply as Neo. It never posts and never touches a Slack token: it leaves
the draft for the bridge, which DMs the owner a preview with "Post" / "Discard" and posts
only after the owner clicks Post. A newer draft for the same thread replaces the older one.

Usage:
  neo-say --link <slack permalink> < reply.md
  neo-say --channel C123 --thread 1792457823.946789 --text "..."
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import time
import uuid

from slack_links import thread_from_link

PENDING_DIR = os.path.expanduser("~/.config/neo-slack/drafts/pending")


def parse_link(link: str) -> tuple[str, str]:
    """Slack message link -> (channel, thread ts)."""
    target = thread_from_link(link)
    if not target:
        sys.exit(f"neo-say: not a Slack message link: {link}")
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--link", help="permalink of the message or thread to reply to")
    parser.add_argument("--channel")
    parser.add_argument("--thread", help="thread ts to reply in")
    parser.add_argument("--text", help="reply in Slack mrkdwn (*bold*, lists); tag people as <@U123>, "
                                       "never bare names; read from stdin when omitted")
    args = parser.parse_args()

    if args.link:
        channel, thread = parse_link(args.link)
    elif args.channel and args.thread:
        channel, thread = args.channel, args.thread
    else:
        parser.error("give --link, or --channel and --thread")
    if not re.fullmatch(r"[A-Z0-9]+", channel) or not re.fullmatch(r"\d+\.\d+", thread):
        parser.error("channel or thread ts has an unexpected format")
    text = (args.text if args.text is not None else sys.stdin.read()).strip()
    if not text:
        parser.error("the reply is empty")

    draft_id = uuid.uuid4().hex[:12]
    os.makedirs(PENDING_DIR, exist_ok=True)
    # Atomic: the bridge never sees a half-written draft.
    fd, tmp = tempfile.mkstemp(dir=PENDING_DIR, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump({"channel": channel, "thread_ts": thread, "text": text, "created": time.time()}, f)
    os.replace(tmp, os.path.join(PENDING_DIR, f"{draft_id}.json"))
    print(f"Draft {draft_id} queued. The bridge DMs the owner for approval; nothing is posted until they click Post.")


if __name__ == "__main__":
    main()
