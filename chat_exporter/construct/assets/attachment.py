import math

from chat_exporter.ext.discord_utils import DiscordUtils
from chat_exporter.ext.html_generator import (
    fill_out,
    img_attachment,
    msg_attachment,
    audio_attachment,
    video_attachment,
    PARSE_MODE_NONE,
)


class Attachment:
    def __init__(self, attachments, guild):
        self.attachments = attachments
        self.guild = guild

    async def flow(self):
        await self.build_attachment()
        return self.attachments

    async def build_attachment(self):
        is_spoiler = self._is_spoiler(self.attachments)

        if self.attachments.content_type is not None:
            if "image" in self.attachments.content_type:
                await self.image()
                if is_spoiler:
                    self._mark_spoiler()
                return
            elif "video" in self.attachments.content_type:
                await self.video()
                if is_spoiler:
                    self._mark_spoiler()
                return
            elif "audio" in self.attachments.content_type:
                await self.audio()
                if is_spoiler:
                    self._mark_spoiler()
                return

        await self.file()
        if is_spoiler:
            self._mark_spoiler()

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
        file_icon = DiscordUtils.file_attachment_audio
        file_size = self.get_file_size(self.attachments.size)

        self.attachments = await fill_out(self.guild, audio_attachment, [
            ("ATTACH_ICON", file_icon, PARSE_MODE_NONE),
            ("ATTACH_URL", self.attachments.proxy_url, PARSE_MODE_NONE),
            ("ATTACH_BYTES", str(file_size), PARSE_MODE_NONE),
            ("ATTACH_AUDIO", self.attachments.proxy_url, PARSE_MODE_NONE),
            ("ATTACH_FILE", str(self.attachments.filename), PARSE_MODE_NONE)
        ])

    async def file(self):
        file_icon = await self.get_file_icon()

        file_size = self.get_file_size(self.attachments.size)

        self.attachments = await fill_out(self.guild, msg_attachment, [
            ("ATTACH_ICON", file_icon, PARSE_MODE_NONE),
            ("ATTACH_URL", self.attachments.proxy_url, PARSE_MODE_NONE),
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

        for tmp in [self.attachments.proxy_url, self.attachments.filename]:
            if not tmp:
                continue
            extension = tmp.rsplit('.', 1)[-1]
            if extension in acrobat_types:
                return DiscordUtils.file_attachment_acrobat
            elif extension in webcode_types:
                return DiscordUtils.file_attachment_webcode
            elif extension in code_types:
                return DiscordUtils.file_attachment_code
            elif extension in document_types:
                return DiscordUtils.file_attachment_document
            elif extension in archive_types:
                return DiscordUtils.file_attachment_archive
        
        return DiscordUtils.file_attachment_unknown

    @staticmethod
    def _is_spoiler(attachment) -> bool:
        """Check if an attachment is marked as a spoiler."""
        spoiler_attr = getattr(attachment, "spoiler", None)
        if callable(spoiler_attr):
            try:
                return bool(spoiler_attr())
            except Exception:
                pass
        if spoiler_attr is not None:
            return bool(spoiler_attr)

        is_spoiler_method = getattr(attachment, "is_spoiler", None)
        if callable(is_spoiler_method):
            try:
                return bool(is_spoiler_method())
            except Exception:
                return False

        return False

    def _mark_spoiler(self):
        """Add spoiler styling class to the rendered attachment HTML."""
        if not isinstance(self.attachments, str):
            return

        target = '<div class=chatlog__attachment>'
        replacement = '<div class="chatlog__attachment chatlog__attachment-spoiler">'
        if target in self.attachments:
            self.attachments = self.attachments.replace(target, replacement, 1)
        elif 'class="chatlog__attachment"' in self.attachments:
            self.attachments = self.attachments.replace(
                'class="chatlog__attachment"',
                'class="chatlog__attachment chatlog__attachment-spoiler"',
                1,
            )
