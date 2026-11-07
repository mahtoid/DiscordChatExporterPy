import asyncio
import html
import logging
import os
import re
import shutil
import tempfile
from collections import OrderedDict
from datetime import datetime
from typing import Callable, List, Optional

import pytz

from chat_exporter.construct.attachment_handler import AttachmentHandler
from chat_exporter.construct.message import MessageConstruct, gather_messages, resolve_thread_starter
from chat_exporter.ext.discord_import import discord
from chat_exporter.ext.discord_utils import DiscordUtils
from chat_exporter.ext.export_context import export_scope
from chat_exporter.ext.html_generator import (
    PARSE_MODE_HTML_SAFE,
    PARSE_MODE_NONE,
    PARSE_MODE_TEXT,
    PARSE_MODE_URL,
    channel_subject,
    channel_topic,
    fancy_time,
    fill_out,
    meta_data_temp,
    total,
)

log = logging.getLogger("chat_exporter")

# The page is rendered around the messages, so a streamed export can write them in between from disk.
_PAGE_HEAD, _PAGE_TAIL = total.split("{{MESSAGES}}", 1)

# Replies usually point at recent messages; older ones are fetched from the API on demand.
RECENT_MESSAGES_KEPT = 500


class TranscriptDAO:
    html: str

    def __init__(
        self,
        channel: discord.TextChannel,
        limit: Optional[int],
        messages: Optional[List[discord.Message]],
        pytz_timezone,
        military_time: bool,
        fancy_times: bool,
        before: Optional[datetime],
        after: Optional[datetime],
        support_dev: bool,
        bot: Optional[discord.Client],
        attachment_handler: Optional[AttachmentHandler],
        raise_exceptions: bool = False,
        fetch_reactors: bool = True,
    ):
        self.channel = channel
        self.messages = messages
        self.limit = int(limit) if limit else None
        self.military_time = military_time
        self.fancy_times = fancy_times
        self.before = before
        self.after = after
        self.support_dev = support_dev
        self.pytz_timezone = pytz_timezone
        self.attachment_handler = attachment_handler
        self.raise_exceptions = raise_exceptions
        self.fetch_reactors = fetch_reactors
        self.bot = bot

    async def build_transcript(self):
        async with export_scope(self.pytz_timezone, self.bot):
            message_html, meta_data = await gather_messages(
                self.messages, self.channel.guild, self.pytz_timezone, self.military_time, self.attachment_handler,
                self.fetch_reactors
            )
            await self.export_transcript(message_html, meta_data)
        return self

    async def export_transcript(self, message_html: str, meta_data: dict):
        head, tail = await self._render_page(meta_data, len(self.messages))
        self.html = head + message_html.strip() + tail

    async def _render_page(self, meta_data: dict, message_count: int):
        guild_icon = (
            self.channel.guild.icon
            if (self.channel.guild.icon and len(self.channel.guild.icon) > 2)
            else DiscordUtils.default_avatar
        )

        guild_name = self.channel.guild.name

        timezone = pytz.timezone(self.pytz_timezone)
        if self.military_time:
            time_now = datetime.now(timezone).strftime("%e %B %Y at %H:%M:%S (%Z)")
        else:
            time_now = datetime.now(timezone).strftime("%e %B %Y at %I:%M:%S %p (%Z)")

        meta_data_html_chunks: List[str] = []
        for data in meta_data:
            creation_time = meta_data[int(data)][1].astimezone(timezone).strftime("%b %d, %Y")
            joined_time = (
                meta_data[int(data)][5].astimezone(timezone).strftime("%b %d, %Y")
                if meta_data[int(data)][5]
                else "Unknown"
            )

            pattern = r"^#\d{4}"
            discrim = str(meta_data[int(data)][0][-5:])
            user = str(meta_data[int(data)][0])

            meta_data_html_chunks.append(
                await fill_out(
                    self.channel.guild,
                    meta_data_temp,
                    [
                        ("USER_ID", str(data), PARSE_MODE_TEXT),
                        ("USERNAME", user[:-5] if re.match(pattern, discrim) else user, PARSE_MODE_TEXT),
                        ("DISCRIMINATOR", discrim if re.match(pattern, discrim) else "", PARSE_MODE_TEXT),
                        ("BOT", str(meta_data[int(data)][2]), PARSE_MODE_NONE),
                        ("CREATED_AT", str(creation_time), PARSE_MODE_TEXT),
                        ("JOINED_AT", str(joined_time), PARSE_MODE_TEXT),
                        ("GUILD_ICON", str(guild_icon), PARSE_MODE_URL),
                        ("DISCORD_ICON", str(DiscordUtils.logo), PARSE_MODE_URL),
                        ("MEMBER_ID", str(data), PARSE_MODE_TEXT),
                        ("USER_AVATAR", str(meta_data[int(data)][3]), PARSE_MODE_URL),
                        ("DISPLAY", str(meta_data[int(data)][6]), PARSE_MODE_NONE),
                        ("MESSAGE_COUNT", str(meta_data[int(data)][4]), PARSE_MODE_TEXT),
                    ],
                )
            )

        meta_data_html = "".join(meta_data_html_chunks)

        if self.military_time:
            channel_creation_time = self.channel.created_at.astimezone(timezone).strftime("%b %d, %Y (%H:%M:%S)")
        else:
            channel_creation_time = self.channel.created_at.astimezone(timezone).strftime("%b %d, %Y (%I:%M:%S %p)")

        raw_channel_topic = (
            self.channel.topic if isinstance(self.channel, discord.TextChannel) and self.channel.topic else ""
        )

        channel_topic_html = ""
        if raw_channel_topic:
            channel_topic_html = await fill_out(
                self.channel.guild, channel_topic, [("CHANNEL_TOPIC", html.escape(raw_channel_topic))]
            )

        limit = "start"
        if self.limit:
            limit = f"latest {self.limit} messages"

        subject = await fill_out(
            self.channel.guild,
            channel_subject,
            [
                ("LIMIT", limit, PARSE_MODE_NONE),
                ("CHANNEL_NAME", self.channel.name, PARSE_MODE_TEXT),
                ("RAW_CHANNEL_TOPIC", html.escape(str(raw_channel_topic))),
            ],
        )

        sd = (
            ('<div class="meta__support">    <a href="https://ko-fi.com/mahtoid">DONATE</a></div>')
            if self.support_dev
            else ""
        )

        _fancy_time = ""

        if self.fancy_times:
            if self.military_time:
                time_format = "HH:mm"
            else:
                time_format = "hh:mm A"

            _fancy_time = await fill_out(
                self.channel.guild,
                fancy_time,
                [("TIME_FORMAT", time_format, PARSE_MODE_NONE), ("TIMEZONE", str(self.pytz_timezone), PARSE_MODE_NONE)],
            )

        replacements = [
            ("SERVER_NAME", guild_name, PARSE_MODE_TEXT),
            ("GUILD_ID", str(self.channel.guild.id), PARSE_MODE_NONE),
            ("SERVER_AVATAR_URL", str(guild_icon), PARSE_MODE_URL),
            ("CHANNEL_NAME", self.channel.name, PARSE_MODE_TEXT),
            ("MESSAGE_COUNT", str(message_count), PARSE_MODE_NONE),
            ("META_DATA", meta_data_html, PARSE_MODE_NONE),
            ("DATE_TIME", str(time_now), PARSE_MODE_TEXT),
            ("SUBJECT", subject, PARSE_MODE_NONE),
            ("CHANNEL_CREATED_AT", str(channel_creation_time), PARSE_MODE_TEXT),
            ("CHANNEL_TOPIC", str(channel_topic_html), PARSE_MODE_NONE),
            ("CHANNEL_ID", str(self.channel.id), PARSE_MODE_NONE),
            ("MESSAGE_PARTICIPANTS", str(len(meta_data)), PARSE_MODE_NONE),
            ("FANCY_TIME", _fancy_time, PARSE_MODE_NONE),
            ("SD", sd, PARSE_MODE_NONE),
            ("SERVER_NAME_SAFE", guild_name, PARSE_MODE_HTML_SAFE),
            ("CHANNEL_NAME_SAFE", self.channel.name, PARSE_MODE_HTML_SAFE),
        ]
        head = await fill_out(self.channel.guild, _PAGE_HEAD, replacements)
        tail = await fill_out(self.channel.guild, _PAGE_TAIL, replacements)
        return head, tail

    async def export_to_file(
        self,
        fp,
        should_stop: Optional[Callable[[], bool]] = None,
        recent_messages: int = RECENT_MESSAGES_KEPT,
    ) -> int:
        """Streams the transcript to `fp` (a path or a binary file object) and returns the message count.

        Only the previous message and the last `recent_messages` messages are kept in memory; the rendered
        messages are written to a temporary file and spliced into the page at the end.
        """
        async with export_scope(self.pytz_timezone, self.bot):
            with tempfile.TemporaryFile("w+b") as body:
                message_count, meta_data = await self._stream_messages(body, should_stop, recent_messages)
                head, tail = await self._render_page(meta_data, message_count)
                body.seek(0)
                await asyncio.to_thread(_write_page, fp, head, body, tail)
        return message_count

    async def _stream_messages(self, body, should_stop, recent_messages):
        guild = self.channel.guild
        meta_data: dict = {}
        recent: OrderedDict = OrderedDict()
        previous_message = None
        message_count = 0

        async for message in self._iter_messages():
            if should_stop is not None and should_stop():
                break

            if message_count == 0:
                message = await resolve_thread_starter(guild, message)

            message_html, meta_data = await MessageConstruct(
                message,
                previous_message,
                self.pytz_timezone,
                self.military_time,
                guild,
                meta_data,
                recent,
                self.attachment_handler,
                self.fetch_reactors,
            ).construct_message()
            if message_count == 0:
                message_html = message_html.lstrip()
            body.write(message_html.encode("utf-8"))

            previous_message = message
            message_count += 1
            recent[message.id] = message
            if len(recent) > recent_messages:
                recent.popitem(last=False)

        if message_count:
            body.write(b"</div>")
        return message_count, meta_data

    async def _iter_messages(self):
        if self.messages is not None:
            if hasattr(self.messages, "__aiter__"):
                async for message in self.messages:
                    yield message
            else:
                for message in self.messages:
                    yield message
            return

        if self.limit is None:
            async for message in self.channel.history(
                limit=None, before=self.before, after=self.after, oldest_first=True
            ):
                yield message
            return

        # A limit means "the latest N messages", which Discord only returns newest-first. N bounds the memory.
        latest = [m async for m in self.channel.history(limit=self.limit, before=self.before, after=self.after)]
        if not self.after:
            latest.reverse()
        for message in latest:
            yield message


def _write_page(fp, head: str, body, tail: str) -> None:
    if isinstance(fp, (str, os.PathLike)):
        with open(fp, "wb") as out:
            _write_page(out, head, body, tail)
        return
    fp.write(head.encode("utf-8"))
    shutil.copyfileobj(body, fp, 1024 * 1024)
    fp.write(tail.encode("utf-8"))


class Transcript(TranscriptDAO):
    async def export(self):
        if not self.messages:
            self.messages = [
                message
                async for message in self.channel.history(
                    limit=self.limit,
                    before=self.before,
                    after=self.after,
                )
            ]

        if not self.after:
            # Don't reverse the caller's list in place.
            self.messages = list(reversed(self.messages))

        try:
            return await super().build_transcript()
        except Exception:
            self.html = "Whoops! Something went wrong..."
            log.exception("Failed to build the transcript for channel %s", getattr(self.channel, "id", "unknown"))
            if self.raise_exceptions:
                raise
            return self
