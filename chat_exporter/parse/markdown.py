import re
from typing import List, Optional

from chat_exporter.ext.discord_import import discord
from chat_exporter.ext.emoji_convert import convert_emoji
from chat_exporter.ext.export_context import current
from chat_exporter.ext.sanitize import normalise_text
from chat_exporter.parse.ast import AstParser, ContainerNode, CustomEmojiNode, Node, TextNode

bot: Optional[discord.Client] = None


def pass_bot(_bot):
    # Bot is used to fetch a user who is no longer inside a guild
    # This will stop the user from appearing as 'Unknown' which some people do not want
    global bot
    bot = _bot


_CUSTOM_EMOJI = re.compile(CustomEmojiNode.PATTERN)


async def render_text_with_emoji(text: str) -> str:
    """Converts custom and unicode emoji in escaped text to images."""
    parts = []
    last = 0
    for match in _CUSTOM_EMOJI.finditer(text):
        parts.append(await convert_emoji(text[last : match.start()]))
        parts.append(CustomEmojiNode.from_match(match).render())
        last = match.end()
    parts.append(await convert_emoji(text[last:]))
    return "".join(parts)


async def _convert_emoji_in(nodes: List[Node]) -> None:
    for node in nodes:
        if isinstance(node, TextNode):
            node.text = await render_text_with_emoji(node.text)
        elif isinstance(node, ContainerNode):
            await _convert_emoji_in(node.children)


class ParseMarkdown:
    def __init__(self, content, guild=None, _bot=None):
        self.content = normalise_text(content)
        self.guild = guild
        self.bot = _bot or current().bot or bot

    async def _render(self) -> str:
        nodes = AstParser().parse(self.content)
        await _convert_emoji_in(nodes)
        self.content = "".join(n.render(self.guild, self.bot) for n in nodes)
        return self.content

    async def standard_message_flow(self):
        await self._render()

        content_no_emojis = re.sub(r'<img class="emoji emoji--small"[^>]*>', "", self.content)
        content_no_emojis = content_no_emojis.replace("<br>", "").strip()

        if not content_no_emojis:
            self.content = self.content.replace("emoji--small", "emoji--large")

        return self.content

    async def link_embed_flow(self):
        return await self._render()

    async def standard_embed_flow(self):
        return await self._render()

    async def special_embed_flow(self):
        return await self.standard_embed_flow()

    async def message_reference_flow(self):
        return await self.standard_embed_flow()

    async def special_emoji_flow(self):
        self.content = await render_text_with_emoji(self.content)
        return self.content
