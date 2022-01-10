from chat_exporter.ext.discord_import import discord

from chat_exporter.ext.emoji_convert import convert_emoji
from chat_exporter.ext.discord_utils import DiscordUtils
from chat_exporter.ext.html_generator import (
    fill_out,
    component_button,
    component_menu,
    component_menu_options,
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
    menu_div_id: int = 0

    def __init__(self, component, guild):
        self.component = component
        self.guild = guild

    async def build_component(self, c):
        if isinstance(c, discord.Button):
            await self.build_button(c)
        elif isinstance(c, discord.SelectMenu):
            await self.build_menu(c)
            Component.menu_div_id += 1

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

    async def build_menu(self, c):
        placeholder = c.placeholder if c.placeholder else ""
        options = c.options
        content = await self.build_menu_options(options)

        self.components += await fill_out(self.guild, component_menu, [
            ("ID", str(self.menu_div_id), PARSE_MODE_NONE),
            ("PLACEHOLDER", str(placeholder), PARSE_MODE_MARKDOWN),
            ("CONTENT", str(content), PARSE_MODE_NONE),
            ("ICON", DiscordUtils.interaction_dropdown_icon, PARSE_MODE_NONE),
        ])

    async def build_menu_options(self, options):
        content = []
        for option in options:
            content.append(await fill_out(self.guild, component_menu_options, [
                ("TITLE", str(option.label), PARSE_MODE_MARKDOWN),
                ("DESCRIPTION", str(option.description) if option.description else "", PARSE_MODE_MARKDOWN)
            ]))

        if content:
            content = f'<div id="dropdownMenu{self.menu_div_id}" class="dropdownContent">{"".join(content)}</div>'

        return content

    async def flow(self):
        for c in self.component.children:
            await self.build_component(c)
        return self.components
