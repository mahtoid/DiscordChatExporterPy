import io
import re
import os
import discord
import sys
import traceback
from chat_exporter.misc_tools import escape_html, member_colour_translator
from chat_exporter.mention_convert import parse_mentions, escape_mentions, unescape_mentions
from chat_exporter.markdown_convert import parse_markdown, parse_embed_markdown, parse_emoji
from chat_exporter.emoji_convert import convert_emoji
from pytz import timezone
from datetime import timedelta

dir_path = os.path.dirname(os.path.realpath(__file__))

eastern = timezone("US/Eastern")
utc = timezone("UTC")

bot = None


def init_exporter(_bot):
    global bot
    bot = _bot


async def export(ctx):
    # noinspection PyBroadException
    try:
        transcript = await produce_transcript(ctx.channel)
    except Exception:
        transcript = None
        print("Error during transcript generation!", file=sys.stderr)
        traceback.print_exc()
        error_embed = discord.Embed(
            title="Transcript Generation Failed!",
            description="Whoops! We've stumbled in to an issue here.",
            colour=discord.Colour.red()
        )
        await ctx.channel.send(embed=error_embed)
        print(f"Please send a screenshot of the above error to https://www.github.com/mahtoid/DiscordChatExporterPy")

    if transcript is not None:
        async for m in ctx.channel.history(limit=None):
            try:
                for f in m.attachments:
                    if f"transcript-{ctx.channel.name}.html" in f.filename:
                        await m.delete()
            except TypeError:
                continue

        # Save transcript
        transcript_embed = discord.Embed(
            description=f"**Transcript Name:** transcript-{ctx.channel.name}\n\n"
                        f"{ctx.author.mention} requested a transcript of the channel",
            colour=discord.Colour.blurple()
        )

        transcript_file = discord.File(io.BytesIO(transcript.encode()),
                                       filename=f"transcript-{ctx.channel.name}.html")

        await ctx.channel.send(embed=transcript_embed, file=transcript_file)


async def generate_transcript(channel):
    # noinspection PyBroadException
    try:
        transcript = await produce_transcript(channel)
    except Exception:
        transcript = None
        print(f"Please send a screenshot of the above error to https://www.github.com/mahtoid/DiscordChatExporterPy")

    return transcript


