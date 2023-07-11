import html
from typing import List, Optional, Union

from pytz import timezone
from datetime import timedelta

from chat_exporter.ext.discord_import import discord

from chat_exporter.construct.assets import Attachment, Component, Embed, Reaction
from chat_exporter.ext.discord_utils import DiscordUtils
from chat_exporter.ext.discriminator import discriminator
from chat_exporter.ext.html_generator import (
    fill_out,
    bot_tag,
    bot_tag_verified,
    message_body,
    message_pin,
    message_thread,
    message_content,
    message_reference,
    message_reference_unknown,
    message_interaction,
    img_attachment,
    start_message,
    end_message,
    PARSE_MODE_NONE,
    PARSE_MODE_MARKDOWN,
    PARSE_MODE_REFERENCE,
    message_thread_remove,
    message_thread_add,
)


def _gather_user_bot(author: discord.Member):
    if author.bot and author.public_flags.verified_bot:
        return bot_tag_verified
    elif author.bot:
        return bot_tag
    return ""


def _set_edit_at(message_edited_at):
    return f'<span class="chatlog__reference-edited-timestamp" data-timestamp="{message_edited_at}">(edited)</span>'


class MessageConstruct:
    message_html: str = ""

    # Asset Types
    embeds: str = ""
    reactions: str = ""
    components: str = ""
    attachments: str = ""
    time_format: str = ""

    def __init__(
        self,
        message: discord.Message,
        previous_message: Optional[discord.Message],
        pytz_timezone,
        military_time: bool,
        guild: discord.Guild,
        meta_data: dict,
        message_dict: dict
    ):
        self.message = message
        self.previous_message = previous_message
        self.pytz_timezone = pytz_timezone
        self.military_time = military_time
        self.guild = guild
        self.message_dict = message_dict

        self.time_format = "%A, %e %B %Y %I:%M %p"
        if self.military_time:
            self.time_format = "%A, %e %B %Y %H:%M"

        self.message_created_at, self.message_edited_at = self.set_time()
        self.meta_data = meta_data

    async def construct_message(
        self,
    ) -> (str, dict):
        if discord.MessageType.pins_add == self.message.type:
            await self.build_pin()
        elif discord.MessageType.thread_created == self.message.type:
            await self.build_thread()
        elif discord.MessageType.recipient_remove == self.message.type:
            await self.build_thread_remove()
        elif discord.MessageType.recipient_add == self.message.type:
            await self.build_thread_add()
        else:
            await self.build_message()
        return self.message_html, self.meta_data

    async def build_message(self):
        await self.build_content()
        await self.build_reference()
        await self.build_interaction()
        await self.build_sticker()
        await self.build_assets()
        await self.build_message_template()
        await self.build_meta_data()

    async def build_pin(self):
        await self.generate_message_divider(channel_audit=True)
        await self.build_pin_template()

    async def build_thread(self):
        await self.generate_message_divider(channel_audit=True)
        await self.build_thread_template()

    async def build_thread_remove(self):
        await self.generate_message_divider(channel_audit=True)
        await self.build_remove()

    async def build_thread_add(self):
        await self.generate_message_divider(channel_audit=True)
        await self.build_add()

    async def build_meta_data(self):
        user_id = self.message.author.id

        if user_id in self.meta_data:
            self.meta_data[user_id][4] += 1
        else:
            user_name_discriminator = await discriminator(self.message.author.name, self.message.author.discriminator)
            user_created_at = self.message.author.created_at
            user_bot = _gather_user_bot(self.message.author)
            user_avatar = (
                self.message.author.display_avatar if self.message.author.display_avatar
                else DiscordUtils.default_avatar
            )
            user_joined_at = self.message.author.joined_at if hasattr(self.message.author, "joined_at") else None
            user_display_name = (
                f'<div class="meta__display-name">{self.message.author.display_name}</div>'
                if self.message.author.display_name != self.message.author.name
                else ""
            )
            self.meta_data[user_id] = [
                user_name_discriminator, user_created_at, user_bot, user_avatar, 1, user_joined_at, user_display_name
            ]

    async def build_content(self):
        if not self.message.content:
            self.message.content = ""
            return

        if self.message_edited_at:
            self.message_edited_at = _set_edit_at(self.message_edited_at)

        self.message.content = html.escape(self.message.content)
        self.message.content = await fill_out(self.guild, message_content, [
            ("MESSAGE_CONTENT", self.message.content, PARSE_MODE_MARKDOWN),
            ("EDIT", self.message_edited_at, PARSE_MODE_NONE)
        ])

    async def build_reference(self):
        if not self.message.reference:
            self.message.reference = ""
            return

        message: discord.Message = self.message_dict.get(self.message.reference.message_id)

        if not message:
            try:
                message: discord.Message = await self.message.channel.fetch_message(self.message.reference.message_id)
            except (discord.NotFound, discord.HTTPException) as e:
                self.message.reference = ""
                if isinstance(e, discord.NotFound):
                    self.message.reference = message_reference_unknown
                return

        is_bot = _gather_user_bot(message.author)
        user_colour = await self._gather_user_colour(message.author)

        if not message.content and not message.interaction:
            message.content = "Click to see attachment"
        elif not message.content and message.interaction:
            message.content = "Click to see command"

        icon = ""
        if not message.interaction and (message.embeds or message.attachments):
            icon = DiscordUtils.reference_attachment_icon
        elif message.interaction:
            icon = DiscordUtils.interaction_command_icon

        _, message_edited_at = self.set_time(message)

        if message_edited_at:
            message_edited_at = _set_edit_at(message_edited_at)

        avatar_url = message.author.display_avatar if message.author.display_avatar else DiscordUtils.default_avatar
        self.message.reference = await fill_out(self.guild, message_reference, [
            ("AVATAR_URL", str(avatar_url), PARSE_MODE_NONE),
            ("BOT_TAG", is_bot, PARSE_MODE_NONE),
            ("NAME_TAG", await discriminator(message.author.name, message.author.discriminator), PARSE_MODE_NONE),
            ("NAME", str(html.escape(message.author.display_name))),
            ("USER_COLOUR", user_colour, PARSE_MODE_NONE),
            ("CONTENT", message.content.replace("\n", "").replace("<br>", ""), PARSE_MODE_REFERENCE),
            ("EDIT", message_edited_at, PARSE_MODE_NONE),
            ("ICON", icon, PARSE_MODE_NONE),
            ("USER_ID", str(message.author.id), PARSE_MODE_NONE),
            ("MESSAGE_ID", str(self.message.reference.message_id), PARSE_MODE_NONE),
        ])

    async def build_interaction(self):
        if not self.message.interaction:
            self.message.interaction = ""
            return

        user: Union[discord.Member, discord.User] = self.message.interaction.user
        is_bot = _gather_user_bot(user)
        user_colour = await self._gather_user_colour(user)
        avatar_url = user.display_avatar if user.display_avatar else DiscordUtils.default_avatar
        self.message.interaction = await fill_out(self.guild, message_interaction, [
            ("AVATAR_URL", str(avatar_url), PARSE_MODE_NONE),
            ("BOT_TAG", is_bot, PARSE_MODE_NONE),
            ("NAME_TAG", await discriminator(user.name, user.discriminator), PARSE_MODE_NONE),
            ("NAME", str(html.escape(user.display_name))),
            ("USER_COLOUR", user_colour, PARSE_MODE_NONE),
            ("FILLER", "used ", PARSE_MODE_NONE),
            ("COMMAND", "/" + self.message.interaction.name, PARSE_MODE_NONE),
            ("USER_ID", str(user.id), PARSE_MODE_NONE),
            ("INTERACTION_ID", str(self.message.interaction.id), PARSE_MODE_NONE),
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

    async def build_message_template(self):
        started = await self.generate_message_divider()

        if started:
            return self.message_html

        self.message_html += await fill_out(self.guild, message_body, [
            ("MESSAGE_ID", str(self.message.id)),
            ("MESSAGE_CONTENT", self.message.content, PARSE_MODE_NONE),
            ("EMBEDS", self.embeds, PARSE_MODE_NONE),
            ("ATTACHMENTS", self.attachments, PARSE_MODE_NONE),
            ("COMPONENTS", self.components, PARSE_MODE_NONE),
            ("EMOJI", self.reactions, PARSE_MODE_NONE),
            ("TIMESTAMP", self.message_created_at, PARSE_MODE_NONE),
            ("TIME", self.message_created_at.split()[-1], PARSE_MODE_NONE),
        ])

        return self.message_html

    def _generate_message_divider_check(self):
        return bool(
            self.previous_message is None or self.message.reference != "" or
            self.previous_message.type is not discord.MessageType.default or self.message.interaction != "" or
            self.previous_message.author.id != self.message.author.id or self.message.webhook_id is not None or
            self.message.created_at > (self.previous_message.created_at + timedelta(minutes=4))
        )

    async def generate_message_divider(self, channel_audit=False):
        if channel_audit or self._generate_message_divider_check():
            if self.previous_message is not None:
                self.message_html += await fill_out(self.guild, end_message, [])

            if channel_audit:
                self.audit = True
                return

            followup_symbol = ""
            is_bot = _gather_user_bot(self.message.author)
            avatar_url = self.message.author.display_avatar if self.message.author.display_avatar else DiscordUtils.default_avatar

            if self.message.reference != "" or self.message.interaction:
                followup_symbol = "<div class='chatlog__followup-symbol'></div>"

            time = self.message.created_at
            if not self.message.created_at.tzinfo:
                time = timezone("UTC").localize(time)

            default_timestamp = time.astimezone(timezone(self.pytz_timezone)).strftime("%d-%m-%Y %H:%M")

            self.message_html += await fill_out(self.guild, start_message, [
                ("REFERENCE_SYMBOL", followup_symbol, PARSE_MODE_NONE),
                ("REFERENCE", self.message.reference if self.message.reference else self.message.interaction,
                 PARSE_MODE_NONE),
                ("AVATAR_URL", str(avatar_url), PARSE_MODE_NONE),
                ("NAME_TAG", await discriminator(self.message.author.name, self.message.author.discriminator), PARSE_MODE_NONE),
                ("USER_ID", str(self.message.author.id)),
                ("USER_COLOUR", await self._gather_user_colour(self.message.author)),
                ("USER_ICON", await self._gather_user_icon(self.message.author), PARSE_MODE_NONE),
                ("NAME", str(html.escape(self.message.author.display_name))),
                ("BOT_TAG", str(is_bot), PARSE_MODE_NONE),
                ("TIMESTAMP", str(self.message_created_at)),
                ("DEFAULT_TIMESTAMP", str(default_timestamp), PARSE_MODE_NONE),
                ("MESSAGE_ID", str(self.message.id)),
                ("MESSAGE_CONTENT", self.message.content, PARSE_MODE_NONE),
                ("EMBEDS", self.embeds, PARSE_MODE_NONE),
                ("ATTACHMENTS", self.attachments, PARSE_MODE_NONE),
                ("COMPONENTS", self.components, PARSE_MODE_NONE),
                ("EMOJI", self.reactions, PARSE_MODE_NONE)
            ])

            return True

    async def build_pin_template(self):
        self.message_html += await fill_out(self.guild, message_pin, [
            ("PIN_URL", DiscordUtils.pinned_message_icon, PARSE_MODE_NONE),
            ("USER_COLOUR", await self._gather_user_colour(self.message.author)),
            ("NAME", str(html.escape(self.message.author.display_name))),
            ("NAME_TAG", await discriminator(self.message.author.name, self.message.author.discriminator), PARSE_MODE_NONE),
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
            ("NAME_TAG", await discriminator(self.message.author.name, self.message.author.discriminator), PARSE_MODE_NONE),
            ("MESSAGE_ID", str(self.message.id), PARSE_MODE_NONE),
        ])

    async def build_remove(self):
        removed_member: discord.Member = self.message.mentions[0]
        self.message_html += await fill_out(self.guild, message_thread_remove, [
            ("THREAD_URL", DiscordUtils.thread_remove_recipient,
             PARSE_MODE_NONE),
            ("USER_COLOUR", await self._gather_user_colour(self.message.author)),
            ("NAME", str(html.escape(self.message.author.display_name))),
            ("NAME_TAG", await discriminator(self.message.author.name, self.message.author.discriminator),
             PARSE_MODE_NONE),
            ("RECIPIENT_USER_COLOUR", await self._gather_user_colour(removed_member)),
            ("RECIPIENT_NAME", str(html.escape(removed_member.display_name))),
            ("RECIPIENT_NAME_TAG", await discriminator(removed_member.name, removed_member.discriminator),
             PARSE_MODE_NONE),
            ("MESSAGE_ID", str(self.message.id), PARSE_MODE_NONE),
        ])

    async def build_add(self):
        removed_member: discord.Member = self.message.mentions[0]
        self.message_html += await fill_out(self.guild, message_thread_add, [
            ("THREAD_URL", DiscordUtils.thread_add_recipient,
             PARSE_MODE_NONE),
            ("USER_COLOUR", await self._gather_user_colour(self.message.author)),
            ("NAME", str(html.escape(self.message.author.display_name))),
            ("NAME_TAG", await discriminator(self.message.author.name, self.message.author.discriminator),
             PARSE_MODE_NONE),
            ("RECIPIENT_USER_COLOUR", await self._gather_user_colour(removed_member)),
            ("RECIPIENT_NAME", str(html.escape(removed_member.display_name))),
            ("RECIPIENT_NAME_TAG", await discriminator(removed_member.name, removed_member.discriminator),
             PARSE_MODE_NONE),
            ("MESSAGE_ID", str(self.message.id), PARSE_MODE_NONE),
        ])

    async def _gather_member(self, author: discord.Member):
        member = self.guild.get_member(author.id)

        if member:
            return member

        try:
            return await self.guild.fetch_member(author.id)
        except Exception:
            return None

    async def _gather_user_colour(self, author: discord.Member):
        member = await self._gather_member(author)
        user_colour = member.colour if member and str(member.colour) != "#000000" else "#FFFFFF"
        return f"color: {user_colour};"

    async def _gather_user_icon(self, author: discord.Member):
        member = await self._gather_member(author)

        if not member:
            return ""

        if hasattr(member, "display_icon") and member.display_icon:
            return f"<img class='chatlog__role-icon' src='{member.display_icon}' alt='Role Icon'>"
        elif hasattr(member, "top_role") and member.top_role and member.top_role.icon:
            return f"<img class='chatlog__role-icon' src='{member.top_role.icon}' alt='Role Icon'>"
        return ""

    def set_time(self, message: Optional[discord.Message] = None):
        message = message if message else self.message
        created_at_str = self.to_local_time_str(message.created_at)
        edited_at_str = self.to_local_time_str(message.edited_at) if message.edited_at else ""

        return created_at_str, edited_at_str

    def to_local_time_str(self, time):
        if not self.message.created_at.tzinfo:
            time = timezone("UTC").localize(time)

        local_time = time.astimezone(timezone(self.pytz_timezone))

        if self.military_time:
            return local_time.strftime(self.time_format)

        return local_time.strftime(self.time_format)


async def gather_messages(
    messages: List[discord.Message],
    guild: discord.Guild,
    pytz_timezone,
    military_time,
) -> (str, dict):
    message_html: str = ""
    meta_data: dict = {}
    previous_message: Optional[discord.Message] = None

    message_dict = {message.id: message for message in messages}

    if "thread" in str(messages[0].channel.type) and messages[0].reference:
        channel = guild.get_channel(messages[0].reference.channel_id)

        if not channel:
            channel = await guild.fetch_channel(messages[0].reference.channel_id)

        message = await channel.fetch_message(messages[0].reference.message_id)
        messages[0] = message
        messages[0].reference = None

    for message in messages:
        content_html, meta_data = await MessageConstruct(
            message,
            previous_message,
            pytz_timezone,
            military_time,
            guild,
            meta_data,
            message_dict,
        ).construct_message()
        message_html += content_html
        previous_message = message

    message_html += "</div>"
    return message_html, meta_data
