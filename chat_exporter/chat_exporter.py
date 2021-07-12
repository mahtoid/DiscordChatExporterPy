import io
import re
from pytz import timezone
from PIL import ImageColor
from datetime import timedelta
from dataclasses import dataclass

from typing import Optional, List

import discord
import sys
import traceback
import html

from chat_exporter.build_embed import BuildEmbed
from chat_exporter.build_attachments import BuildAttachment
from chat_exporter.build_reaction import BuildReaction
from chat_exporter.build_html import fill_out, start_message, bot_tag, message_reference, message_reference_unknown, \
    message_content, message_body, end_message, total, PARSE_MODE_NONE, PARSE_MODE_MARKDOWN, PARSE_MODE_REFERENCE, \
    img_attachment
from chat_exporter.parse_mention import pass_bot


bot = None


def init_exporter(_bot):
    global bot
    bot = _bot
    pass_bot(bot)


async def export(channel: discord.TextChannel, limit: int = None, set_timezone="Europe/London"):
    # noinspection PyBroadException
    try:
        return (await Transcript.export(channel, limit, set_timezone)).html
    except Exception:
        traceback.print_exc()
        print(f"Please send a screenshot of the above error to https://www.github.com/mahtoid/DiscordChatExporterPy")


async def raw_export(channel: discord.TextChannel, messages: List[discord.Message],
                     set_timezone: str = "Europe/London"):
    # noinspection PyBroadException
    try:
        return (await Transcript.raw_export(channel, messages, set_timezone)).html
    except Exception:
        traceback.print_exc()
        print(f"Please send a screenshot of the above error to https://www.github.com/mahtoid/DiscordChatExporterPy")


async def quick_export(ctx):
    # noinspection PyBroadException
    try:
        transcript = await Transcript.export(ctx.channel, None, "Europe/London")
    except Exception:
        print("Error during transcript generation!", file=sys.stderr)
        traceback.print_exc()
        error_embed = discord.Embed(
            title="Transcript Generation Failed!",
            description="Whoops! We've stumbled in to an issue here.",
            colour=discord.Colour.red()
        )
        await ctx.channel.send(embed=error_embed)
        print(f"Please send a screenshot of the above error to https://www.github.com/mahtoid/DiscordChatExporterPy")
        return

    async for m in ctx.channel.history(limit=None):
        try:
            for f in m.attachments:
                if f"transcript-{ctx.channel.name}.html" in f.filename:
                    await m.delete()
        except TypeError:
            continue

    # Save transcript
    transcript_embed = discord.Embed(
        description=f"**Transcript Name:** transcript-{ctx.channel.name}\n\n"
                    f"{ctx.author.mention} requested a transcript of the channel",
        colour=discord.Colour.blurple()
    )

    transcript_file = discord.File(io.BytesIO(transcript.html.encode()),
                                   filename=f"transcript-{ctx.channel.name}.html")

    await ctx.send(embed=transcript_embed, file=transcript_file)


@dataclass
class Transcript:
    guild: discord.Guild
    channel: discord.TextChannel
    messages: List[discord.Message]
    timezone_string: str
    html: Optional[str] = None

    @classmethod
    async def export(cls, channel: discord.TextChannel, limit, timezone_string: str = "Europe/London") -> "Transcript":
        if limit:
            messages = await channel.history(limit=limit).flatten()
            messages.reverse()
        else:
            messages = await channel.history(limit=limit, oldest_first=True).flatten()
        transcript = await Transcript(channel=channel, guild=channel.guild, messages=messages,
                                      timezone_string=timezone(timezone_string))\
            .build_transcript()
        return transcript

    @classmethod
    async def raw_export(cls, channel: discord.TextChannel, messages: List[discord.Message],
                         timezone_string: str = 'Europe/London') -> "Transcript":
        messages.reverse()
        transcript = await Transcript(channel=channel, guild=channel.guild, messages=messages,
                                      timezone_string=timezone(timezone_string))\
            .build_transcript()
        return transcript

    async def build_transcript(self):
        previous_message = None
        message_html = ""

        for m in self.messages:
            message_html += await Message(m, previous_message, self.timezone_string).build_message()
            previous_message = m

        await self.build_guild(message_html)

        return self

    async def build_guild(self, message_html):

        # TODO: Improve 2.0.0a support
        try:
            guild_icon = self.guild.icon_url
        except AttributeError:
            guild_icon = self.guild.icon

        if not guild_icon or len(guild_icon) < 2:
            guild_icon = "https://discord.com/assets/1f0bfc0865d324c2587920a7d80c609b.png"
        guild_name = html.escape(self.guild.name)
        self.html = await fill_out(self.guild, total, [
            ("SERVER_NAME", f"Guild: {guild_name}"),
            ("SERVER_AVATAR_URL", str(guild_icon), PARSE_MODE_NONE),
            ("CHANNEL_NAME", f"Channel: {self.channel.name}"),
            ("MESSAGE_COUNT", str(len(self.messages))),
            ("MESSAGES", message_html, PARSE_MODE_NONE),
            ("TIMEZONE", str(self.timezone_string)),
        ])