async def produce_transcript(channel):
    guild = channel.guild
    messages = await channel.history(limit=None, oldest_first=True).flatten()
    previous_author = 0
    previous_timestamp = ""
    messages_html = ""
    for m in messages:
        time_format = "%b %d, %Y %I:%M %p"
        time_string = utc.localize(m.created_at).astimezone(eastern)
        time_string_created = time_string.strftime(time_format)
        if m.edited_at is not None:
            time_string_edited = utc.localize(m.edited_at).astimezone(eastern)
            time_string_edited = time_string_edited.strftime(time_format)
            time_string_final = "%s (edited %s)" \
                                % (time_string_created, time_string_edited)
        else:
            time_string_final = time_string_created

        m.content = await escape_html(m.content)
        m.content = re.sub(r"\n", "<br>", m.content)

        embeds = ""
        for e in m.embeds:
            fields = ""
            for f in e.fields:
                if f.inline:
                    cur_field = await fill_out(channel, msg_embed_field_inline, [
                        ("EMBED_FIELD_NAME", f.name),
                        ("EMBED_FIELD_VALUE", f.value),
                    ])
                    fields += cur_field
                else:
                    cur_field = await fill_out(channel, msg_embed_field, [
                        ("EMBED_FIELD_NAME", f.name),
                        ("EMBED_FIELD_VALUE", f.value),
                    ])
                    fields += cur_field

            # default values for embeds need explicit setting because
            # Embed.empty breaks just about everything
            title = e.title \
                if e.title != discord.Embed.Empty \
                else ""
            r, g, b = (e.colour.r, e.colour.g, e.colour.b) \
                if e.colour != discord.Embed.Empty \
                else (0x20, 0x22, 0x25)  # default colour
            desc = e.description \
                if e.description != discord.Embed.Empty \
                else ""
            author = e.author.name \
                if e.author.name != discord.Embed.Empty \
                else ""
            footer = e.footer.text \
                if e.footer.text != discord.Embed.Empty \
                else ""
            footer_icon = e.footer.icon_url \
                if e.footer.icon_url != discord.Embed.Empty \
                else None

            thumbnail = e.thumbnail.url \
                if e.thumbnail.url != discord.Embed.Empty \
                else ""

            image = e.image.url \
                if e.image.url != discord.Embed.Empty \
                else ""

            if image != "":
                image = await fill_out(channel, embed_image, [
                    ("EMBED_IMAGE", str(image)),
                ])

            if thumbnail != "":
                thumbnail = await fill_out(channel, embed_thumbnail, [
                    ("EMBED_THUMBNAIL", str(thumbnail)),
                ])

            footer_fields = ""
            if footer != "":
                if footer_icon:
                    cur_footer = await fill_out(channel, embed_footer_image, [
                        ("EMBED_FOOTER", footer),
                        ("EMBED_FOOTER_ICON", footer_icon)
                    ])
                else:
                    cur_footer = await fill_out(channel, embed_footer, [
                        ("EMBED_FOOTER", footer),
                    ])
                footer_fields += cur_footer

            cur_embed = await fill_out(channel, msg_embed, [
                ("EMBED_R", str(r)),
                ("EMBED_G", str(g)),
                ("EMBED_B", str(b)),
                ("EMBED_AUTHOR", author, PARSE_MODE_EMBED_EMOJI),
                ("EMBED_TITLE", title, PARSE_MODE_EMBED_EMOJI),
                ("EMBED_IMAGE", image),
                ("EMBED_THUMBNAIL", thumbnail),
                ("EMBED_DESC", desc, PARSE_MODE_EMBED),
                ("EMBED_FIELDS", fields, PARSE_MODE_EMBED_VALUE),
                ("EMBED_FOOTER", footer_fields, PARSE_MODE_EMBED_EMOJI)
            ])
            embeds += cur_embed

        attachments = ""

        for a in m.attachments:
            result_img = False
            for ending in img_types:
                if str(a.url).endswith(ending):
                    result_img = True

            if result_img:
                cur_attach = await fill_out(channel, img_attachment, [
                    ("ATTACH_URL", a.url),
                    ("ATTACH_URL_THUMB", a.url)
                ])
            else:
                file_mb = a.size / 1000000
                cur_attach = await fill_out(channel, msg_attachment, [
                    ("ATTACH_URL", a.url),
                    ("ATTACH_BYTES", str(file_mb)[:4] + "MB"),
                    ("ATTACH_FILE", str(a.filename))
                ])
            attachments += cur_attach

        if m.author.bot:
            ze_bot_tag = bot_tag
        else:
            ze_bot_tag = ""

        output = []
        if "http://" in m.content or "www." in m.content or "https://" in m.content:
            for word in m.content.split():
                if word.startswith("&lt;") and word.endswith("&gt;"):
                    pattern = r"&lt;(.*)&gt;"
                    url = re.search(pattern, word).group(1)
                    url = f'<a href="{url}">{url}</a>'
                    output.append(url)
                elif "http://" in word:
                    pattern = r"http://(.*)"
                    word_link = re.search(pattern, word).group(1)
                    word_full = f'<a href="http://{word_link}">http://{word_link}</a>'
                    word = re.sub(pattern, word_full, word)
                    output.append(word)
                elif "www." in word:
                    pattern = r"www.(.*)"
                    word_link = re.search(pattern, word).group(1)
                    word_full = f'<a href="www.{word_link}">www.{word_link}</a>'
                    word = re.sub(pattern, word_full, word)
                    output.append(word)
                elif "https://" in word:
                    pattern = r"https://(.*)"
                    word_link = re.search(pattern, word).group(1)
                    word_full = f'<a href="https://{word_link}">https://{word_link}</a>'
                    word = re.sub(pattern, word_full, word)
                    output.append(word)
                else:
                    output.append(word)
            m.content = " ".join(output)

        emojis = ""
        for reactions in m.reactions:
            react_emoji = reactions.emoji
            if react_emoji == "":
                emojis += ""
            elif ":" in str(react_emoji):
                emoji_animated = re.compile(r"&lt;a:.*:.*&gt;")
                if emoji_animated.search(str(react_emoji)):
                    file_ending = "gif"
                else:
                    file_ending = "png"
                pattern = r":.*:(\d*)"
                emoji_id = re.search(pattern, str(react_emoji)).group(1)
                cur_custom_emoji = await fill_out(channel, custom_emoji, [
                    ("EMOJI", str(emoji_id)),
                    ("EMOJI_COUNT", str(reactions.count)),
                    ("EMOJI_FILE", file_ending)
                ])
                emojis += cur_custom_emoji
            else:
                react_emoji = convert_emoji(react_emoji)
                cur_emoji = await fill_out(channel, emoji, [
                    ("EMOJI", str(react_emoji)),
                    ("EMOJI_COUNT", str(reactions.count))
                ])
                emojis += cur_emoji

        m.content = await parse_emoji(m.content)

        cur_msg = ""

        author_name = await escape_html(m.author.display_name)

        user_colour = await member_colour_translator(m.author)
        if previous_author == m.author.id and previous_timestamp > time_string:
            cur_msg = await fill_out(channel, continue_message, [
                ("AVATAR_URL", str(m.author.avatar_url)),
                ("NAME_TAG", "%s#%s" % (m.author.name, m.author.discriminator)),
                ("USER_ID", str(m.author.id)),
                ("NAME", str(author_name)),
                ("BOT_TAG", ze_bot_tag, PARSE_MODE_NONE),
                ("TIMESTAMP", time_string_final),
                ("MESSAGE_ID", str(m.id)),
                ("MESSAGE_CONTENT", m.content),
                ("EMBEDS", embeds, PARSE_MODE_NONE),
                ("ATTACHMENTS", attachments, PARSE_MODE_NONE),
                ("EMOJI", emojis)
            ])
        else:
            if previous_author != 0 and previous_timestamp != "":
                cur_msg = await fill_out(channel, end_message, [])
            cur_msg += await fill_out(channel, msg, [
                ("AVATAR_URL", str(m.author.avatar_url)),
                ("NAME_TAG", "%s#%s" % (m.author.name, m.author.discriminator)),
                ("USER_ID", str(m.author.id)),
                ("USER_COLOUR", user_colour),
                ("NAME", str(author_name)),
                ("BOT_TAG", ze_bot_tag, PARSE_MODE_NONE),
                ("TIMESTAMP", time_string_final),
                ("MESSAGE_ID", str(m.id)),
                ("MESSAGE_CONTENT", m.content),
                ("EMBEDS", embeds, PARSE_MODE_NONE),
                ("ATTACHMENTS", attachments, PARSE_MODE_NONE),
                ("EMOJI", emojis)
            ])
            previous_author = m.author.id
            previous_timestamp = time_string + timedelta(minutes=4)

        messages_html += cur_msg

    guild_icon = guild.icon_url
    if len(guild_icon) < 2:
        guild_icon = "https://discord.com/assets/dd4dbc0016779df1378e7812eabaa04d.png"
    guild_name = await escape_html(guild.name)
    transcript = await fill_out(channel, total, [
        ("SERVER_NAME", f"Guild: {guild_name}"),
        ("SERVER_AVATAR_URL", str(guild_icon), PARSE_MODE_NONE),
        ("CHANNEL_NAME", f"Channel: {channel.name}"),
        ("MESSAGE_COUNT", str(len(messages))),
        ("MESSAGES", messages_html, PARSE_MODE_NONE),
        ("TIMEZONE", str(eastern)),
    ])

    return transcript


