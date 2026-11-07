"""Security and regression tests for HTML/URL injection, streaming and state isolation."""

import asyncio
import io
import unittest
from datetime import datetime
from unittest.mock import MagicMock

import pytz

import chat_exporter
from chat_exporter.construct.assets.component import Component
from chat_exporter.ext.discord_import import discord
from chat_exporter.ext.sanitize import safe_url
from chat_exporter.parse.ast import AstParser
from chat_exporter.parse.markdown import ParseMarkdown
from tests.test_export import _make_author, _make_channel, _make_embed, _make_guild, _make_message


def _run(coro):
    return asyncio.run(coro)


class TestSanitizeAndMarkdown(unittest.TestCase):
    def test_safe_url_blocks_bad_schemes(self):
        for bad in (
            "javascript:alert(1)",
            "JAVASCRIPT:alert(1)",
            "java\t\nscript:alert(1)",
            "\x01javascript:alert(1)",
            "data:text/html,<script>alert(1)</script>",
            "vbscript:msgbox(1)",
            "file:///etc/passwd",
            "//evil.example/x.js",
            "/relative/path",
            "http://",
        ):
            self.assertEqual(safe_url(bad), "", f"should reject {bad!r}")

        self.assertEqual(safe_url('https://example.com/a"b<c>'), "https://example.com/a&quot;b&lt;c&gt;")

    def test_ast_escapes_raw_html_and_drops_html_node(self):
        out = "".join(n.render() for n in AstParser().parse("<script>alert(1)</script> **ok**"))
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", out)
        self.assertIn("<strong>ok</strong>", out)

    def test_masked_link_blocks_javascript_and_escapes_href(self):
        out = _run(ParseMarkdown("[click](javascript:alert`1`)").standard_message_flow())
        self.assertNotIn("javascript:", out)
        self.assertEqual(out, "click")

        out = _run(ParseMarkdown('[ok](https://example.com/a"onmouseover="x)').standard_message_flow())
        self.assertIn('href="https://example.com/a&quot;onmouseover=&quot;x"', out)

    def test_shield_placeholder_forgery_cannot_break_out_of_attribute(self):
        payload = "[x]({{SHIELD_0}})\n```x/onmouseover=alert`1`//\ncode\n```"
        out = _run(ParseMarkdown(payload).standard_message_flow())
        self.assertNotIn("onmouseover=", out)
        self.assertNotIn("<a ", out)
        self.assertIn('class="pre pre--multiline language-xonmouseoveralert1"', out)

    def test_mention_names_are_escaped_without_placeholder_garbage(self):
        guild = _make_guild()

        role = MagicMock()
        role.name = '" onmouseover=alert(1) <script>'
        role.color.r, role.color.g, role.color.b = 255, 0, 0
        guild.get_role.return_value = role

        channel = MagicMock()
        channel.id = 99
        channel.name = "<img src=x onerror=alert(1)>"
        guild.get_channel.return_value = channel

        member = MagicMock()
        member.display_name = "a <b> & \"c\""
        guild.get_member.return_value = member

        out = _run(ParseMarkdown("<@&1> <#99> <@2>", guild).standard_message_flow())
        self.assertNotIn("<script>", out)
        self.assertNotIn("<img src=x", out)
        self.assertNotIn("______", out)
        self.assertIn("@a &lt;b&gt; &amp; &quot;c&quot;", out)
        self.assertIn('title="&quot; onmouseover=alert(1) &lt;script&gt;"', out)

    def test_custom_emoji_with_underscores_is_not_split_by_italic(self):
        out = _run(ParseMarkdown("<:uno_reverse:12345> and <:two_words:67890>").standard_message_flow())
        self.assertNotIn("<em>", out)
        self.assertEqual(out.count("cdn.discordapp.com/emojis/"), 2)

    def test_forged_custom_emoji_does_not_swallow_following_markup(self):
        out = _run(ParseMarkdown("<:<t:5>").standard_message_flow())
        self.assertIn('class="unix-timestamp"', out)


