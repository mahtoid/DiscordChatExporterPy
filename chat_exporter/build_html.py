import os

from chat_exporter.parse_mention import ParseMention
from chat_exporter.parse_markdown import ParseMarkdown

dir_path = os.path.dirname(os.path.realpath(__file__))

PARSE_MODE_NONE = 0
PARSE_MODE_NO_MARKDOWN = 1
PARSE_MODE_MARKDOWN = 2
PARSE_MODE_EMBED = 3
PARSE_MODE_SPECIAL_EMBED = 4
PARSE_MODE_REFERENCE = 5


async def fill_out(guild, base, replacements):
    for r in replacements:
        if len(r) == 2:  # default case
            k, v = r
            r = (k, v, PARSE_MODE_MARKDOWN)

        k, v, mode = r

        if mode != PARSE_MODE_NONE:
            v = ParseMention(v, guild).flow()
        if mode == PARSE_MODE_MARKDOWN:
            v = ParseMarkdown(v).standard_message_flow()
        elif mode == PARSE_MODE_EMBED:
            v = ParseMarkdown(v).standard_embed_flow()
        elif mode == PARSE_MODE_SPECIAL_EMBED:
            v = ParseMarkdown(v).special_embed_flow()
        elif mode == PARSE_MODE_REFERENCE:
            v = ParseMarkdown(v).message_reference_flow()
            pass

        base = base.replace("{{" + k + "}}", v)

    return base


def read_file(filename):
    with open(filename, "r") as f:
        s = f.read()
    return s


# MESSAGES
start_message = read_file(dir_path + "/chat_exporter_html/message/start.html")
bot_tag = read_file(dir_path + "/chat_exporter_html/message/bot-tag.html")
message_content = read_file(dir_path + "/chat_exporter_html/message/content.html")
message_reference = read_file(dir_path + "/chat_exporter_html/message/reference.html")
message_reference_unknown = read_file(dir_path + "/chat_exporter_html/message/reference_unknown.html")
message_body = read_file(dir_path + "/chat_exporter_html/message/message.html")
end_message = read_file(dir_path + "/chat_exporter_html/message/end.html")

# EMBED
embed_body = read_file(dir_path + "/chat_exporter_html/embed/body.html")
embed_title = read_file(dir_path + "/chat_exporter_html/embed/title.html")
embed_description = read_file(dir_path + "/chat_exporter_html/embed/description.html")
embed_field = read_file(dir_path + "/chat_exporter_html/embed/field.html")
embed_field_inline = read_file(dir_path + "/chat_exporter_html/embed/field-inline.html")
embed_footer = read_file(dir_path + "/chat_exporter_html/embed/footer.html")
embed_footer_icon = read_file(dir_path + "/chat_exporter_html/embed/footer_image.html")
embed_image = read_file(dir_path + "/chat_exporter_html/embed/image.html")
embed_thumbnail = read_file(dir_path + "/chat_exporter_html/embed/thumbnail.html")
embed_author = read_file(dir_path + "/chat_exporter_html/embed/author.html")
embed_author_icon = read_file(dir_path + "/chat_exporter_html/embed/author_icon.html")

# REACTION
emoji = read_file(dir_path + "/chat_exporter_html/reaction/emoji.html")
custom_emoji = read_file(dir_path + "/chat_exporter_html/reaction/custom_emoji.html")

# ATTACHMENT
img_attachment = read_file(dir_path + "/chat_exporter_html/attachment/image.html")
msg_attachment = read_file(dir_path + "/chat_exporter_html/attachment/message.html")
audio_attachment = read_file(dir_path + "/chat_exporter_html/attachment/audio.html")

# GUILD / FULL TRANSCRIPT
total = read_file(dir_path + "/chat_exporter_html/base.html")
