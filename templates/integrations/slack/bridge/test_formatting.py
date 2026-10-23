"""Tests for slack_format and slack_links. Run: python3 -m unittest test_formatting.py"""

import unittest

from slack_format import inline, to_rich_text
from slack_links import thread_from_link


def kinds(block: dict) -> list[tuple[str, str]]:
    return [(e["type"], e.get("style", "")) for e in block["elements"]]


class RichTextTest(unittest.TestCase):
    def test_paragraphs_become_sections(self):
        block = to_rich_text("first line\nsecond line\n\nnext paragraph")
        self.assertEqual(block["type"], "rich_text")
        self.assertEqual(kinds(block), [("rich_text_section", ""), ("rich_text_section", "")])
        self.assertEqual(block["elements"][0]["elements"][0]["text"].split("\n")[:2], ["first line", "second line"])

    def test_numbered_list_keeps_its_numbering_after_a_nested_item(self):
        block = to_rich_text("1. one\n2. two\n  - nested\n3. three")
        lists = [e for e in block["elements"] if e["type"] == "rich_text_list"]
        self.assertEqual([(l["style"], l["indent"], len(l["elements"])) for l in lists],
                         [("ordered", 0, 2), ("bullet", 1, 1), ("ordered", 0, 1)])
        self.assertEqual(lists[2]["offset"], 2)

    def test_bullet_markers(self):
        for marker in ("-", "•", "*"):
            block = to_rich_text(f"{marker} a\n{marker} b")
            self.assertEqual(block["elements"][0]["style"], "bullet")
            self.assertEqual(len(block["elements"][0]["elements"]), 2)

    def test_code_block_is_preformatted(self):
        block = to_rich_text("```\nSELECT 1;\n```")
        self.assertEqual(block["elements"][0]["type"], "rich_text_preformatted")
        self.assertEqual(block["elements"][0]["elements"][0]["text"], "SELECT 1;")

    def test_inline_elements(self):
        els = inline("hi <@U0ABC|Ana> see <!subteam^S0XYZ> *bold* _it_ `code` <https://a.b|docs> https://c.d")
        types = [(e["type"], tuple(sorted(e.get("style", {})))) for e in els if e["type"] != "text" or e.get("style")]
        self.assertIn(("user", ()), types)
        self.assertIn(("usergroup", ()), types)
        self.assertIn(("text", ("bold",)), types)
        self.assertIn(("text", ("italic",)), types)
        self.assertIn(("text", ("code",)), types)
        links = [e for e in els if e["type"] == "link"]
        self.assertEqual([(l["url"], l.get("text")) for l in links], [("https://a.b", "docs"), ("https://c.d", None)])

    def test_asterisks_inside_words_are_not_bold(self):
        els = inline("2*3*4 stays plain")
        self.assertTrue(all("style" not in e for e in els))

    def test_empty_text_still_valid(self):
        self.assertEqual(inline(""), [{"type": "text", "text": " "}])


class LinkTest(unittest.TestCase):
    def test_message_link(self):
        self.assertEqual(thread_from_link("https://x.slack.com/archives/C0TEST/p1792457823946789"),
                         ("C0TEST", "1792457823.946789"))

    def test_reply_link_resolves_to_its_thread(self):
        link = "<https://x.slack.com/archives/C1/p1792514192016009?thread_ts=1792512307.299699&cid=C1|label>"
        self.assertEqual(thread_from_link(link), ("C1", "1792512307.299699"))

    def test_no_link(self):
        self.assertIsNone(thread_from_link("no link here"))
        self.assertIsNone(thread_from_link("https://example.com/archives/C1/p1792457823946789"))


if __name__ == "__main__":
    unittest.main()
