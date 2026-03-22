import math

from chat_exporter.ext.discord_utils import DiscordUtils
from chat_exporter.ext.html_generator import (
    PARSE_MODE_NONE,
    audio_attachment,
    fill_out,
    img_attachment,
    img_grid,
    img_grid_item,
    msg_attachment,
    video_attachment,
)


class Attachment:
    def __init__(self, attachments, guild):
        self.attachments = attachments
        self.guild = guild

    async def flow(self):
        await self.build_attachment()
        return self.attachments

    async def build_attachment(self):
        is_spoiler = self._is_spoiler()

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

    async def get_data(self):
        is_spoiler = self._is_spoiler()
        if self.attachments.content_type is not None:
            if "image" in self.attachments.content_type:
                return {
                    "type": "image",
                    "url": self.attachments.proxy_url,
                    "is_spoiler": is_spoiler,
                    "filename": self.attachments.filename,
                }
            elif "video" in self.attachments.content_type:
                return {
                    "type": "video",
                    "url": self.attachments.proxy_url,
                    "is_spoiler": is_spoiler,
                    "filename": self.attachments.filename,
                }
        return None

    async def image(self):
        self.attachments = await fill_out(
            self.guild,
            img_attachment,
            [
                ("ATTACH_URL", self.attachments.proxy_url, PARSE_MODE_NONE),
                ("ATTACH_URL_THUMB", self.attachments.proxy_url, PARSE_MODE_NONE),
            ],
        )

    async def video(self):
        self.attachments = await fill_out(
            self.guild, video_attachment, [("ATTACH_URL", self.attachments.proxy_url, PARSE_MODE_NONE)]
        )

    async def audio(self):
        file_icon = DiscordUtils.file_attachment_audio
        file_size = self.get_file_size(self.attachments.size)

        self.attachments = await fill_out(
            self.guild,
            audio_attachment,
            [
                ("ATTACH_ICON", file_icon, PARSE_MODE_NONE),
                ("ATTACH_URL", self.attachments.proxy_url, PARSE_MODE_NONE),
                ("ATTACH_BYTES", str(file_size), PARSE_MODE_NONE),
                ("ATTACH_AUDIO", self.attachments.proxy_url, PARSE_MODE_NONE),
                ("ATTACH_FILE", str(self.attachments.filename), PARSE_MODE_NONE),
            ],
        )

    async def file(self):
        file_icon = await self.get_file_icon()

        file_size = self.get_file_size(self.attachments.size)

        self.attachments = await fill_out(
            self.guild,
            msg_attachment,
            [
                ("ATTACH_ICON", file_icon, PARSE_MODE_NONE),
                ("ATTACH_URL", self.attachments.proxy_url, PARSE_MODE_NONE),
                ("ATTACH_BYTES", str(file_size), PARSE_MODE_NONE),
                ("ATTACH_FILE", str(self.attachments.filename), PARSE_MODE_NONE),
            ],
        )

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
        return self.resolve_file_icon(
            name=str(getattr(self.attachments, "filename", "") or ""),
            content_type=str(getattr(self.attachments, "content_type", "") or ""),
            url=str(getattr(self.attachments, "proxy_url", "") or ""),
        )

    @staticmethod
    def resolve_file_icon(name: str = "", content_type: str = "", url: str = "") -> str:
        acrobat_types = "pdf"
        webcode_types = "html", "htm", "css", "rss", "xhtml", "xml"
        code_types = "py", "cgi", "pl", "gadget", "jar", "msi", "wsf", "bat", "php", "js"
        document_types = (
            "txt",
            "doc",
            "docx",
            "rtf",
            "xls",
            "xlsx",
            "ppt",
            "pptx",
            "odt",
            "odp",
            "ods",
            "odg",
            "odf",
            "swx",
            "sxi",
            "sxc",
            "sxd",
            "stw",
        )
        archive_types = (
            "br",
            "rpm",
            "dcm",
            "epub",
            "zip",
            "tar",
            "rar",
            "gz",
            "bz2",
            "7x",
            "7z",
            "deb",
            "ar",
            "z",
            "lzo",
            "lz",
            "lz4",
            "arj",
            "pkg",
        )

        content_type = (content_type or "").lower()
        if content_type.startswith("audio/"):
            return DiscordUtils.file_attachment_audio

        def _extension_from(value: str) -> str:
            if not value:
                return ""
            cleaned = str(value).split("?", 1)[0].split("#", 1)[0]
            if "." not in cleaned:
                return ""
            return cleaned.rsplit(".", 1)[-1].lower()

        extension = ""
        for candidate in (name, url):
            extension = _extension_from(candidate)
            if extension:
                break

        if not extension and content_type:
            if "html" in content_type:
                extension = "html"
            elif "pdf" in content_type:
                extension = "pdf"

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

    def _is_spoiler(self) -> bool:
        """Check if an attachment is marked as a spoiler."""
        attachment = self.attachments
        spoiler_attr = getattr(attachment, "spoiler", None)
        if callable(spoiler_attr):
            try:
                return bool(spoiler_attr())
            except Exception:  # noqa: S110
                # In case spoiler_attr() is a property mascotading as a callable that fails
                pass
        if spoiler_attr is not None:
            return bool(spoiler_attr)

        is_spoiler_method = getattr(attachment, "is_spoiler", None)
        if callable(is_spoiler_method):
            try:
                return bool(is_spoiler_method())
            except Exception:  # noqa: S110
                # If the method check fails, assume it's not a spoiler
                return False

        return False

    def _mark_spoiler(self):
        """Add spoiler styling class to the rendered attachment HTML."""
        if not isinstance(self.attachments, str):
            return

        replacements = (
            ("<div class='chatlog__attachment'>", "<div class='chatlog__attachment chatlog__attachment-spoiler'>"),
            ("<div class=\"chatlog__attachment\">", "<div class=\"chatlog__attachment chatlog__attachment-spoiler\">"),
            ("<div class=chatlog__attachment>", "<div class=\"chatlog__attachment chatlog__attachment-spoiler\">"),
            ("class='chatlog__attachment'", "class='chatlog__attachment chatlog__attachment-spoiler'"),
            ("class=\"chatlog__attachment\"", "class=\"chatlog__attachment chatlog__attachment-spoiler\""),
            ("class=chatlog__attachment", "class=\"chatlog__attachment chatlog__attachment-spoiler\""),
        )

        for target, replacement in replacements:
            if target in self.attachments:
                self.attachments = self.attachments.replace(target, replacement, 1)
                break


