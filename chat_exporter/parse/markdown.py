import re
from typing import Optional

from chat_exporter.ext.discord_import import discord
from chat_exporter.ext.emoji_convert import convert_emoji
from chat_exporter.parse.ast import AstParser

bot: Optional[discord.Client] = None


def pass_bot(_bot):
    # Bot is used to fetch a user who is no longer inside a guild
    # This will stop the user from appearing as 'Unknown' which some people do not want
    global bot
    bot = _bot


class ParseMarkdown:
    def __init__(self, content, guild=None, _bot=None):
        self.content = content
        self.guild = guild
        self.bot = _bot or bot
        self.code_blocks = []

    def parse_code_block_markdown(self):
        # Shield multiline code blocks
        def repl_multiline(match):
            self.code_blocks.append(match.group(0))
            return f"{{{{CODE_BLOCK_{len(self.code_blocks) - 1}}}}}"

        self.content = re.sub(r"```.*?```", repl_multiline, self.content, flags=re.DOTALL)

        # Shield inline code
        def repl_inline(match):
            self.code_blocks.append(match.group(0))
            return f"{{{{CODE_BLOCK_{len(self.code_blocks) - 1}}}}}"

        self.content = re.sub(r"`.*?`", repl_inline, self.content, flags=re.DOTALL)

    def reverse_code_block_markdown(self):
        for i, block in enumerate(self.code_blocks):
            self.content = self.content.replace(f"{{{{CODE_BLOCK_{i}}}}}", block)

    async def standard_message_flow(self):
        ast = AstParser()
        nodes = ast.parse(self.content)
        self.content = "".join(n.render(self.guild, self.bot) for n in nodes)
        await self.parse_emoji()
        return self.content

    async def link_embed_flow(self):
        ast = AstParser()
        nodes = ast.parse(self.content)
        self.content = "".join(n.render(self.guild, self.bot) for n in nodes)
        await self.parse_emoji()
        return self.content

    async def standard_embed_flow(self):
        ast = AstParser()
        nodes = ast.parse(self.content)
        self.content = "".join(n.render(self.guild, self.bot) for n in nodes)
        await self.parse_emoji()
        return self.content

    async def special_embed_flow(self):
        return await self.standard_embed_flow()

    async def message_reference_flow(self):
        self.strip_preserve()
        return await self.standard_embed_flow()

    async def special_emoji_flow(self):
        await self.parse_emoji()
        return self.content

    def strip_preserve(self):
        p = r'<span class="chatlog__markdown-preserve">(.*?)</span>'
        self.content = re.sub(p, r"\1", self.content)

    async def parse_emoji(self):
        holder = (
            [r"&lt;:.*?:(\d*)&gt;", '<img class="emoji emoji--small" src="https://cdn.discordapp.com/emojis/%s.png">'],
            [r"&lt;a:.*?:(\d*)&gt;", '<img class="emoji emoji--small" src="https://cdn.discordapp.com/emojis/%s.gif">'],
            [r"<:.*?:(\d*)>", '<img class="emoji emoji--small" src="https://cdn.discordapp.com/emojis/%s.png">'],
            [r"<a:.*?:(\d*)>", '<img class="emoji emoji--small" src="https://cdn.discordapp.com/emojis/%s.gif">'],
        )

        shield_blocks = []
        def repl(match):
            shield_blocks.append(match.group(0))
            return f"{{{{SHIELD_{len(shield_blocks) - 1}}}}}"
        self.content = re.sub(r'<div class="pre pre--multiline.*?</div>', repl, self.content, flags=re.DOTALL)
        self.content = re.sub(r'<span class="pre pre-inline">.*?</span>', repl, self.content, flags=re.DOTALL)

        self.content = await convert_emoji([word for word in self.content])

        for p, r in holder:

            def make_repl(template):
                def repl(match):
                    return template % match.group(1)

                return repl

            self.content = re.sub(p, make_repl(r), self.content)

        for i, block in enumerate(shield_blocks):
            self.content = self.content.replace(f"{{{{SHIELD_{i}}}}}", block)
