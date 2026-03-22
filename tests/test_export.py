"""
Integration tests for chat_exporter using mocked Discord objects.

These tests exercise the full rendering pipeline (raw_export) without
needing a live Discord connection. A small HTML artifact is saved to
tests/artifacts/ for visual inspection if needed.
"""

import asyncio
import os
import unittest
from datetime import datetime
from unittest.mock import MagicMock

import pytz

import chat_exporter
from chat_exporter.ext.discord_import import discord

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "artifacts")


def _make_guild(name="Test Guild", guild_id=111111111111111111):
    guild = MagicMock(spec=discord.Guild)
    guild.id = guild_id
    guild.name = name
    guild.icon = None
    guild.get_channel.return_value = None
    guild.get_member.return_value = None
    guild.get_role.return_value = None
    guild.timezone = "UTC"
    return guild


def _make_author(name="testuser", user_id=222222222222222222, bot=False):
    author = MagicMock(spec=discord.Member)
    author.id = user_id
    author.name = name
    author.discriminator = "0"
    author.display_name = name
    author.display_avatar = None
    author.display_icon = None
    author.top_role = None
    author.colour = "#FFFFFF"
    author.bot = bot
    author.public_flags.verified_bot = False
    author.created_at = datetime(2020, 1, 1, tzinfo=pytz.utc)
    author.joined_at = datetime(2021, 1, 1, tzinfo=pytz.utc)
    return author


def _make_message(content="", msg_id=1, created_at=None, author=None, guild=None):
    msg = MagicMock()
    msg.id = msg_id
    msg.type = MagicMock()
    msg.type.__eq__ = lambda self, other: False  # not a special message type
    msg.content = content
    msg.created_at = created_at or datetime(2024, 1, 1, 12, 0, 0, tzinfo=pytz.utc)
    msg.edited_at = None
    msg.author = author or _make_author()
    msg.reference = None
    msg.attachments = []
    msg.embeds = []
    msg.reactions = []
    msg.components = []
    msg.stickers = []
    msg.interaction = None
    msg.message_snapshots = []
    msg.channel = MagicMock()
    msg.channel.type = MagicMock()
    msg.channel.type.__str__ = lambda self: "text"
    msg.channel.guild = guild or _make_guild()
    return msg


def _make_channel(guild=None):
    ch = MagicMock()
    ch.name = "test-channel"
    ch.id = 333333333333333333
    ch.topic = None
    ch.guild = guild or _make_guild()
    ch.type = MagicMock()
    ch.type.__str__ = lambda self: "text"
    ch.created_at = datetime(2019, 1, 1, tzinfo=pytz.utc)
    return ch


