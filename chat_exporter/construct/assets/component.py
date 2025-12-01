from urllib.parse import urlparse

from chat_exporter.construct.assets.attachment import Attachment
from chat_exporter.ext.discord_import import discord
from chat_exporter.ext.discord_utils import DiscordUtils
from chat_exporter.ext.html_generator import (
    PARSE_MODE_EMOJI,
    PARSE_MODE_MARKDOWN,
    PARSE_MODE_NONE,
    component_button,
    component_container,
    component_file,
    component_media_gallery,
    component_media_gallery_item,
    component_menu,
    component_menu_options,
    component_menu_options_emoji,
    component_section,
    component_separator,
    component_text_display,
    component_thumbnail,
    fill_out,
)


class Component:
    styles = {
        "primary": "#5865F2",
        "secondary": "#4F545C",
        "success": "#2D7D46",
        "danger": "#D83C3E",
        "blurple": "#5865F2",
        "grey": "#4F545C",
        "gray": "#4F545C",
        "green": "#2D7D46",
        "red": "#D83C3E",
        "link": "#4F545C",
    }

    components: str = ""
    menus: str = ""
    buttons: str = ""
    menu_div_id: int = 0

    def __init__(self, component, guild, attachments=None):
        self.component = component
        self.guild = guild
        self.attachments = list(attachments) if attachments else []
        # Reset per-component accumulators
        self.components = ""
        self.menus = ""
        self.buttons = ""

    @staticmethod
    def _get_media_url(media):
        """Return a best-effort URL string from a media/file object, dict, or raw string."""
        if not media:
            return ""
        if isinstance(media, str):
            return media
        if isinstance(media, dict):
            return str(media.get("url", ""))
        return str(getattr(media, "url", ""))

    @staticmethod
    def _get_attr(obj, key, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    @staticmethod
    def _stringify_emoji(emoji_obj):
        """Return a displayable emoji string from dict/emoji."""
        if not emoji_obj:
            return ""
        if isinstance(emoji_obj, dict):
            emoji_id = emoji_obj.get("id")
            emoji_name = emoji_obj.get("name") or ""
            if emoji_id:
                return f"<:{emoji_name}:{emoji_id}>"
            return emoji_name
        return str(emoji_obj)

    @staticmethod
    def _file_display_name(url: str) -> str:
        """Return a clean filename without query/fragment."""
        if not url:
            return ""
        if url.startswith("attachment://"):
            return url.replace("attachment://", "")

        parsed = urlparse(url)
        path_name = parsed.path.rsplit("/", 1)[-1] if parsed.path else url
        return path_name or url

    def _find_related_attachment(self, media, file_name: str):
        """Attempt to match a component media item to a real attachment for metadata."""
        if not self.attachments:
            return None

        attachment_id = getattr(media, "attachment_id", None) if media else None
        if attachment_id is not None:
            for attachment in self.attachments:
                if getattr(attachment, "id", None) == attachment_id:
                    return attachment

        for attachment in self.attachments:
            if file_name and str(getattr(attachment, "filename", "")) == file_name:
                return attachment

        media_url = self._get_media_url(media)
        if media_url:
            for attachment in self.attachments:
                if getattr(attachment, "url", None) == media_url or getattr(attachment, "proxy_url", None) == media_url:
                    return attachment

        return None

    @staticmethod
    def _get_file_extension(name: str) -> str:
        if not name or "." not in name:
            return ""
        return name.rsplit(".", 1)[-1].lower()

    def _get_file_icon(self, file_name: str, content_type: str = "") -> str:
        """Return the most appropriate file icon for the given name or content type."""
        content_type = (content_type or "").lower()
        if content_type.startswith("audio/"):
            return DiscordUtils.file_attachment_audio

        ext = self._get_file_extension(file_name)
        if not ext and content_type:
            if "html" in content_type:
                ext = "html"
            elif "pdf" in content_type:
                ext = "pdf"

        if ext in ("pdf",):
            return DiscordUtils.file_attachment_acrobat
        elif ext in ("html", "htm", "css", "rss", "xhtml", "xml"):
            return DiscordUtils.file_attachment_webcode
        elif ext in ("py", "cgi", "pl", "gadget", "jar", "msi", "wsf", "bat", "php", "js"):
            return DiscordUtils.file_attachment_code
        elif ext in (
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
        ):
            return DiscordUtils.file_attachment_document
        elif ext in (
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
            "deb",
            "ar",
            "z",
            "lzo",
            "lz",
            "lz4",
            "arj",
            "pkg",
        ):
            return DiscordUtils.file_attachment_archive

        return DiscordUtils.file_attachment_unknown

    async def build_component(self, c):
        # Check for component type attribute
        component_type = getattr(c, 'type', None)
        
        # Handle legacy components (v1)
        if isinstance(c, discord.Button):
            return await self.build_button(c)
        elif isinstance(c, discord.SelectMenu):
            menu_html = await self.build_menu(c)
            Component.menu_div_id += 1
            return menu_html
        
        # Handle components v2 based on type
        if component_type is None:
            return ""
        
        type_value = component_type.value if hasattr(component_type, 'value') else component_type
        
        # ActionRow (type 1) - contains buttons/selects
        if type_value == 1:
            return await self.build_action_row(c)
        # Button (type 2)
        elif type_value == 2:
            return await self.build_button(c)
        # StringSelect (type 3)
        elif type_value == 3:
            menu_html = await self.build_menu(c)
            Component.menu_div_id += 1
            return menu_html
        # Section (type 9)
        elif type_value == 9:
            return await self.build_section(c)
        # TextDisplay (type 10)
        elif type_value == 10:
            return await self.build_text_display(c)
        # Thumbnail (type 11)
        elif type_value == 11:
            return await self.build_thumbnail(c)
        # MediaGallery (type 12)
        elif type_value == 12:
            return await self.build_media_gallery(c)
        # File (type 13)
        elif type_value == 13:
            return await self.build_file(c)
        # Separator (type 14)
        elif type_value == 14:
            return await self.build_separator(c)
        # Container (type 17)
        elif type_value == 17:
            return await self.build_container(c)
        
        return ""

    async def build_action_row(self, c):
        """Build an action row containing buttons or select menus"""
        result = ""
        items_html = ""
        
        children = getattr(c, 'children', []) or getattr(c, 'components', [])
        for child in children:
            child_html = await self.build_component(child)
            if child_html:
                items_html += child_html
        
        if items_html:
            result = f'<div class="chatlog__components">{items_html}</div>'
        
        return result

    async def build_button(self, c):
        url_value = self._get_attr(c, "url", None)
        disabled = bool(self._get_attr(c, "disabled", False))

        if url_value:
            url = str(url_value)
            target = " target='_blank'"
            icon = str(DiscordUtils.button_external_link)
        else:
            url = "javascript:;"
            target = ""
            icon = ""
            
        label = str(self._get_attr(c, "label", "") or "")
        raw_style = self._get_attr(c, "style", None)
        style_key = ""
        if isinstance(raw_style, int):
            style_key = {
                1: "primary",
                2: "secondary",
                3: "success",
                4: "danger",
                5: "link",
            }.get(raw_style, "")
        else:
            raw_style_str = str(raw_style)
            style_key = raw_style_str.split(".")[-1].lower()
        style = self.styles.get(style_key, "#4F545C")
        emoji = self._stringify_emoji(self._get_attr(c, "emoji", None))

        return await fill_out(self.guild, component_button, [
            ("DISABLED", "chatlog__component-disabled" if disabled else "", PARSE_MODE_NONE),
            ("URL", url, PARSE_MODE_NONE),
            ("LABEL", label, PARSE_MODE_MARKDOWN),
            ("EMOJI", emoji, PARSE_MODE_EMOJI),
            ("ICON", icon, PARSE_MODE_NONE),
            ("TARGET", target, PARSE_MODE_NONE),
            ("STYLE", style, PARSE_MODE_NONE)
        ])

    async def build_menu(self, c):
        placeholder = self._get_attr(c, "placeholder", "") or ""
        options = self._get_attr(c, "options", []) or []
        disabled = bool(self._get_attr(c, "disabled", False))
        content = ""
        default_labels = []
        for opt in options:
            if self._get_attr(opt, "default", False):
                label = str(self._get_attr(opt, "label", ""))
                emoji = self._stringify_emoji(self._get_attr(opt, "emoji", None))
                if emoji:
                    label = f"{emoji} {label}".strip()
                default_labels.append(label)
        if not placeholder and default_labels:
            placeholder = ", ".join([label for label in default_labels if label])
        if not placeholder:
            placeholder = "Select an option"

        if not disabled:
            content = await self.build_menu_options(options)

        menu_html = await fill_out(self.guild, component_menu, [
            ("DISABLED", "chatlog__component-disabled" if disabled else "", PARSE_MODE_NONE),
            ("ID", str(self.menu_div_id), PARSE_MODE_NONE),
            ("PLACEHOLDER", str(placeholder), PARSE_MODE_MARKDOWN),
            ("CONTENT", str(content), PARSE_MODE_NONE),
            ("ICON", DiscordUtils.interaction_dropdown_icon, PARSE_MODE_NONE),
        ])
        return menu_html

    async def build_menu_options(self, options):
        content = []
        for option in options:
            label = self._get_attr(option, "label", "")
            description = self._get_attr(option, "description", "")
            option_emoji = self._stringify_emoji(self._get_attr(option, "emoji", None))
            is_default = bool(self._get_attr(option, "default", False))
            default_class = "dropdownContentSelected" if is_default else ""

            if option_emoji:
                content.append(await fill_out(self.guild, component_menu_options_emoji, [
                    ("EMOJI", str(option_emoji), PARSE_MODE_EMOJI),
                    ("TITLE", str(label), PARSE_MODE_MARKDOWN),
                    ("DESCRIPTION", str(description) if description else "", PARSE_MODE_MARKDOWN),
                    ("DEFAULT_CLASS", default_class, PARSE_MODE_NONE),
                ]))
            else:
                content.append(await fill_out(self.guild, component_menu_options, [
                    ("TITLE", str(label), PARSE_MODE_MARKDOWN),
                    ("DESCRIPTION", str(description) if description else "", PARSE_MODE_MARKDOWN),
                    ("DEFAULT_CLASS", default_class, PARSE_MODE_NONE),
                ]))

        if content:
            content = f'<div id="dropdownMenu{self.menu_div_id}" class="dropdownContent">{"".join(content)}</div>'

        return content

    async def build_container(self, c):
        """Build a container component (like an embed)"""
        accent_color = getattr(c, 'accent_color', None) or getattr(c, 'accent_colour', None)
        spoiler = getattr(c, 'spoiler', False)
        components = getattr(c, 'components', []) or getattr(c, 'children', [])
        
        # Build nested components
        content_html = ""
        for child in components:
            child_html = await self.build_component(child)
            if child_html:
                content_html += child_html
        
        # Handle accent color
        accent_style = ""
        if accent_color is not None:
            # Discord Colour objects don't support string formatting with :x directly
            try:
                if hasattr(accent_color, "value"):
                    color_value = accent_color.value
                elif isinstance(accent_color, str):
                    cleaned = accent_color.lower().strip()
                    if cleaned.startswith("#"):
                        cleaned = cleaned[1:]
                    if cleaned.startswith("0x"):
                        cleaned = cleaned[2:]
                    color_value = int(cleaned, 16)
                else:
                    color_value = int(accent_color)
                color_hex = f"#{color_value:06x}"
                accent_style = f'style="border-left: 4px solid {color_hex}; padding-left: 12px;"'
            except (TypeError, ValueError):
                accent_style = ""
        
        spoiler_class = "chatlog__component-spoiler" if spoiler else ""
        
        return await fill_out(self.guild, component_container, [
            ("SPOILER_CLASS", spoiler_class, PARSE_MODE_NONE),
            ("ACCENT_COLOR_STYLE", accent_style, PARSE_MODE_NONE),
            ("CONTENT", content_html, PARSE_MODE_NONE),
        ])

    async def build_section(self, c):
        """Build a section component with content and accessory"""
        components = getattr(c, 'components', []) or getattr(c, 'children', [])
        accessory = getattr(c, 'accessory', None)
        
        # Build content (text displays)
        content_html = ""
        for child in components:
            child_html = await self.build_component(child)
            if child_html:
                content_html += child_html
        
        # Build accessory (thumbnail or button)
        accessory_html = ""
        if accessory:
            accessory_html = await self.build_component(accessory)
        
        return await fill_out(self.guild, component_section, [
            ("CONTENT", content_html, PARSE_MODE_NONE),
            ("ACCESSORY", accessory_html, PARSE_MODE_NONE),
        ])

    async def build_text_display(self, c):
        """Build a text display component"""
        content = getattr(c, 'content', '')
        
        return await fill_out(self.guild, component_text_display, [
            ("CONTENT", str(content), PARSE_MODE_MARKDOWN),
        ])

    async def build_thumbnail(self, c):
        """Build a thumbnail component"""
        media = self._get_attr(c, 'media', None)
        description = self._get_attr(c, 'description', None)
        spoiler = bool(self._get_attr(c, 'spoiler', False))
        
        url = self._get_media_url(media)
        if not url:
            return ""

        spoiler_class = "chatlog__component-spoiler" if spoiler else ""
        description_text = description if description else ""
        description_overlay = ""
        
        if description:
            description_overlay = f'<div class="chatlog__component-thumbnail-description">{description}</div>'
        
        return await fill_out(self.guild, component_thumbnail, [
            ("URL", str(url), PARSE_MODE_NONE),
            ("DESCRIPTION", description_text, PARSE_MODE_MARKDOWN),
            ("SPOILER_CLASS", spoiler_class, PARSE_MODE_NONE),
            ("DESCRIPTION_OVERLAY", description_overlay, PARSE_MODE_NONE),
        ])

    async def build_media_gallery(self, c):
        """Build a media gallery component"""
        items = getattr(c, 'items', []) or getattr(c, 'components', []) or getattr(c, 'children', [])
        
        items_html = ""
        for item in items:
            items_html += await self.build_media_gallery_item(item)
        
        # Determine gallery class based on item count
        item_count = len(items)
        gallery_class = ""
        if item_count == 1:
            gallery_class = "chatlog__media-gallery-single"
        elif item_count == 2:
            gallery_class = "chatlog__media-gallery-double"
        elif item_count == 3:
            gallery_class = "chatlog__media-gallery-triple"
        elif item_count >= 4:
            gallery_class = "chatlog__media-gallery-grid"
        
        return await fill_out(self.guild, component_media_gallery, [
            ("ITEMS", items_html, PARSE_MODE_NONE),
            ("GALLERY_CLASS", gallery_class, PARSE_MODE_NONE),
        ])

    async def build_media_gallery_item(self, item):
        """Build a single media gallery item"""
        media = self._get_attr(item, 'media', None)
        description = self._get_attr(item, 'description', None)
        spoiler = bool(self._get_attr(item, 'spoiler', False))
        
        url = self._get_media_url(media)
        if not url:
            return ""

        spoiler_class = "chatlog__component-spoiler" if spoiler else ""
        description_text = description if description else ""
        description_overlay = ""
        
        if description:
            description_overlay = f'<div class="chatlog__component-media-description">{description}</div>'
        
        return await fill_out(self.guild, component_media_gallery_item, [
            ("URL", str(url), PARSE_MODE_NONE),
            ("DESCRIPTION", description_text, PARSE_MODE_MARKDOWN),
            ("SPOILER_CLASS", spoiler_class, PARSE_MODE_NONE),
            ("DESCRIPTION_OVERLAY", description_overlay, PARSE_MODE_NONE),
        ])

    async def build_separator(self, c):
        """Build a separator component"""
        divider = self._get_attr(c, 'divider', True)
        spacing = self._get_attr(c, 'spacing', 1)
        
        # Spacing: 1 = SMALL, 2 = LARGE
        spacing_class = "chatlog__separator-large" if spacing == 2 else "chatlog__separator-small"
        divider_html = '<div class="chatlog__separator-line"></div>' if divider else ""
        
        return await fill_out(self.guild, component_separator, [
            ("SPACING_CLASS", spacing_class, PARSE_MODE_NONE),
            ("DIVIDER", divider_html, PARSE_MODE_NONE),
        ])

    async def build_file(self, c):
        """Build a file component"""
        file = self._get_attr(c, 'file', None) or self._get_attr(c, 'media', None)
        spoiler = bool(self._get_attr(c, 'spoiler', False))
        
        url = self._get_media_url(file)
        if not url:
            return ""

        # Extract filename and additional metadata
        file_name = self._get_attr(c, "name", None) or self._file_display_name(url)
        related_attachment = self._find_related_attachment(file, file_name)
        if related_attachment:
            file_name = str(getattr(related_attachment, "filename", file_name) or file_name)

        size_bytes = getattr(related_attachment, "size", None) if related_attachment else None
        if size_bytes is None:
            component_size = self._get_attr(c, "size", None)
            if component_size is not None:
                try:
                    size_bytes = int(component_size)
                except (TypeError, ValueError):
                    size_bytes = None
        file_size = Attachment.get_file_size(size_bytes) if size_bytes is not None else "Unknown size"

        content_type = getattr(file, "content_type", None)
        if related_attachment and not content_type:
            content_type = getattr(related_attachment, "content_type", None)
        file_icon = self._get_file_icon(file_name, content_type)
        
        spoiler_class = "chatlog__component-spoiler" if spoiler else ""
        
        return await fill_out(self.guild, component_file, [
            ("FILE_NAME", str(file_name), PARSE_MODE_NONE),
            ("FILE_URL", str(url), PARSE_MODE_NONE),
            ("FILE_ICON", str(file_icon), PARSE_MODE_NONE),
            ("FILE_SIZE", str(file_size), PARSE_MODE_NONE),
            ("SPOILER_CLASS", spoiler_class, PARSE_MODE_NONE),
        ])

    async def flow(self):
        # Try to handle the component directly
        component_html = await self.build_component(self.component)
        if component_html:
            self.components += component_html
        else:
            # Fallback to legacy flow for action rows with children
            children = getattr(self.component, 'children', []) or getattr(self.component, 'components', [])
            for c in children:
                child_html = await self.build_component(c)
                if child_html:
                    self.buttons += child_html

            if self.menus:
                self.components += f'<div class="chatlog__components">{self.menus}</div>'

            if self.buttons:
                self.components += f'<div class="chatlog__components">{self.buttons}</div>'

        return self.components
