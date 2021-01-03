from dataclasses import dataclass

from build_html import fill_out, img_attachment, msg_attachment, PARSE_MODE_NONE


@dataclass
class BuildAttachment:
    image_types = ".png", ".jpeg", ".jpg", ".gif"

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
        file_mb = self.attachments.size / 1000000
        self.attachments = await fill_out(self.guild, msg_attachment, [
            ("ATTACH_URL", self.attachments.url, PARSE_MODE_NONE),
            ("ATTACH_BYTES", str(file_mb)[:4] + "MB"),
            ("ATTACH_FILE", str(self.attachments.filename))
        ])
