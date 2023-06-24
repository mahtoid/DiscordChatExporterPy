import datetime
import html
import traceback

import re
from typing import List, Optional

import pytz

from chat_exporter.ext.discord_import import discord

from chat_exporter.construct.message import gather_messages
from chat_exporter.construct.assets.component import Component

from chat_exporter.ext.cache import clear_cache
from chat_exporter.parse.mention import pass_bot
from chat_exporter.ext.discord_utils import DiscordUtils
from chat_exporter.ext.html_generator import (
    fill_out, total, channel_topic, meta_data_temp, fancy_time, channel_subject, PARSE_MODE_NONE
)


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
        before: Optional[datetime.datetime],
        after: Optional[datetime.datetime],
        support_dev: bool,
        bot: Optional[discord.Client],
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

        # This is to pass timezone in to mention.py without rewriting
        setattr(discord.Guild, "timezone", self.pytz_timezone)

        if bot:
            pass_bot(bot)

    async def build_transcript(self):
        message_html, meta_data = await gather_messages(
            self.messages,
            self.channel.guild,
            self.pytz_timezone,
            self.military_time,
        )
        await self.export_transcript(message_html, meta_data)
        clear_cache()
        Component.menu_div_id = 0
        return self

    async def export_transcript(self, message_html: str, meta_data: str):
        guild_icon = self.channel.guild.icon if (
                self.channel.guild.icon and len(self.channel.guild.icon) > 2
        ) else DiscordUtils.default_avatar

        guild_name = html.escape(self.channel.guild.name)

        timezone = pytz.timezone(self.pytz_timezone)
        time_now = datetime.datetime.now(timezone).strftime("%e %B %Y at %T (%Z)")

        meta_data_html: str = ""
        for data in meta_data:
            creation_time = meta_data[int(data)][1].astimezone(timezone).strftime("%b %d, %Y")
            joined_time = (
                meta_data[int(data)][5].astimezone(timezone).strftime("%b %d, %Y")
                if meta_data[int(data)][5] else "Unknown"
            )

            pattern = r'^#\d{4}'
            discrim = str(meta_data[int(data)][0][-5:])
            user = str(meta_data[int(data)][0])

            meta_data_html += await fill_out(self.channel.guild, meta_data_temp, [
                ("USER_ID", str(data), PARSE_MODE_NONE),
                ("USERNAME", user[:-5] if re.match(pattern, discrim) else user, PARSE_MODE_NONE),
                ("DISCRIMINATOR", discrim if re.match(pattern, discrim) else ""),
                ("BOT", str(meta_data[int(data)][2]), PARSE_MODE_NONE),
                ("CREATED_AT", str(creation_time), PARSE_MODE_NONE),
                ("JOINED_AT", str(joined_time), PARSE_MODE_NONE),
                ("GUILD_ICON", str(guild_icon), PARSE_MODE_NONE),
                ("DISCORD_ICON", str(DiscordUtils.logo), PARSE_MODE_NONE),
                ("MEMBER_ID", str(data), PARSE_MODE_NONE),
                ("USER_AVATAR", str(meta_data[int(data)][3]), PARSE_MODE_NONE),
                ("DISPLAY", str(meta_data[int(data)][6]), PARSE_MODE_NONE),
                ("MESSAGE_COUNT", str(meta_data[int(data)][4]))
            ])

        channel_creation_time = self.channel.created_at.astimezone(timezone).strftime("%b %d, %Y (%T)")

        raw_channel_topic = (
            self.channel.topic if isinstance(self.channel, discord.TextChannel) and self.channel.topic else ""
        )

        channel_topic_html = ""
        if raw_channel_topic:
            channel_topic_html = await fill_out(self.channel.guild, channel_topic, [
                ("CHANNEL_TOPIC", html.escape(raw_channel_topic))
            ])

        limit = "start"
        if self.limit:
            limit = f"latest {self.limit} messages"

        subject = await fill_out(self.channel.guild, channel_subject, [
            ("LIMIT", limit, PARSE_MODE_NONE),
            ("CHANNEL_NAME", self.channel.name),
            ("RAW_CHANNEL_TOPIC", str(raw_channel_topic))
        ])

        sd = (
            '<div class="meta__support">'
            '    <a href="https://ko-fi.com/mahtoid">DONATE</a>'
            '</div>'
        ) if self.support_dev else ""

        _fancy_time = ""

        if self.fancy_times:
            _fancy_time = await fill_out(self.channel.guild, fancy_time, [
                ("TIMEZONE", str(self.pytz_timezone), PARSE_MODE_NONE)
            ])

        self.html = await fill_out(self.channel.guild, total, [
            ("SERVER_NAME", f"{guild_name}"),
            ("GUILD_ID", str(self.channel.guild.id), PARSE_MODE_NONE),
            ("SERVER_AVATAR_URL", str(guild_icon), PARSE_MODE_NONE),
            ("CHANNEL_NAME", f"{self.channel.name}"),
            ("MESSAGE_COUNT", str(len(self.messages))),
            ("MESSAGES", message_html, PARSE_MODE_NONE),
            ("META_DATA", meta_data_html, PARSE_MODE_NONE),
            ("DATE_TIME", str(time_now)),
            ("SUBJECT", subject, PARSE_MODE_NONE),
            ("CHANNEL_CREATED_AT", str(channel_creation_time), PARSE_MODE_NONE),
            ("CHANNEL_TOPIC", str(channel_topic_html), PARSE_MODE_NONE),
            ("CHANNEL_ID", str(self.channel.id), PARSE_MODE_NONE),
            ("MESSAGE_PARTICIPANTS", str(len(meta_data)), PARSE_MODE_NONE),
            ("FANCY_TIME", _fancy_time, PARSE_MODE_NONE),
            ("SD", sd, PARSE_MODE_NONE)
        ])


class Transcript(TranscriptDAO):
    async def export(self):
        if not self.messages:
            self.messages = [message async for message in self.channel.history(
                limit=self.limit,
                before=self.before,
                after=self.after,
            )]

        if not self.after:
            self.messages.reverse()

        try:
            return await super().build_transcript()
        except Exception:
            self.html = "Whoops! Something went wrong..."
            traceback.print_exc()
            print("Please send a screenshot of the above error to https://www.github.com/mahtoid/DiscordChatExporterPy")
            return self