class Message:
    message: discord.Message
    previous_message: discord.Message

    message_html: str = ""
    embeds: str = ""
    attachments: str = ""
    reactions: str = ""

    bot_tag: Optional[str] = None

    transcript: Optional[str] = None
    user_colour: Optional[str] = None

    previous_author: Optional[int] = None
    previous_timestamp: Optional[int] = None
    time_string_create: Optional[str] = None
    time_string_edited: Optional[str] = None

    time_format = "%b %d, %Y %I:%M %p"
    utc = timezone("UTC")

    def __init__(self, message, previous_message, timezone_string):
        self.message = message
        self.previous_message = previous_message
        self.timezone = timezone_string
        self.guild = message.guild

        self.time_string_create, self.time_string_edit = self.set_time(message)

    async def build_message(self):
        self.message.content = html.escape(self.message.content)
        self.message.content = re.sub(r"\n", "<br>", self.message.content)

        await self.build_content()
        await self.build_reference()
        await self.build_sticker()

        for e in self.message.embeds:
            self.embeds += await BuildEmbed(e, self.guild).flow()

        for a in self.message.attachments:
            self.attachments += await BuildAttachment(a, self.guild).flow()

        for r in self.message.reactions:
            self.reactions += await BuildReaction(r, self.guild).flow()

        if self.reactions:
            self.reactions = f'<div class="chatlog__reactions">{self.reactions}</div>'

        await self.generate_message_divider()

        self.message_html += await fill_out(self.guild, message_body, [
            ("MESSAGE_ID", str(self.message.id)),
            ("MESSAGE_CONTENT", self.message.content, PARSE_MODE_NONE),
            ("EMBEDS", self.embeds, PARSE_MODE_NONE),
            ("ATTACHMENTS", self.attachments, PARSE_MODE_NONE),
            ("EMOJI", self.reactions, PARSE_MODE_NONE)
        ])

        return self.message_html

    async def generate_message_divider(self):
        if self.previous_message is None or self.message.reference != "" or \
                self.previous_message.author.id != self.message.author.id or \
                self.message.created_at > (self.previous_message.created_at + timedelta(minutes=4)):

            if self.previous_message is not None:
                self.message_html += await fill_out(self.guild, end_message, [])

            user_colour = self.user_colour_translate(self.guild, self.message.author)

            is_bot = self.check_if_bot(self.message)

            # TODO: Improve 2.0.0a support
            try:
                avatar_url = str(self.message.author.avatar_url)
            except AttributeError:
                avatar_url = str(self.message.author.avatar)

            self.message_html += await fill_out(self.guild, start_message, [
                ("REFERENCE", self.message.reference, PARSE_MODE_NONE),
                ("AVATAR_URL", avatar_url, PARSE_MODE_NONE),
                ("NAME_TAG", "%s#%s" % (self.message.author.name, self.message.author.discriminator), PARSE_MODE_NONE),
                ("USER_ID", str(self.message.author.id)),
                ("USER_COLOUR", user_colour),
                ("NAME", str(html.escape(self.message.author.display_name))),
                ("BOT_TAG", is_bot, PARSE_MODE_NONE),
                ("TIMESTAMP", self.time_string_create),
            ])

    async def build_content(self):
        if not self.message.content:
            self.message.content = ""
            return

        if self.time_string_edit != "":
            self.time_string_edit = f'<span class="chatlog__edited-timestamp" title="{self.time_string_edit}">' \
                                    f'(edited)</span>'

        self.message.content = await fill_out(self.guild, message_content, [
            ("MESSAGE_CONTENT", self.message.content, PARSE_MODE_MARKDOWN),
            ("EDIT", self.time_string_edit, PARSE_MODE_NONE)
        ])

    async def build_sticker(self):
        if not self.message.stickers:
            return

        # TODO: Improve 2.0.0a support (P.S. Stickers don't work for v2 yet)
        try:
            sticker_image_url = self.message.stickers[0].image_url
        except AttributeError:
            sticker_image_url = self.message.stickers[0].image

        if sticker_image_url is None:
            sticker_image_url = (
                f"https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/stickers/"
                f"{self.message.stickers[0].pack_id}/{self.message.stickers[0].id}.gif"
            )

        self.message.content = await fill_out(self.guild, img_attachment, [
            ("ATTACH_URL", str(sticker_image_url), PARSE_MODE_NONE),
            ("ATTACH_URL_THUMB", str(sticker_image_url), PARSE_MODE_NONE)
        ])

    async def build_reference(self):
        if not self.message.reference:
            self.message.reference = ""
            return

        try:
            message: discord.Message = await self.message.channel.fetch_message(self.message.reference.message_id)
        except discord.NotFound:
            self.message.reference = message_reference_unknown
            return

        is_bot = self.check_if_bot(message)
        user_colour = self.user_colour_translate(self.guild, message.author)

        if not message.content:
            message.content = "Click to see attachment"

        if message.embeds or message.attachments:
            attachment_icon = \
                '<img class="chatlog__reference-icon" ' \
                'src="https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/discord-attachment.svg">'
        else:
            attachment_icon = ""

        _, time_string_edit = self.set_time(message)

        if time_string_edit != "":
            time_string_edit = f'<span class="chatlog__reference-edited-timestamp" title="{time_string_edit}">(edited)'\
                               f'</span>'

        self.message.reference = await fill_out(self.guild, message_reference, [
            ("AVATAR_URL", str(message.author.avatar_url), PARSE_MODE_NONE),
            ("BOT_TAG", is_bot, PARSE_MODE_NONE),
            ("NAME_TAG", "%s#%s" % (message.author.name, message.author.discriminator), PARSE_MODE_NONE),
            ("NAME", str(html.escape(message.author.display_name))),
            ("USER_COLOUR", user_colour, PARSE_MODE_NONE),
            ("CONTENT", message.content, PARSE_MODE_REFERENCE),
            ("EDIT", time_string_edit, PARSE_MODE_NONE),
            ("ATTACHMENT_ICON", attachment_icon, PARSE_MODE_NONE),
            ("MESSAGE_ID", str(self.message.reference.message_id), PARSE_MODE_NONE)
        ])

    @staticmethod
    def check_if_bot(message):
        if message.author.bot:
            return bot_tag
        else:
            return ""

    @staticmethod
    def user_colour_translate(guild, author):
        try:
            member = guild.get_member(author.id)
        except discord.NotFound:
            member = author

        if member is not None:
            user_colour = member.colour
            if '#000000' in str(user_colour):
                user_colour = f"color: #%02x%02x%02x;" % (255, 255, 255)
            else:
                user_colour = ImageColor.getrgb(str(user_colour))
                colour_r, colour_g, colour_b = user_colour
                user_colour = f"color: #%02x%02x%02x;" % (colour_r, colour_g, colour_b)
        else:
            user_colour = f"color: #%02x%02x%02x;" % (255, 255, 255)

        return user_colour

    def set_time(self, message):
        created_at = message.created_at.replace(tzinfo=None)
        time_string = self.utc.localize(created_at).astimezone(self.timezone)
        time_string_created = time_string.strftime(self.time_format)
        if message.edited_at is not None:
            edited_at = message.edited_at.replace(tzinfo=None)
            time_string_edited = self.utc.localize(edited_at).astimezone(self.timezone)
            time_string_edited = time_string_edited.strftime(self.time_format)
            time_string_edited = "%s" % time_string_edited
        else:
            time_string_edited = ""

        return time_string_created, time_string_edited