class TestFullTranscriptEscaping(unittest.TestCase):
    def test_all_user_and_server_fields_are_escaped(self):
        guild = _make_guild(name='<script>alert("guild")</script> [g](javascript:alert(1))')
        channel = _make_channel(guild=guild)
        channel.name = '<img src=x onerror=alert("chan")>'
        channel.topic = '<img src=x onerror=alert("topic")>'

        bad_author = _make_author(name='" onmouseover=alert("user") <x>')
        bad_author.display_name = '<img src=x onerror=alert("nick")> [n](javascript:alert(1))'

        # Message 1: target of a reply, with raw HTML in content
        m1 = _make_message(content='<img src=x onerror=alert("reply")>', msg_id=1, author=bad_author, guild=guild)

        # Message 2: replies to m1, has attachment + reaction + embed + components with malicious values
        m2 = _make_message(content="normal body", msg_id=2, author=bad_author, guild=guild)
        ref = MagicMock()
        ref.message_id = 1
        ref.channel_id = channel.id
        ref.guild_id = guild.id
        m2.reference = ref

        att = MagicMock()
        att.content_type = "application/octet-stream"
        att.url = "https://cdn.discordapp.com/attachments/1/2/file.txt"
        att.proxy_url = att.url
        att.filename = '<img src=x onerror=alert("file")>.txt'
        att.size = 100
        att.spoiler = False
        att.is_spoiler = lambda: False
        m2.attachments = [att]

        reactor = MagicMock()
        reactor.display_name = '<img src=x onerror=alert("react")>'
        reaction = MagicMock()
        reaction.emoji = "<a:party:42>"
        reaction.count = 12

        async def _users(limit=10):
            yield reactor

        reaction.users = _users
        m2.reactions = [reaction]

        m2.embeds = [
            _make_embed(
                title="Title",
                url="javascript:alert('title')",
                description='<img src=x onerror=alert("desc")>',
                author_name="Auth",
                author_url="javascript:alert('author')",
                author_icon='x" onerror=alert("aicon")',
                image_url="javascript:alert('img')",
                thumbnail_url='x" onerror=alert("thumb")',
                footer_text="Foot",
                footer_icon="javascript:alert('ficon')",
            )
        ]

        # Thread-created system message with HTML in the thread name
        m3 = _make_message(content='<img src=x onerror=alert("thread")>', msg_id=3, author=bad_author, guild=guild)
        m3.type = discord.MessageType.thread_created

        html_out = _run(chat_exporter.raw_export(channel, [m1, m2, m3], tz_info="UTC", fetch_reactors=True))

        for forbidden in (
            '<script>alert("guild")',
            '<img src=x onerror=alert("chan")>',
            '<img src=x onerror=alert("topic")>',
            '<img src=x onerror=alert("nick")>',
            '<img src=x onerror=alert("reply")>',
            '<img src=x onerror=alert("file")>',
            '<img src=x onerror=alert("react")>',
            '<img src=x onerror=alert("desc")>',
            '<img src=x onerror=alert("thread")>',
            'onmouseover=alert("user")',
            'onerror=alert("aicon")',
            'onerror=alert("thumb")',
            'href="javascript:',
            "src=\"javascript:",
        ):
            self.assertNotIn(forbidden, html_out)

        # Animated custom reaction now renders as .gif (was broken before)
        self.assertIn("https://cdn.discordapp.com/emojis/42.gif", html_out)
        # Re-exporting the same message objects must still work (no in-place mutation)
        self.assertIs(m2.reference, ref)
        html_again = _run(chat_exporter.raw_export(channel, [m1, m2, m3], tz_info="UTC", fetch_reactors=True))
        self.assertIn("chatlog__followup", html_again)

    def test_component_attributes_cannot_break_out_via_markdown_or_urls(self):
        guild = _make_guild()
        btn = {
            "type": 2,
            "style": 5,
            "label": "go",
            "url": "javascript:alert(1)",
            "disabled": False,
        }
        menu = {
            "type": 3,
            "placeholder": '[p]( onmouseover=alert`1` x=)',
            "options": [{"label": "opt", "description": "desc"}],
            "disabled": False,
        }
        thumb = {
            "type": 11,
            "media": {"url": "https://cdn.discordapp.com/a.png"},
            "description": '[d]( onmouseover=alert`2` x=) <script>',
            "spoiler": False,
        }
        file_comp = {
            "type": 13,
            "file": {"url": "javascript:alert(3)"},
            "name": "<img src=x onerror=alert(4)>",
            "size": 10,
        }
        for comp in (btn, menu, thumb, file_comp):
            out = _run(Component(comp, guild).flow())
            self.assertNotIn("javascript:alert", out)
            self.assertNotIn("onmouseover=alert", out)
            self.assertNotIn("<script>", out)
            self.assertNotIn("<img src=x onerror", out)
            self.assertNotIn("{{html.escape", out)

    def test_export_to_file_matches_raw_export_and_handles_stop(self):
        guild = _make_guild()
        channel = _make_channel(guild=guild)
        msgs = [
            _make_message(content=f"msg **{i}**", msg_id=i + 1, created_at=datetime(2024, 1, 1, 12, i, tzinfo=pytz.utc), guild=guild)
            for i in range(10)
        ]

        # raw_export reverses a newest-first list; pass oldest-first to export_to_file
        raw_html = _run(chat_exporter.raw_export(channel, list(reversed(msgs)), tz_info="UTC", fetch_reactors=False))
        buf = io.BytesIO()
        count = _run(chat_exporter.export_to_file(channel, buf, messages=msgs, tz_info="UTC", fetch_reactors=False))
        self.assertEqual(count, 10)
        streamed_html = buf.getvalue().decode("utf-8")

        import re

        def norm(s):
            return re.sub(r"\d{1,2} \w+ \d{4} at \d\d:\d\d:\d\d [AP]M \(UTC\)", "<NOW>", s)

        self.assertEqual(norm(raw_html), norm(streamed_html))

        # Stopping early writes a complete, valid page with the collected messages
        seen = 0

        def stop():
            nonlocal seen
            seen += 1
            return seen > 3

        buf2 = io.BytesIO()
        count2 = _run(chat_exporter.export_to_file(channel, buf2, messages=msgs, tz_info="UTC", should_stop=stop))
        self.assertEqual(count2, 3)
        self.assertTrue(buf2.getvalue().decode("utf-8").rstrip().endswith("</html>"))
        self.assertNotIn("{{MESSAGES}}", buf2.getvalue().decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
