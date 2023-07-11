import html

from chat_exporter.ext.discord_import import discord

from chat_exporter.ext.html_generator import (
    fill_out,
    embed_body,
    embed_title,
    embed_description,
    embed_field,
    embed_field_inline,
    embed_footer,
    embed_footer_icon,
    embed_image,
    embed_thumbnail,
    embed_author,
    embed_author_icon,
    PARSE_MODE_NONE,
    PARSE_MODE_EMBED,
    PARSE_MODE_MARKDOWN,
    PARSE_MODE_SPECIAL_EMBED,
)

modules_which_use_none = ["nextcord", "disnake"]


def _gather_checker():
    if discord.module not in modules_which_use_none and hasattr(discord.Embed, "Empty"):
        return discord.Embed.Empty
    return None


class Embed:
    r: str
    g: str
    b: str
    title: str
    description: str
    author: str
    image: str
    thumbnail: str
    footer: str
    fields: str

    check_against = None

    def __init__(self, embed, guild):
        self.embed: discord.Embed = embed
        self.guild: discord.Guild = guild

    async def flow(self):
        self.check_against = _gather_checker()
        self.build_colour()
        await self.build_title()
        await self.build_description()
        await self.build_fields()
        await self.build_author()
        await self.build_image()
        await self.build_thumbnail()
        await self.build_footer()
        await self.build_embed()

        return self.embed

    def build_colour(self):
        self.r, self.g, self.b = (
            (self.embed.colour.r, self.embed.colour.g, self.embed.colour.b)
            if self.embed.colour != self.check_against else (0x20, 0x22, 0x25)  # default colour
        )

    async def build_title(self):
        self.title = html.escape(self.embed.title) if self.embed.title != self.check_against else ""

        if self.title:
            self.title = await fill_out(self.guild, embed_title, [
                ("EMBED_TITLE", self.title, PARSE_MODE_MARKDOWN)
            ])

    async def build_description(self):
        self.description = html.escape(self.embed.description) if self.embed.description != self.check_against else ""

        if self.description:
            self.description = await fill_out(self.guild, embed_description, [
                ("EMBED_DESC", self.embed.description, PARSE_MODE_EMBED)
            ])

    async def build_fields(self):
        self.fields = ""

        # This does not have to be here, but Pycord.
        if not self.embed.fields:
            return

        for field in self.embed.fields:
            field.name = html.escape(field.name)
            field.value = html.escape(field.value)

            if field.inline:
                self.fields += await fill_out(self.guild, embed_field_inline, [
                    ("FIELD_NAME", field.name, PARSE_MODE_SPECIAL_EMBED),
                    ("FIELD_VALUE", field.value, PARSE_MODE_EMBED)
                ])
            else:
                self.fields += await fill_out(self.guild, embed_field, [
                    ("FIELD_NAME", field.name, PARSE_MODE_SPECIAL_EMBED),
                    ("FIELD_VALUE", field.value, PARSE_MODE_EMBED)])

    async def build_author(self):
        self.author = html.escape(self.embed.author.name) if (
                self.embed.author and self.embed.author.name != self.check_against
        ) else ""

        self.author = f'<a class="chatlog__embed-author-name-link" href="{self.embed.author.url}">{self.author}</a>' \
            if (
                self.embed.author and self.embed.author.url != self.check_against
            ) else self.author

        author_icon = await fill_out(self.guild, embed_author_icon, [
            ("AUTHOR", self.author, PARSE_MODE_NONE),
            ("AUTHOR_ICON", self.embed.author.icon_url, PARSE_MODE_NONE)
        ]) if self.embed.author and self.embed.author.icon_url != self.check_against else ""

        if author_icon == "" and self.author != "":
            self.author = await fill_out(self.guild, embed_author, [("AUTHOR", self.author, PARSE_MODE_NONE)])
        else:
            self.author = author_icon

    async def build_image(self):
        self.image = await fill_out(self.guild, embed_image, [
            ("EMBED_IMAGE", str(self.embed.image.proxy_url), PARSE_MODE_NONE)
        ]) if self.embed.image and self.embed.image.url != self.check_against else ""

    async def build_thumbnail(self):
        self.thumbnail = await fill_out(self.guild, embed_thumbnail, [
            ("EMBED_THUMBNAIL", str(self.embed.thumbnail.url), PARSE_MODE_NONE)]) \
            if self.embed.thumbnail and self.embed.thumbnail.url != self.check_against else ""

    async def build_footer(self):
        self.footer = html.escape(self.embed.footer.text) if (
                self.embed.footer and self.embed.footer.text != self.check_against
        ) else ""

        footer_icon = self.embed.footer.icon_url if (
                self.embed.footer and self.embed.footer.icon_url != self.check_against
        ) else None

        if not self.footer:
            return

        if footer_icon is not None:
            self.footer = await fill_out(self.guild, embed_footer_icon, [
                ("EMBED_FOOTER", self.footer, PARSE_MODE_NONE),
                ("EMBED_FOOTER_ICON", footer_icon, PARSE_MODE_NONE)
            ])
        else:
            self.footer = await fill_out(self.guild, embed_footer, [
                ("EMBED_FOOTER", self.footer, PARSE_MODE_NONE)])

    async def build_embed(self):
        self.embed = await fill_out(self.guild, embed_body, [
            ("EMBED_R", str(self.r)),
            ("EMBED_G", str(self.g)),
            ("EMBED_B", str(self.b)),
            ("EMBED_AUTHOR", self.author, PARSE_MODE_NONE),
            ("EMBED_TITLE", self.title, PARSE_MODE_NONE),
            ("EMBED_IMAGE", self.image, PARSE_MODE_NONE),
            ("EMBED_THUMBNAIL", self.thumbnail, PARSE_MODE_NONE),
            ("EMBED_DESC", self.description, PARSE_MODE_NONE),
            ("EMBED_FIELDS", self.fields, PARSE_MODE_NONE),
            ("EMBED_FOOTER", self.footer, PARSE_MODE_NONE),
        ])