def _make_embed(
    title=None,
    description=None,
    colour=0x5B8DEF,
    fields=None,
    author_name=None,
    author_icon=None,
    author_url=None,
    footer_text=None,
    footer_icon=None,
    image_url=None,
    thumbnail_url=None,
    timestamp=None,
    url=None,
):
    embed = MagicMock(spec=discord.Embed)
    embed.title = title
    embed.description = description
    embed.colour = MagicMock()
    embed.colour.r = (colour >> 16) & 0xFF
    embed.colour.g = (colour >> 8) & 0xFF
    embed.colour.b = colour & 0xFF
    embed.colour.__ne__ = lambda s, o: True

    embed.fields = []
    if fields:
        for f in fields:
            field = MagicMock()
            field.name = f.get("name")
            field.value = f.get("value")
            field.inline = f.get("inline", False)
            embed.fields.append(field)

    embed.author = MagicMock()
    embed.author.name = author_name
    embed.author.icon_url = author_icon
    embed.author.url = author_url

    embed.footer = MagicMock()
    embed.footer.text = footer_text
    embed.footer.icon_url = footer_icon

    embed.image = MagicMock()
    embed.image.url = image_url
    embed.image.proxy_url = image_url

    embed.thumbnail = MagicMock()
    embed.thumbnail.url = thumbnail_url
    embed.thumbnail.proxy_url = thumbnail_url

    embed.timestamp = timestamp
    embed.url = url
    return embed


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestRawExport(unittest.TestCase):
    def setUp(self):
        self.guild = _make_guild()
        self.channel = _make_channel(guild=self.guild)
        os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    def _export(self, messages, filename=None, channel=None, guild=None):
        channel = channel or self.channel
        guild = guild or self.guild
        html = _run(
            chat_exporter.raw_export(
                channel=channel,
                messages=messages,
                tz_info="UTC",
                military_time=True,
                guild=guild,
            )
        )
        if filename and html:
            path = os.path.join(ARTIFACTS_DIR, filename)
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
        return html

    def test_plain_message_renders(self):
        """A simple plain-text message should appear in the exported HTML."""
        msg = _make_message("Hello, world!", guild=self.guild)
        html = self._export([msg], "plain_message.html")
        self.assertIsNotNone(html)
        self.assertIn("Hello, world!", html)

    def test_bold_formatting_in_message(self):
        """Bold markdown in a message should render as <strong> tags."""
        msg = _make_message("This is **bold** text", guild=self.guild)
        html = self._export([msg], "bold_formatting.html")
        self.assertIn("<strong>bold</strong>", html)

    def test_heading_in_message(self):
        """Heading markdown should render as <h1> tags."""
        msg = _make_message("# Big Title\nSome text below.", guild=self.guild)
        html = self._export([msg], "heading.html")
        self.assertIn("<h1>Big Title</h1>", html)

    def test_blockquote_in_message(self):
        """Blockquote markdown should render inside a .quote div."""
        msg = _make_message("> This is a quote", guild=self.guild)
        html = self._export([msg], "blockquote.html")
        self.assertIn('class="quote"', html)
        self.assertIn("This is a quote", html)

    def test_subtext_in_message(self):
        """Subtext -# should render as a <small> tag."""
        msg = _make_message("-# small print here", guild=self.guild)
        html = self._export([msg], "subtext.html")
        self.assertIn("<small>small print here</small>", html)

    def test_multiple_messages(self):
        """Multiple messages should all appear in the final export."""
        msgs = [
            _make_message("First message", msg_id=1, guild=self.guild),
            _make_message("Second message", msg_id=2, guild=self.guild),
            _make_message("Third message", msg_id=3, guild=self.guild),
        ]
        html = self._export(msgs, "multiple_messages.html")
        self.assertIn("First message", html)
        self.assertIn("Second message", html)
        self.assertIn("Third message", html)

    def test_bot_message(self):
        """Bot-authored messages should include a bot tag."""
        author = _make_author(name="MyBot", bot=True)
        msg = _make_message("I am a bot!", author=author, guild=self.guild)
        html = self._export([msg], "bot_message.html")
        self.assertIn("I am a bot!", html)
        self.assertIn("bot-tag", html)

    def test_heading_no_trailing_breaks(self):
        """Headings followed by blank lines should not produce extra <br> before the next text."""
        msg = _make_message("# Title\n\n\n\nContent below", guild=self.guild)
        html = self._export([msg], "heading_no_breaks.html")
        # The heading should render, then Content without piles of <br> between them
        self.assertIn("<h1>Title</h1>", html)
        self.assertIn("Content below", html)

    def test_mention_display_name_like_mention_no_infinite_loop(self):
        """
        Regression test for GitHub issue #151.
        A user whose display_name is itself formatted as a mention (e.g. '<@999999999>')
        should not cause an infinite loop. The export should complete quickly.
        """
        import asyncio

        # Mock a member whose display_name looks like a mention
        malicious_member = MagicMock(spec=discord.Member)
        malicious_member.id = 1234567890
        malicious_member.display_name = "<@999999999>"
        malicious_member.display_avatar = None
        malicious_member.display_icon = None
        malicious_member.top_role = None
        malicious_member.colour = "#FFFFFF"

        guild = _make_guild()
        guild.get_member.return_value = malicious_member

        # The message content contains a mention of that member
        msg = _make_message("<@1234567890> said hello", guild=guild)
        msg.channel.guild = guild

        # This should complete without hanging — if it loops infinitely the test will timeout
        try:
            result = _run(
                asyncio.wait_for(
                    chat_exporter.raw_export(channel=self.channel, messages=[msg], guild=guild), timeout=5.0
                )
            )
            # Export should produce some HTML
            self.assertIsNotNone(result)
        except asyncio.TimeoutError:
            self.fail("raw_export timed out — possible infinite loop regression (issue #151)")

    def test_embed_with_member_mention_in_description(self):
        """An embed description containing a member mention should render the mention span correctly."""
        member = MagicMock(spec=discord.Member)
        member.id = 987654321
        member.display_name = "TestUser"
        member.display_avatar = None
        member.display_icon = None
        member.top_role = None
        member.colour = "#FFFFFF"

        guild = _make_guild()
        guild.get_member.return_value = member
        channel = _make_channel(guild=guild)

        # Build a realistic embed where None-sentinel fields really are None
        embed = MagicMock(
            spec=[
                "colour",
                "title",
                "description",
                "fields",
                "author",
                "image",
                "thumbnail",
                "footer",
                "timestamp",
                "url",
            ]
        )
        embed.colour = MagicMock()
        embed.colour.r, embed.colour.g, embed.colour.b = 0x5B, 0x8D, 0xEF
        embed.colour.__ne__ = lambda s, o: True
        embed.title = None
        embed.description = "<@987654321> is mentioned here"
        embed.fields = []
        embed.author = MagicMock()
        embed.author.name = None
        embed.author.url = None
        embed.author.icon_url = None
        embed.image = MagicMock()
        embed.image.url = None
        embed.thumbnail = MagicMock()
        embed.thumbnail.url = None
        embed.footer = MagicMock()
        embed.footer.text = None
        embed.footer.icon_url = None
        embed.timestamp = None
        embed.url = None

        msg = _make_message("", guild=guild)
        msg.embeds = [embed]
        msg.channel.guild = guild

        html = self._export([msg], "embed_mention.html", channel=channel, guild=guild)
        self.assertIsNotNone(html)
        # The mention should appear as a mention span, not as raw escaped HTML
        self.assertIn('class="mention"', html)
        self.assertIn("TestUser", html)

    def test_all_mentions_and_timestamps(self):
        """Test that all mention types and timestamps render correctly in a full export."""
        # Mock role
        role = MagicMock(spec=discord.Role)
        role.id = 111
        role.name = "TestRole"
        role.color.r, role.color.g, role.color.b = 255, 0, 0
        
        # Mock channel
        channel_mention = MagicMock(spec=discord.TextChannel)
        channel_mention.id = 222
        channel_mention.name = "mentioned-channel"
        
        # Mock member
        member = MagicMock(spec=discord.Member)
        member.id = 333
        member.display_name = "MentionedUser"
        member.display_avatar = None
        member.display_icon = None
        member.top_role = None
        member.colour = "#FFFFFF"
        
        guild = _make_guild()
        guild.get_role.side_effect = lambda id: role if id == 111 else None
        guild.get_channel.side_effect = lambda id: channel_mention if id == 222 else None
        guild.get_member.side_effect = lambda id: member if id == 333 else None

        content = (
            "Role: <@&111>\n"
            "Channel: <#222>\n"
            "User: <@333>\n"
            "Everyone: @everyone\n"
            "Here: @here\n"
            "Timestamp: <t:1614556800:f>"
        )
        msg = _make_message(content, guild=guild)
        html = self._export([msg], "all_mentions.html", guild=guild)
        
        self.assertIn("@TestRole", html)
        self.assertIn("color: #ff0000", html)
        self.assertIn("#mentioned-channel", html)
        self.assertIn("@MentionedUser", html)
        self.assertIn("@everyone", html)
        self.assertIn("@here", html)
        self.assertIn("unix-timestamp", html)

    def test_complex_embed_rendering(self):
        """Test a very complex embed with all fields populated."""
        guild = _make_guild()
        member = MagicMock(spec=discord.Member)
        member.id = 123
        member.display_name = "EmbedExpert"
        member.display_avatar = None
        member.display_icon = None
        member.top_role = None
        member.colour = "#FF5733"
        guild.get_member.return_value = member

        embed = _make_embed(
            title="Complex Title",
            description="This is a description with a mention <@123> and a link [Google](https://google.com)",
            colour=0x00FF00,
            fields=[
                {"name": "Field 1", "value": "Value 1", "inline": True},
                {"name": "Field 2", "value": "Value 2", "inline": True},
                {"name": "Field 3", "value": "Value 3", "inline": False},
            ],
            author_name="Author Name",
            author_icon="https://mahto.id/assets/me.png",
            author_url="https://mahto.id/assets/me.png",
            footer_text="Footer Text",
            footer_icon="https://mahto.id/assets/me.png",
            image_url="https://mahto.id/assets/me.png",
            thumbnail_url="https://mahto.id/assets/me.png",
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=pytz.utc),
            url="https://mahto.id/assets/me.png",
        )

        msg = _make_message("Message with complex embed", guild=guild)
        msg.embeds = [embed]
        html = self._export([msg], "complex_embed.html", guild=guild)

        self.assertIn("Complex Title", html)
        self.assertIn("@EmbedExpert", html)
        self.assertIn("Value 1", html)
        self.assertIn("Value 3", html)
        self.assertIn("Author Name", html)
        self.assertIn("Footer Text", html)
        self.assertIn("https://mahto.id/assets/me.png", html)
        self.assertIn("https://mahto.id/assets/me.png", html)

    def test_message_with_multiple_embeds_and_attachments(self):
        """Test a message that has multiple embeds and multiple attachments."""
        guild = _make_guild()
        
        embed1 = _make_embed(title="Embed 1", description="Description 1")
        embed2 = _make_embed(title="Embed 2", description="Description 2")
        
        att1 = MagicMock(spec=discord.Attachment)
        att1.url = "https://mahto.id/assets/me.png"
        att1.proxy_url = "https://mahto.id/assets/me.png"
        att1.filename = "file1.png"
        att1.size = 1048576
        att1.content_type = "image/png"
        att1.is_spoiler.return_value = False
        
        att2 = MagicMock(spec=discord.Attachment)
        att2.url = "https://mahto.id/assets/me.png"
        att2.proxy_url = "https://mahto.id/assets/me.png"
        att2.filename = "file2.txt"
        att2.size = 1024
        att2.content_type = "text/plain"
        att2.is_spoiler.return_value = False
        
        msg = _make_message("Multiple things here", guild=guild)
        msg.embeds = [embed1, embed2]
        msg.attachments = [att1, att2]
        
        html = self._export([msg], "multiple_things.html", guild=guild)
        
        self.assertIn("Embed 1", html)
        self.assertIn("Embed 2", html)
        self.assertIn("https://mahto.id/assets/me.png", html)
        self.assertIn("file2.txt", html)

    def test_image_spoiler(self):
        """An image marked as a spoiler should have the spoiler CSS class."""
        guild = _make_guild()
        
        att = MagicMock(spec=discord.Attachment)
        att.url = "https://mahto.id/assets/me.png"
        att.proxy_url = "https://mahto.id/assets/me.png"
        att.filename = "SPOILER_file.png"
        att.size = 100
        att.content_type = "image/png"
        att.is_spoiler.return_value = True
        
        msg = _make_message("", guild=guild)
        msg.attachments = [att]
        
        html = self._export([msg], "image_spoiler.html", guild=guild)
        
        self.assertIn("chatlog__attachment-spoiler", html)
        self.assertIn("SPOILER", html)

    def test_image_grid_2(self):
        """Two consecutive images should be rendered in a 1x2 grid."""
        guild = _make_guild()
        
        att1 = MagicMock(spec=discord.Attachment)
        att1.url = "https://mahto.id/assets/me.png"
        att1.proxy_url = "https://mahto.id/assets/me.png"
        att1.filename = "img1.png"
        att1.size = 100
        att1.content_type = "image/png"
        att1.is_spoiler.return_value = False
        
        att2 = MagicMock(spec=discord.Attachment)
        att2.url = "https://mahto.id/assets/me.png"
        att2.proxy_url = "https://mahto.id/assets/me.png"
        att2.filename = "img2.png"
        att2.size = 100
        att2.content_type = "image/png"
        att2.is_spoiler.return_value = False
        
        msg = _make_message("", guild=guild)
        msg.attachments = [att1, att2]
        
        html = self._export([msg], "image_grid_2.html", guild=guild)
        
        self.assertIn("chatlog__attachment-grid--1x2", html)
        self.assertIn("https://mahto.id/assets/me.png", html)

    def test_image_grid_3(self):
        """Three consecutive images should be rendered in a 1x3 grid."""
        guild = _make_guild()
        attachments = []
        for i in range(3):
            att = MagicMock(spec=discord.Attachment)
            att.url = "https://mahto.id/assets/me.png"
            att.proxy_url = "https://mahto.id/assets/me.png"
            att.filename = f"img{i}.png"
            att.size = 100
            att.content_type = "image/png"
            att.is_spoiler.return_value = False
            attachments.append(att)
            
        msg = _make_message("", guild=guild)
        msg.attachments = attachments
        
        html = self._export([msg], "image_grid_3.html", guild=guild)
        
        self.assertIn("chatlog__attachment-grid--1x3", html)
        self.assertIn("https://mahto.id/assets/me.png", html)

    def test_image_grid_4(self):
        """Four consecutive images should be rendered in a 2x2 grid."""
        guild = _make_guild()
        attachments = []
        for i in range(4):
            att = MagicMock(spec=discord.Attachment)
            att.url = "https://mahto.id/assets/me.png"
            att.proxy_url = "https://mahto.id/assets/me.png"
            att.filename = f"img{i}.png"
            att.size = 100
            att.content_type = "image/png"
            att.is_spoiler.return_value = False
            attachments.append(att)
            
        msg = _make_message("", guild=guild)
        msg.attachments = attachments
        
        html = self._export([msg], "image_grid_4.html", guild=guild)
        
        self.assertIn("chatlog__attachment-grid--2x2", html)
        self.assertIn("https://mahto.id/assets/me.png", html)

    def test_image_grid_5(self):
        """Five consecutive images should be split into 1x2 and 1x3 grids."""
        guild = _make_guild()
        attachments = []
        for i in range(5):
            att = MagicMock(spec=discord.Attachment)
            att.url = "https://mahto.id/assets/me.png"
            att.proxy_url = "https://mahto.id/assets/me.png"
            att.filename = f"img{i}.png"
            att.size = 100
            att.content_type = "image/png"
            att.is_spoiler.return_value = False
            attachments.append(att)

        msg = _make_message("", guild=guild)
        msg.attachments = attachments

        html = self._export([msg], "image_grid_5.html", guild=guild)

        self.assertIn("chatlog__attachment-grid--1x2", html)
        self.assertIn("chatlog__attachment-grid--1x3", html)
        self.assertIn("https://mahto.id/assets/me.png", html)

    def test_image_grid_10(self):
        """Ten consecutive images should be split into 1x1 and 3x3 grids."""
        guild = _make_guild()
        attachments = []
        for i in range(10):
            att = MagicMock(spec=discord.Attachment)
            att.url = "https://mahto.id/assets/me.png"
            att.proxy_url = "https://mahto.id/assets/me.png"
            att.filename = f"img{i}.png"
            att.size = 100
            att.content_type = "image/png"
            att.is_spoiler.return_value = False
            attachments.append(att)

        msg = _make_message("", guild=guild)
        msg.attachments = attachments

        html = self._export([msg], "image_grid_10.html", guild=guild)

        self.assertIn("chatlog__attachment-grid--1x1", html)
        self.assertIn("chatlog__attachment-grid--3x3", html)
        self.assertIn("https://mahto.id/assets/me.png", html)

    def test_grid_width_restriction(self):
        """The grid should have a max-width restriction."""
        guild = _make_guild()
        att = MagicMock(spec=discord.Attachment)
        att.url = "https://mahto.id/assets/me.png"
        att.proxy_url = "https://mahto.id/assets/me.png"
        att.filename = "img1.png"
        att.size = 100
        att.content_type = "image/png"
        att.is_spoiler.return_value = False

        msg = _make_message("", guild=guild)
        msg.attachments = [att, att] # 2 images for a grid

        html = self._export([msg], "grid_width.html", guild=guild)

        self.assertIn("max-width: 550px", html)
