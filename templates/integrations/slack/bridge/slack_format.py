"""Turn a Slack mrkdwn draft into a rich_text block, the format Slack's own editor produces.

mrkdwn has no real lists: "1." and "•" lines render as plain text with no indentation.
rich_text lists render like the ones people type. Supported: paragraphs, "1." / "-" / "•" lists
(two spaces of indentation per nesting level), *bold*, _italic_, `code`, ```code blocks```,
<@U123> mentions, <!subteam^S123> groups, <url|label> and bare https links.
"""

from __future__ import annotations

import re

INLINE = re.compile(
    r"<@(?P<user>[UW][A-Z0-9]+)(?:\|[^>]*)?>"
    r"|<!subteam\^(?P<group>S[A-Z0-9]+)(?:\|[^>]*)?>"
    r"|<(?P<url>https?://[^|>]+)(?:\|(?P<label>[^>]+))?>"
    r"|`(?P<code>[^`]+)`"
    r"|(?<![\w*])\*(?P<bold>[^*\n]+)\*(?![\w*])"
    r"|(?<![\w_])_(?P<italic>[^_\n]+)_(?![\w_])"
    r"|(?P<bare>https?://[^\s<>]+)"
)
LIST_ITEM = re.compile(r"^(?P<indent> *)(?:(?P<num>\d+)[.)]|[-•*])\s+(?P<body>.*)$")


def inline(text: str) -> list[dict]:
    out: list[dict] = []
    pos = 0
    for m in INLINE.finditer(text):
        if m.start() > pos:
            out.append({"type": "text", "text": text[pos:m.start()]})
        if m["user"]:
            out.append({"type": "user", "user_id": m["user"]})
        elif m["group"]:
            out.append({"type": "usergroup", "usergroup_id": m["group"]})
        elif m["url"]:
            out.append({"type": "link", "url": m["url"], **({"text": m["label"]} if m["label"] else {})})
        elif m["code"]:
            out.append({"type": "text", "text": m["code"], "style": {"code": True}})
        elif m["bold"]:
            out.extend({**el, "style": {**el.get("style", {}), "bold": True}} for el in inline(m["bold"]))
        elif m["italic"]:
            out.extend({**el, "style": {**el.get("style", {}), "italic": True}} for el in inline(m["italic"]))
        elif m["bare"]:
            out.append({"type": "link", "url": m["bare"]})
        pos = m.end()
    if pos < len(text):
        out.append({"type": "text", "text": text[pos:]})
    return out or [{"type": "text", "text": " "}]


def to_rich_text(mrkdwn: str) -> dict:
    elements: list[dict] = []
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            elements.append({"type": "rich_text_section", "elements": inline("\n".join(paragraph))})
            paragraph.clear()

    lines = mrkdwn.strip().split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if len(stripped) > 6 and stripped.startswith("```") and stripped.endswith("```"):
            # Whole code block on one line: ```SELECT 1;```
            flush_paragraph()
            elements.append({"type": "rich_text_preformatted",
                             "elements": [{"type": "text", "text": stripped[3:-3].strip() or " "}]})
        elif stripped.startswith("```"):
            flush_paragraph()
            code, i = [], i + 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            elements.append({"type": "rich_text_preformatted",
                             "elements": [{"type": "text", "text": "\n".join(code) or " "}]})
        elif item := LIST_ITEM.match(line):
            flush_paragraph()
            style = "ordered" if item["num"] else "bullet"
            indent = min(len(item["indent"]) // 2, 6)
            last = elements[-1] if elements else None
            entry = {"type": "rich_text_section", "elements": inline(item["body"])}
            if last and last["type"] == "rich_text_list" and last["style"] == style and last["indent"] == indent:
                last["elements"].append(entry)
            else:
                block = {"type": "rich_text_list", "style": style, "indent": indent, "elements": [entry]}
                if style == "ordered" and item["num"] != "1":
                    block["offset"] = int(item["num"]) - 1
                elements.append(block)
        elif not line.strip():
            flush_paragraph()
            # A blank line between blocks keeps the spacing the author wrote.
            if elements and elements[-1]["type"] == "rich_text_section":
                elements[-1]["elements"].append({"type": "text", "text": "\n"})
        else:
            paragraph.append(line)
        i += 1
    flush_paragraph()
    return {"type": "rich_text", "elements": elements}
