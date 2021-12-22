import html
from typing import List, Optional

from pytz import timezone
from datetime import timedelta

from chat_exporter.ext.discord_import import discord

from chat_exporter.construct.assets import Attachment, Component, Embed, Reaction
from chat_exporter.ext.discord_utils import DiscordUtils
from chat_exporter.ext.html_generator import (
    fill_out,
    bot_tag,
    message_body,
    message_pin,
    message_thread,
    message_content,
    message_reference,
    message_reference_unknown,
    img_attachment,
    start_message,
    end_message,
    PARSE_MODE_NONE,
    PARSE_MODE_MARKDOWN,
    PARSE_MODE_REFERENCE,
)


def _gather_user_bot(author: discord.Member):
    return bot_tag if author.bot else ""


def _set_edit_at(message_edited_at):
    return f'<span class="chatlog__reference-edited-timestamp" title="{message_edited_at}">(edited)</span>'


class MessageConstruct:
    message_html: str = ""

    # Asset Types
    embeds: str = ""
    reactions: str = ""
    components: str = ""
    attachments: str = ""

    def __init__(
        self,
        message: discord.Message,
        previous_message: Optional[discord.Message],
        pytz_timezone,
        guild: discord.Guild,
    ):
        self.message = message
        self.previous_message = previous_message
        self.pytz_timezone = pytz_timezone
        self.guild = guild
        self.message_created_at, self.message_edited_at = self.set_time()

    async def construct_message(
        self,
    ) -> str:
        if self.message.type == "pins_added":
            await self.build_pin()
        elif self.message.type == "thread_created":
            await self.build_thread()
        else:
            await self.build_message()
        return self.message_html

    async def build_message(self):
        await self.build_content()
        await self.build_reference()
        await self.build_sticker()
        await self.build_assets()
        await self.build_message_template()

    async def build_pin(self):
        await self.generate_message_divider(channel_audit=True)
        await self.build_pin_template()

    async def build_thread(self):
        await self.generate_message_divider(channel_audit=True)
        await self.build_thread_template()

    async def build_content(self):
        if not self.message.content:
            self.message.content = ""
            return

        if self.message_edited_at:
            self.message_edited_at = _set_edit_at(self.message_edited_at)

        self.message.content = await fill_out(self.guild, message_content, [
            ("MESSAGE_CONTENT", self.message.content, PARSE_MODE_MARKDOWN),
            ("EDIT", self.message_edited_at, PARSE_MODE_NONE)
        ])

    async def build_reference(self):
        if not self.message.reference:
            self.message.reference = ""
            return

        try:
            message: discord.Message = await self.message.channel.fetch_message(self.message.reference.message_id)
        except (discord.NotFound, discord.HTTPException) as e:
            self.message.reference = ""
            if isinstance(e, discord.NotFound):
                self.message.reference = message_reference_unknown
            return

        is_bot = _gather_user_bot(message.author)
        user_colour = await self._gather_user_colour(message.author)

        if not message.content:
            message.content = "Click to see attachment"

        attachment_icon = DiscordUtils.reference_attachment_icon if message.embeds or message.attachments else ""

        _, message_edited_at = self.set_time(message)

        if message_edited_at:
            message_edited_at = _set_edit_at(message_edited_at)

        avatar_url = self.message.author.avatar if self.message.author.avatar else DiscordUtils.default_avatar

        self.message.reference = await fill_out(self.guild, message_reference, [
            ("AVATAR_URL", str(avatar_url), PARSE_MODE_NONE),
            ("BOT_TAG", is_bot, PARSE_MODE_NONE),
            ("NAME_TAG", "%s#%s" % (message.author.name, message.author.discriminator), PARSE_MODE_NONE),
            ("NAME", str(html.escape(message.author.display_name))),
            ("USER_COLOUR", user_colour, PARSE_MODE_NONE),
            ("CONTENT", message.content, PARSE_MODE_REFERENCE),
            ("EDIT", message_edited_at, PARSE_MODE_NONE),
            ("ATTACHMENT_ICON", attachment_icon, PARSE_MODE_NONE),
            ("MESSAGE_ID", str(self.message.reference.message_id), PARSE_MODE_NONE)
        ])

    async def build_sticker(self):
        if not self.message.stickers or not hasattr(self.message.stickers[0], "url"):
            return

        sticker_image_url = self.message.stickers[0].url

        if sticker_image_url.endswith(".json"):
            sticker = await self.message.stickers[0].fetch()
            sticker_image_url = (
                f"https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/stickers/{sticker.pack_id}/{sticker.id}.gif"
            )

        self.message.content = await fill_out(self.guild, img_attachment, [
            ("ATTACH_URL", str(sticker_image_url), PARSE_MODE_NONE),
            ("ATTACH_URL_THUMB", str(sticker_image_url), PARSE_MODE_NONE)
        ])

    async def build_assets(self):
        for e in self.message.embeds:
            self.embeds += await Embed(e, self.guild).flow()

        for a in self.message.attachments:
            self.attachments += await Attachment(a, self.guild).flow()

        for c in self.message.components:
            self.components += await Component(c, self.guild).flow()

        for r in self.message.reactions:
            self.reactions += await Reaction(r, self.guild).flow()

        if self.reactions:
            self.reactions = f'<div class="chatlog__reactions">{self.reactions}</div>'

        if self.components:
            self.components = f'<div class="chatlog__components">{self.components}</div>'

    async def build_message_template(self):
        await self.generate_message_divider()

        self.message_html += await fill_out(self.guild, message_body, [
            ("MESSAGE_ID", str(self.message.id)),
            ("MESSAGE_CONTENT", self.message.content, PARSE_MODE_NONE),
            ("EMBEDS", self.embeds, PARSE_MODE_NONE),
            ("ATTACHMENTS", self.attachments, PARSE_MODE_NONE),
            ("COMPONENTS", self.components, PARSE_MODE_NONE),
            ("EMOJI", self.reactions, PARSE_MODE_NONE)
        ])

        return self.message_html

    def _generate_message_divider_check(self):
        return bool(
            self.previous_message is None or self.message.reference != "" or
            self.previous_message.author.id != self.message.author.id or self.message.webhook_id is not None or
            self.message.created_at > (self.previous_message.created_at + timedelta(minutes=4))
        )

    async def generate_message_divider(self, channel_audit=False):
        if channel_audit or self._generate_message_divider_check():
            if self.previous_message is not None:
                self.message_html += await fill_out(self.guild, end_message, [])

            if channel_audit:
                return

            user_colour = await self._gather_user_colour(self.message.author)
            is_bot = _gather_user_bot(self.message.author)
            avatar_url = self.message.author.avatar if self.message.author.avatar else DiscordUtils.default_avatar

            self.message_html += await fill_out(self.guild, start_message, [
                ("REFERENCE", self.message.reference, PARSE_MODE_NONE),
                ("AVATAR_URL", str(avatar_url), PARSE_MODE_NONE),
                ("NAME_TAG", "%s#%s" % (self.message.author.name, self.message.author.discriminator), PARSE_MODE_NONE),
                ("USER_ID", str(self.message.author.id)),
                ("USER_COLOUR", str(user_colour)),
                ("NAME", str(html.escape(self.message.author.display_name))),
                ("BOT_TAG", str(is_bot), PARSE_MODE_NONE),
                ("TIMESTAMP", str(self.message_created_at)),
            ])

    async def build_pin_template(self):
        self.message_html += await fill_out(self.guild, message_pin, [
            ("PIN_URL", DiscordUtils.pinned_message_icon, PARSE_MODE_NONE),
            ("USER_COLOUR", await self._gather_user_colour(self.message.author)),
            ("NAME", str(html.escape(self.message.author.display_name))),
            ("NAME_TAG", "%s#%s" % (self.message.author.name, self.message.author.discriminator), PARSE_MODE_NONE),
            ("MESSAGE_ID", str(self.message.id), PARSE_MODE_NONE),
            ("REF_MESSAGE_ID", str(self.message.reference.message_id), PARSE_MODE_NONE)
        ])

    async def build_thread_template(self):
        self.message_html += await fill_out(self.guild, message_thread, [
            ("THREAD_URL", DiscordUtils.thread_channel_icon,
             PARSE_MODE_NONE),
            ("THREAD_NAME", self.message.content, PARSE_MODE_NONE),
            ("USER_COLOUR", await self._gather_user_colour(self.message.author)),
            ("NAME", str(html.escape(self.message.author.display_name))),
            ("NAME_TAG", "%s#%s" % (self.message.author.name, self.message.author.discriminator), PARSE_MODE_NONE),
            ("MESSAGE_ID", str(self.message.id), PARSE_MODE_NONE),
        ])

    async def _gather_user_colour(self, author: discord.Member):
        member = self.guild.get_member(author.id)
        if not member:
            try:
                member = await self.guild.fetch_member(author.id)
            except Exception:
                # This is disgusting, but has to be done for NextCord
                member = None
        user_colour = member.colour if member and str(member.colour) != "#000000" else "#FFFFFF"
        return f"color: {user_colour};"

    def set_time(self, message: Optional[discord.Message] = None):
        message = message if message else self.message
        created_at_str = self.to_local_time_str(message.created_at)
        edited_at_str = self.to_local_time_str(message.edited_at) if message.edited_at else ""

        return created_at_str, edited_at_str

    def to_local_time_str(self, time):
        if not self.message.created_at.tzinfo:
            time = timezone("UTC").localize(time)

        local_time = time.astimezone(timezone(self.pytz_timezone))
        return local_time.strftime("%b %d, %Y %I:%M %p")


class Message:
    def __init__(
        self,
        messages: List[discord.Message],
        guild: discord.Guild,
        pytz_timezone,
    ):
        self.messages = messages
        self.guild = guild
        self.pytz_timezone = pytz_timezone

    async def gather(self) -> str:
        message_html: str = ""
        previous_message: Optional[discord.Message] = None

        for message in self.messages:
            message_html += await MessageConstruct(
                message,
                previous_message,
                self.pytz_timezone,
                self.guild
            ).construct_message()

            previous_message = message
        return message_html
