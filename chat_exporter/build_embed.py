import discord

from chat_exporter.build_html import fill_out, embed_body, embed_title, embed_description, embed_field, \
    embed_field_inline, embed_footer, embed_footer_icon, embed_image, embed_thumbnail, embed_author, embed_author_icon, \
    PARSE_MODE_EMBED, PARSE_MODE_SPECIAL_EMBED, PARSE_MODE_NONE, PARSE_MODE_MARKDOWN


class BuildEmbed:
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

    def __init__(self, embed, guild):
        self.embed: discord.Embed = embed
        self.guild: discord.Guild = guild

    async def flow(self):
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
        self.r, self.g, self.b = (self.embed.colour.r, self.embed.colour.g, self.embed.colour.b) \
            if self.embed.colour != discord.Embed.Empty \
            else (0x20, 0x22, 0x25)  # default colour

    async def build_title(self):
        self.title = self.embed.title \
            if self.embed.title != discord.Embed.Empty \
            else ""

        if self.title != "":
            self.title = await fill_out(self.guild, embed_title, [
                ("EMBED_TITLE", self.title, PARSE_MODE_MARKDOWN)
            ])

    async def build_description(self):
        self.description = self.embed.description \
            if self.embed.description != discord.Embed.Empty \
            else ""

        if self.description != "":
            self.description = await fill_out(self.guild, embed_description, [
                ("EMBED_DESC", self.embed.description, PARSE_MODE_EMBED)
            ])

    async def build_fields(self):
        self.fields = ""
        for field in self.embed.fields:
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
        self.author = self.embed.author.name \
            if self.embed.author.name != discord.Embed.Empty \
            else ""

        self.author = f'<a class="chatlog__embed-author-name-link" href="{self.embed.author.url}">{self.author}</a>' \
            if self.embed.author.url != discord.Embed.Empty \
            else self.author

        author_icon = await fill_out(self.guild, embed_author_icon, [
            ("AUTHOR", self.author, PARSE_MODE_NONE),
            ("AUTHOR_ICON", self.embed.author.icon_url, PARSE_MODE_NONE)
        ]) \
            if self.embed.author.icon_url != discord.Embed.Empty \
            else ""

        if author_icon == "" and self.author != "":
            self.author = await fill_out(self.guild, embed_author, [("AUTHOR", self.author, PARSE_MODE_NONE)])
        else:
            self.author = author_icon

    async def build_image(self):
        self.image = await fill_out(self.guild, embed_image, [
            ("EMBED_IMAGE", str(self.embed.image.proxy_url), PARSE_MODE_NONE)
        ]) \
            if self.embed.image.url != discord.Embed.Empty \
            else ""

    async def build_thumbnail(self):
        self.thumbnail = await fill_out(self.guild, embed_thumbnail, [
            ("EMBED_THUMBNAIL", str(self.embed.thumbnail.url), PARSE_MODE_NONE)]) \
            if self.embed.thumbnail.url != discord.Embed.Empty \
            else ""

    async def build_footer(self):
        footer = self.embed.footer.text \
            if self.embed.footer.text != discord.Embed.Empty \
            else ""
        footer_icon = self.embed.footer.icon_url \
            if self.embed.footer.icon_url != discord.Embed.Empty \
            else None

        if footer != "":
            if footer_icon is not None:
                self.footer = await fill_out(self.guild, embed_footer_icon, [
                    ("EMBED_FOOTER", footer, PARSE_MODE_NONE),
                    ("EMBED_FOOTER_ICON", footer_icon, PARSE_MODE_NONE)
                ])
            else:
                self.footer = await fill_out(self.guild, embed_footer, [
                    ("EMBED_FOOTER", footer, PARSE_MODE_NONE),
                ])
        else:
            self.footer = ""

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
            ("EMBED_FOOTER", self.footer, PARSE_MODE_NONE)
        ])