PARSE_MODE_NONE = 0
PARSE_MODE_NO_MARKDOWN = 1
PARSE_MODE_MARKDOWN = 2
PARSE_MODE_EMBED = 3
PARSE_MODE_EMBED_VALUE = 4
PARSE_MODE_EMBED_EMOJI = 5


async def fill_out(channel, base, replacements):
    for r in replacements:
        if len(r) == 2:  # default case
            k, v = r
            r = (k, v, PARSE_MODE_MARKDOWN)

        k, v, mode = r

        if mode != PARSE_MODE_NONE:
            v = await escape_mentions(v)
            v = await escape_mentions(v)
            v = await unescape_mentions(v)
            v = await parse_mentions(v, channel.guild, bot)
        if mode == PARSE_MODE_MARKDOWN:
            v = await parse_markdown(v)
        if mode == PARSE_MODE_EMBED:
            v = await parse_embed_markdown(v)
            v = await parse_emoji(v)
            v = await parse_markdown(v)
        if mode == PARSE_MODE_EMBED_VALUE:
            v = await parse_embed_markdown(v)
            v = await parse_emoji(v)
        if mode == PARSE_MODE_EMBED_EMOJI:
            v = await parse_emoji(v)

        base = base.replace("{{" + k + "}}", v)

    return base


def read_file(filename):
    with open(filename, "r") as f:
        s = f.read()
    return s


img_types = [".png", ".jpeg", ".jpg", ".gif"]
total = read_file(dir_path + "/chat_exporter_html/base.html")
msg = read_file(dir_path + "/chat_exporter_html/message.html")
bot_tag = read_file(dir_path + "/chat_exporter_html/bot-tag.html")
msg_embed = read_file(dir_path + "/chat_exporter_html/message-embed.html")
msg_embed_field = read_file(dir_path + "/chat_exporter_html/message-embed-field.html")
msg_embed_field_inline = read_file(dir_path + "/chat_exporter_html/message-embed-field-inline.html")
img_attachment = read_file(dir_path + "/chat_exporter_html/image-attachment.html")
msg_attachment = read_file(dir_path + "/chat_exporter_html/message_attachment.html")
emoji = read_file(dir_path + "/chat_exporter_html/emoji_attachment.html")
custom_emoji = read_file(dir_path + "/chat_exporter_html/custom_emoji_attachment.html")
continue_message = read_file(dir_path + "/chat_exporter_html/continue_message.html")
end_message = read_file(dir_path + "/chat_exporter_html/end_message.html")
embed_footer = read_file(dir_path + "/chat_exporter_html/embed_footer.html")
embed_footer_image = read_file(dir_path + "/chat_exporter_html/embed_footer_image.html")
embed_image = read_file(dir_path + "/chat_exporter_html/embed_image.html")
embed_thumbnail = read_file(dir_path + "/chat_exporter_html/embed_thumbnail.html")