class AttachmentGrid:
    def __init__(self, attachments, guild, splitIndex):
        self.attachments = attachments
        self.guild = guild
        self.splitIndex = splitIndex

    async def flow(self):
        grid_items_html = ""
        for a in self.attachments:
            item_content = await Attachment(a, self.guild).flow()
            
            grid_items_html += await fill_out(
                self.guild,
                img_grid_item,
                [
                    ("ITEM_CLASS", "", PARSE_MODE_NONE),
                    ("ITEM_CONTENT", item_content, PARSE_MODE_NONE),
                ],
            )

        grid_class = self._get_grid_class(len(self.attachments), self.splitIndex)

        return await fill_out(
            self.guild,
            img_grid,
            [
                ("GRID_CLASS", grid_class, PARSE_MODE_NONE),
                ("GRID_ITEMS", grid_items_html, PARSE_MODE_NONE),
            ],
        )

    @staticmethod
    def _get_grid_class(count, splitIndex):
        if count == 1:
            return "chatlog__attachment-grid--1x1"
        elif count == 2:
            return "chatlog__attachment-grid--1x2"
        elif count == 3:
            if splitIndex == 0:
                return "chatlog__attachment-grid--1x3" # mosaic
            else:
                return "chatlog__attachment-grid--3x3"
        elif count <= 4:
            return "chatlog__attachment-grid--2x2"
        else:
            return "chatlog__attachment-grid--3x3"
