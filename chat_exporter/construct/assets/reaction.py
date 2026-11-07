import logging
import re

from chat_exporter.ext.discord_import import discord
from chat_exporter.ext.emoji_convert import convert_emoji
from chat_exporter.ext.html_generator import (
    PARSE_MODE_NONE,
    custom_emoji,
    emoji,
    fill_out,
)
from chat_exporter.ext.sanitize import escape

log = logging.getLogger("chat_exporter")


class Reaction:
    def __init__(self, reaction, guild, fetch_reactors=True):
        self.reaction = reaction
        self.guild = guild
        self.fetch_reactors = fetch_reactors

    async def flow(self):
        await self.build_reaction()

        return self.reaction

    async def build_reaction(self):
        self.reactors_str = ""
        if self.fetch_reactors:
            try:
                reactors = [escape(user.display_name) async for user in self.reaction.users(limit=10)]
                self.reactors_str = "<br>".join(reactors)
                if self.reaction.count > 10:
                    self.reactors_str += f"<br>...and {int(self.reaction.count) - 10} others"
            except discord.HTTPException:
                log.debug("Failed to fetch reactors", exc_info=True)
            except Exception:
                log.debug("Unexpected error while fetching reactors", exc_info=True)

        emoji_str = str(self.reaction.emoji)
        if ":" in emoji_str:
            emoji_animated = re.compile(r"<a:.*:.*>|&lt;a:.*:.*&gt;")
            if emoji_animated.search(emoji_str):
                await self.create_discord_reaction("gif")
            else:
                await self.create_discord_reaction("png")
        else:
            await self.create_standard_emoji()

    async def create_discord_reaction(self, emoji_type):
        pattern = r":.*:(\d+)"
        match = re.search(pattern, str(self.reaction.emoji))
        emoji_id = match.group(1) if match else ""
        self.reaction = await fill_out(
            self.guild,
            custom_emoji,
            [
                ("EMOJI", str(emoji_id), PARSE_MODE_NONE),
                ("EMOJI_COUNT", str(int(self.reaction.count)), PARSE_MODE_NONE),
                ("EMOJI_FILE", emoji_type, PARSE_MODE_NONE),
                ("REACTORS", self.reactors_str, PARSE_MODE_NONE),
            ],
        )

    async def create_standard_emoji(self):
        react_emoji = await convert_emoji(str(self.reaction.emoji))
        self.reaction = await fill_out(
            self.guild,
            emoji,
            [
                ("EMOJI", str(react_emoji), PARSE_MODE_NONE),
                ("EMOJI_COUNT", str(int(self.reaction.count)), PARSE_MODE_NONE),
                ("REACTORS", self.reactors_str, PARSE_MODE_NONE),
            ],
        )
