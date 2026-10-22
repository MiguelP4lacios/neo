# /// script
# requires-python = ">=3.11"
# dependencies = ["slack-sdk>=3.33"]
# ///
"""Propose a Slack reply as Neo. It never posts: the owner gets a DM preview with
"Post as Neo" / "Discard", and the bridge posts only after the owner clicks Post.

Usage:
  neo-say --link <slack permalink> < reply.md
  neo-say --channel C123 --thread 1792457823.946789 --text "..."
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import re
import subprocess
import sys
import uuid
from urllib.parse import parse_qs, urlparse

from slack_sdk import WebClient

DRAFTS_DIR = os.path.expanduser("~/.config/neo-slack/drafts")
CONFIG_FILE = os.path.expanduser("~/.config/neo-slack/config.json")
PREVIEW_LIMIT = 2900  # a section block holds at most 3000 chars


def bot_token() -> str:
    result = subprocess.run(
        ["security", "find-generic-password", "-a", getpass.getuser(), "-s", "neo-slack-bot-token", "-w"],
        capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        sys.exit("neo-say: Keychain item 'neo-slack-bot-token' is missing")
    return result.stdout.strip()


def owner_id() -> str:
    if os.environ.get("NEO_OWNER_ID"):
        return os.environ["NEO_OWNER_ID"]
    with open(CONFIG_FILE) as f:
        return json.load(f)["owner_id"]


def slack_name() -> str:
    """The name people see in Slack; internally it is always Neo."""
    if os.environ.get("NEO_SLACK_NAME"):
        return os.environ["NEO_SLACK_NAME"]
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f).get("slack_name", "Neo")
    except OSError:
        return "Neo"


def supersede(bot: WebClient, channel: str, thread: str) -> None:
    """Retire pending drafts for the same thread: only the newest one can be posted."""
    if not os.path.isdir(DRAFTS_DIR):
        return
    for name in os.listdir(DRAFTS_DIR):
        path = os.path.join(DRAFTS_DIR, name)
        try:
            with open(path) as f:
                old = json.load(f)
        except (OSError, ValueError):
            continue
        if (old.get("channel"), old.get("thread_ts")) != (channel, thread):
            continue
        os.remove(path)
        if old.get("dm_channel") and old.get("dm_ts"):
            outcome = ":arrows_counterclockwise: Superseded by a newer draft."
            bot.chat_update(channel=old["dm_channel"], ts=old["dm_ts"], text=outcome, blocks=[
                {"type": "section", "text": {"type": "mrkdwn", "text": f"~Old draft for this thread~\n{outcome}"}}])


def parse_link(link: str) -> tuple[str, str]:
    """https://x.slack.com/archives/C123/p1792457823946789?thread_ts=... -> (C123, thread ts)."""
    url = urlparse(link)
    match = re.search(r"/archives/([A-Z0-9]+)/p(\d{10})(\d{6})", url.path)
    if not match:
        sys.exit(f"neo-say: not a Slack message link: {link}")
    channel, ts = match.group(1), f"{match.group(2)}.{match.group(3)}"
    return channel, parse_qs(url.query).get("thread_ts", [ts])[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--link", help="permalink of the message or thread to reply to")
    parser.add_argument("--channel")
    parser.add_argument("--thread", help="thread ts to reply in")
    parser.add_argument("--text", help="reply in Slack mrkdwn (*bold*); tag people as <@U123>, never bare names; read from stdin when omitted")
    args = parser.parse_args()

    if args.link:
        channel, thread = parse_link(args.link)
    elif args.channel and args.thread:
        channel, thread = args.channel, args.thread
    else:
        parser.error("give --link, or --channel and --thread")
    text = (args.text if args.text is not None else sys.stdin.read()).strip()
    if not text:
        parser.error("the reply is empty")

    bot = WebClient(token=bot_token())
    supersede(bot, channel, thread)
    draft_id = uuid.uuid4().hex[:12]
    os.makedirs(DRAFTS_DIR, exist_ok=True)
    draft_path = os.path.join(DRAFTS_DIR, f"{draft_id}.json")
    draft = {"channel": channel, "thread_ts": thread, "text": text}
    with open(draft_path, "w") as f:
        json.dump(draft, f)
    try:
        where = bot.chat_getPermalink(channel=channel, message_ts=thread)["permalink"]
    except Exception:  # noqa: BLE001 - the preview still works without a link
        where = f"channel {channel}, thread {thread}"
    preview = text if len(text) <= PREVIEW_LIMIT else text[:PREVIEW_LIMIT] + "\n…(truncated preview, full text is posted)"
    name = slack_name()
    dm = bot.conversations_open(users=owner_id())["channel"]["id"]
    sent = bot.chat_postMessage(
        channel=dm,
        text=f"{name} wants to reply in {where}",
        blocks=[
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Proposed reply as {name}* in {where}"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": preview}},
            {"type": "actions", "elements": [
                {"type": "button", "style": "primary", "action_id": "neo_post", "value": draft_id,
                 "text": {"type": "plain_text", "text": f"Post as {name}"}},
                {"type": "button", "action_id": "neo_discard", "value": draft_id,
                 "text": {"type": "plain_text", "text": "Discard"}},
            ]},
        ],
    )
    # Remember where the approval DM is, so a newer draft can close its buttons.
    with open(draft_path, "w") as f:
        json.dump({**draft, "dm_channel": dm, "dm_ts": sent["ts"]}, f)
    print(f"Draft {draft_id} sent to the owner for approval. Nothing is posted until they click Post.")


if __name__ == "__main__":
    main()
