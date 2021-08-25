import math

from chat_exporter.build_html import (
    fill_out,
    img_attachment,
    msg_attachment,
    audio_attachment,
    video_attachment,
    PARSE_MODE_NONE,
)


class BuildAttachment:
    def __init__(self, attachments, guild):
        self.attachments = attachments
        self.guild = guild

    async def flow(self):
        await self.build_attachment()
        return self.attachments

    async def build_attachment(self):
        if self.attachments.content_type is not None:
            if "image" in self.attachments.content_type:
                return await self.image()
            elif "video" in self.attachments.content_type:
                return await self.video()
            elif "audio" in self.attachments.content_type:
                return await self.audio()
        await self.file()

    async def image(self):
        self.attachments = await fill_out(self.guild, img_attachment, [
            ("ATTACH_URL", self.attachments.proxy_url, PARSE_MODE_NONE),
            ("ATTACH_URL_THUMB", self.attachments.proxy_url, PARSE_MODE_NONE)
        ])

    async def video(self):
        self.attachments = await fill_out(self.guild, video_attachment, [
            ("ATTACH_URL", self.attachments.proxy_url, PARSE_MODE_NONE)
        ])

    async def audio(self):
        file_icon = "https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/discord-audio.svg"
        file_size = self.get_file_size(self.attachments.size)

        self.attachments = await fill_out(self.guild, audio_attachment, [
            ("ATTACH_ICON", file_icon, PARSE_MODE_NONE),
            ("ATTACH_URL", self.attachments.url, PARSE_MODE_NONE),
            ("ATTACH_BYTES", str(file_size), PARSE_MODE_NONE),
            ("ATTACH_AUDIO", self.attachments.proxy_url, PARSE_MODE_NONE),
            ("ATTACH_FILE", str(self.attachments.filename), PARSE_MODE_NONE)
        ])

    async def file(self):
        file_icon = await self.get_file_icon()

        file_size = self.get_file_size(self.attachments.size)

        self.attachments = await fill_out(self.guild, msg_attachment, [
            ("ATTACH_ICON", file_icon, PARSE_MODE_NONE),
            ("ATTACH_URL", self.attachments.url, PARSE_MODE_NONE),
            ("ATTACH_BYTES", str(file_size), PARSE_MODE_NONE),
            ("ATTACH_FILE", str(self.attachments.filename), PARSE_MODE_NONE)
        ])

    @staticmethod
    def get_file_size(file_size):
        if file_size == 0:
            return "0 bytes"
        size_name = ("bytes", "KB", "MB")
        i = int(math.floor(math.log(file_size, 1024)))
        p = math.pow(1024, i)
        s = round(file_size / p, 2)
        return "%s %s" % (s, size_name[i])

    async def get_file_icon(self) -> str:
        acrobat_types = "pdf"
        webcode_types = "html", "htm", "css", "rss", "xhtml", "xml"
        code_types = "py", "cgi", "pl", "gadget", "jar", "msi", "wsf", "bat", "php", "js"
        document_types = (
            "txt", "doc", "docx", "rtf", "xls", "xlsx", "ppt", "pptx", "odt", "odp", "ods", "odg", "odf", "swx",
            "sxi", "sxc", "sxd", "stw"
        )
        archive_types = (
            "br", "rpm", "dcm", "epub", "zip", "tar", "rar", "gz", "bz2", "7x", "deb", "ar", "Z", "lzo", "lz", "lz4",
            "arj", "pkg", "z"
        )

        extension = self.attachments.url.rsplit('.', 1)[1]
        if extension in acrobat_types:
            return "https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/discord-acrobat.svg"
        elif extension in webcode_types:
            return "https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/discord-webcode.svg"
        elif extension in code_types:
            return "https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/discord-code.svg"
        elif extension in document_types:
            return "https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/discord-document.svg"
        elif extension in archive_types:
            return "https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/discord-archive.svg"
        else:
            return "https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/discord-unknown.svg"
