from chat_exporter.ext.discord_import import discord

from chat_exporter.ext.emoji_convert import convert_emoji
from chat_exporter.ext.discord_utils import DiscordUtils
from chat_exporter.ext.html_generator import (
    fill_out,
    component_button,
    PARSE_MODE_NONE,
    PARSE_MODE_MARKDOWN,
)


class Component:
    styles = {
        "primary": "#5865F2",
        "secondary": "grey",
        "success": "#57F287",
        "danger": "#ED4245",
        "blurple": "#5865F2",
        "grey": "grey",
        "gray": "grey",
        "green": "#57F287",
        "red": "#ED4245",
        "link": "grey",
    }

    components: str = ""

    def __init__(self, component, guild):
        self.component = component
        self.guild = guild

    async def build_component(self, c):
        if isinstance(c, discord.Button):
            await self.build_button(c)

    async def build_button(self, c):
        url = c.url if c.url else ""
        label = c.label if c.label else ""
        style = self.styles[str(c.style).split(".")[1]]
        icon = DiscordUtils.button_external_link if url else ""
        emoji = await convert_emoji(str(c.emoji)) if c.emoji else ""

        self.components += await fill_out(self.guild, component_button, [
            ("URL", str(url), PARSE_MODE_NONE),
            ("LABEL", str(label), PARSE_MODE_MARKDOWN),
            ("EMOJI", str(emoji), PARSE_MODE_NONE),
            ("ICON", str(icon), PARSE_MODE_NONE),
            ("STYLE", style, PARSE_MODE_NONE)
        ])

    async def flow(self):
        for c in self.component.children:
            await self.build_component(c)
        return self.components
