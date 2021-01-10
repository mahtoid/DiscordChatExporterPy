import math

from chat_exporter.build_html import fill_out, img_attachment, msg_attachment, audio_attachment, PARSE_MODE_NONE


class BuildAttachment:
    image_types = ".png", ".jpeg", ".jpg", ".gif"
    audio: str = ""
    file_icon: str = ""

    def __init__(self, attachments, guild):
        self.attachments = attachments
        self.guild = guild

    async def flow(self):
        await self.build_attachment()

        return self.attachments

    async def build_attachment(self):
        if str(self.attachments.url).endswith(self.image_types):
            await self.image()
        else:
            await self.file()

    async def image(self):
        self.attachments = await fill_out(self.guild, img_attachment, [
            ("ATTACH_URL", self.attachments.proxy_url, PARSE_MODE_NONE),
            ("ATTACH_URL_THUMB", self.attachments.proxy_url, PARSE_MODE_NONE)
        ])

    async def file(self):
        await self.get_file_icon()

        file_size = self.get_file_size(self.attachments.size)

        self.attachments = await fill_out(self.guild, msg_attachment, [
            ("ATTACH_ICON", self.file_icon, PARSE_MODE_NONE),
            ("ATTACH_URL", self.attachments.url, PARSE_MODE_NONE),
            ("ATTACH_BYTES", str(file_size), PARSE_MODE_NONE),
            ("ATTACH_AUDIO", self.audio, PARSE_MODE_NONE),
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

    async def get_file_icon(self):
        audio_types = "aac", "mid", "mp3", "m4a", "ogg", "flac", "wav", "amr"
        webcode_types = "html", "htm", "css", "rss", "xhtml", "xml"
        code_types = "py", "cgi", "pl", "gadget", "jar", "msi", "wsf", "bat", "php", "js"
        document_types = "txt", "doc", "docx", "rtf", "xls", "xlsx", "ppt", "pptx", "odt", "odp", "ods", "odg", "odf", \
                         "swx", "sxi", "sxc", "sxd", "stw"
        acrobat_types = "pdf"
        archive_types = "br", "rpm", "dcm", "epub", "zip", "tar", "rar", "gz", "bz2", "7x", "deb", "ar", "Z", "lzo", \
                        "lz", "lz4", "arj", "pkg", "z"

        split_url = self.attachments.url.rsplit('.', 1)

        if split_url[1].endswith(audio_types):
            self.file_icon = "https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/discord-audio.svg"
            await self.set_audio()
        elif split_url[1].endswith(webcode_types):
            self.file_icon = "https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/discord-webcode.svg"
        elif split_url[1].endswith(code_types):
            self.file_icon = "https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/discord-code.svg"
        elif split_url[1].endswith(document_types):
            self.file_icon = "https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/discord-document.svg"
        elif split_url[1].endswith(acrobat_types):
            self.file_icon = "https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/discord-acrobat.svg"
        elif split_url[1].endswith(archive_types):
            self.file_icon = "https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/discord-archive.svg"
        else:
            self.file_icon = "https://cdn.jsdelivr.net/gh/mahtoid/DiscordUtils@master/discord-unknown.svg"

    async def set_audio(self):
        self.audio = await fill_out(self.guild, audio_attachment, [
            ("ATTACH_URL", self.attachments.url, PARSE_MODE_NONE),
            ("ATTACH_FILE", str(self.attachments.filename))
        ])
