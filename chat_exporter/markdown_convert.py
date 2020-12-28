import re
from chat_exporter.emoji_convert import convert_emoji
from chat_exporter.misc_tools import escape_html


async def parse_emoji(content):
    content = re.sub(r"\n", "<br>", content)

    emoji_pattern = re.compile(r"&lt;:.*:(\d*)&gt;")
    emoji_animated = re.compile(r"&lt;a:.*:(\d*)&gt;")
    match = re.search(emoji_pattern, content)
    while match is not None:
        emoji_id = match.group(1)
        content = content.replace(content[match.start():match.end()],
                                  f'<img class="emoji emoji--small" src="https://cdn.discordapp.com/'
                                  f'emojis/{str(emoji_id)}.png">')
        match = re.search(emoji_pattern, content)

    match = re.search(emoji_animated, content)
    while match is not None:
        emoji_id = match.group(1)
        content = content.replace(content[match.start():match.end()],
                                  f'<img class="emoji emoji--small" src="https://cdn.discordapp.com/'
                                  f'emojis/{str(emoji_id)}.png">')
        match = re.search(emoji_animated, content)

    content = convert_emoji([word for word in content])
    content = re.sub(r"<br>", "\n", content)
    return content


async def parse_embed_markdown(content):
    # [Message](Link)
    pattern = re.compile(r'<div class="chatlog__embed-field-value"><span class="markdown preserve-whitespace">'
                         r'(.+)?</span></div>')
    match = re.search(pattern, content)
    if not match:
        pattern = re.compile(r"\[(.+)?]\((.+)?\)")
        match = re.search(pattern, content)
        while match is not None:
            affected_text = match.group(1)
            affected_url = match.group(2)
            content = content.replace(content[match.start():match.end()],
                                      '<a href="%s">%s</a>' % (affected_url, affected_text))
            match = re.search(pattern, content)
    if match:
        value_content = match.group(1)
        pattern = re.compile(r'\[(.+)?]\((.+)?\)')
        match = re.search(pattern, value_content)
        while match is not None:
            affected_text = match.group(1)
            affected_url = match.group(2)
            value_content = value_content.replace(value_content[match.start():match.end()],
                                                  '<a href="%s">%s</a>' % (affected_url, affected_text))
            match = re.search(pattern, value_content)

        pattern = re.compile(r'<div class="chatlog__embed-field-value"><span class="markdown preserve-whitespace">'
                             r'(.+)?</span></div>')
        match = re.search(pattern, content)
        content = content.replace(content[match.start():match.end()],
                                  value_content)
    return content


async def parse_markdown(content):
    # **bold**
    pattern = re.compile(r"\*\*(.*?)\*\*")
    match = re.search(pattern, content)
    while match is not None:
        affected_text = match.group(1)
        content = content.replace(content[match.start():match.end()],
                                  '<strong>%s</strong>' % affected_text)
        match = re.search(pattern, content)

    # *italic*
    pattern = re.compile(r"\*(.*?)\*")
    match = re.search(pattern, content)
    while match is not None:
        affected_text = match.group(1)
        content = content.replace(content[match.start():match.end()],
                                  '<em>%s</em>' % affected_text)
        match = re.search(pattern, content)

    # __underline__
    pattern = re.compile(r"__(.*?)__")
    match = re.search(pattern, content)
    while match is not None:
        affected_text = match.group(1)
        content = content.replace(content[match.start():match.end()],
                                  '<span style="text-decoration: underline">%s</span>' % affected_text)
        match = re.search(pattern, content)

    # ~~strikethrough~~
    pattern = re.compile(r"~~(.*?)~~")
    match = re.search(pattern, content)
    while match is not None:
        affected_text = match.group(1)
        content = content.replace(content[match.start():match.end()],
                                  '<span style="text-decoration: line-through">%s</span>' % affected_text)
        match = re.search(pattern, content)

    # ||spoiler||
    pattern = re.compile(r"\|\|(.*?)\|\|")
    match = re.search(pattern, content)
    while match is not None:
        affected_text = match.group(1)
        content = content.replace(content[match.start():match.end()],
                                  '<span class="spoiler spoiler--hidden" onclick="showSpoiler(event, this)">'
                                  '<span class="spoiler-text">%s</span></span>' % affected_text)
        match = re.search(pattern, content)

    # > quote
    pattern = re.compile(r"^&gt;\s(.+)")
    match = re.search(pattern, content)
    while match is not None:
        affected_text = match.group(1)
        br_pattern = re.compile(r"^&gt;\s(.+?)<br>")
        if re.search(br_pattern, content):
            match = re.search(br_pattern, content)
            affected_text = match.group(1)
            content = content.replace(content[match.start():match.end()],
                                      '<div class="quote">%s</div>' % affected_text)
        else:
            content = content.replace(content[match.start():match.end()],
                                      '<div class="quote">%s</div>' % affected_text)
        match = re.search(pattern, content)

    pattern = re.compile(r"<br>&gt;\s(.+)")
    match = re.search(pattern, content)
    while match is not None:
        affected_text = match.group(1)
        br_pattern = re.compile(r"<br>&gt;\s(.+?)<br>")
        if re.search(br_pattern, content):
            match = re.search(br_pattern, content)
            affected_text = match.group(1)
            content = content.replace(content[match.start():match.end()],
                                      '<div class="quote">%s</div>' % affected_text)
        else:
            content = content.replace(content[match.start():match.end()],
                                      '<div class="quote">%s</div>' % affected_text)
        match = re.search(pattern, content)
    content = re.sub(r"\n", "<br>", content)

    # ```code```
    pattern = re.compile(r"```(.*?)```")
    match = re.search(pattern, content)
    while match is not None:
        affected_text = match.group(1)
        if affected_text.lower().startswith(("asciidoc", "autohotkey", "bash", "coffeescript", "cpp", "cs", "css",
                                             "diff", "fix", "glsl", "ini", "json", "md", "ml", "prolog", "py",
                                             "tex", "xl", "xml", "js")):
            affected_text = affected_text.replace("<br>", " <br>")
            affected_text = ' '.join(affected_text.split()[1:])
        affected_text = re.sub(r"^<br>", "", affected_text)
        affected_text = re.sub(r"<br>$", "", affected_text)
        affected_text = await return_to_markdown(affected_text)
        content = content.replace(content[match.start():match.end()],
                                  '<div class="pre pre--multiline nohighlight">%s</div>' % affected_text)
        match = re.search(pattern, content)

    # ``code``
    pattern = re.compile(r"``(.*?)``")
    match = re.search(pattern, content)
    while match is not None:
        affected_text = match.group(1)
        affected_text = await return_to_markdown(affected_text)
        content = content.replace(content[match.start():match.end()],
                                  '<span class="pre pre-inline">%s</span>' % affected_text)
        match = re.search(pattern, content)

    # `code`
    pattern = re.compile(r"`(.*?)`")
    match = re.search(pattern, content)
    while match is not None:
        affected_text = match.group(1)
        affected_text = await return_to_markdown(affected_text)
        content = content.replace(content[match.start():match.end()],
                                  '<span class="pre pre-inline">%s</span>' % affected_text)
        match = re.search(pattern, content)
    content = re.sub(r"<br>", "\n", content)
    return content


async def https_http_links(content):
    content = re.sub("\n", "<br>", content)
    output = []
    if "http://" in content or "https://" in content:
        for word in content.replace("<br>", " <br>").split():
            if word.startswith("&lt;") and word.endswith("&gt;"):
                pattern = r"&lt;(.*)&gt;"
                url = re.search(pattern, word).group(1)
                url = f'<a href="{url}">{url}</a>'
                output.append(url)
            elif "https://" in word:
                pattern = r"https://[^\s<*]*"
                word_link = re.search(pattern, word).group()
                if word_link.endswith(")"):
                    output.append(word)
                    continue
                word_full = f'<a href="{word_link}">{word_link}</a>'
                word = re.sub(pattern, word_full, word)
                output.append(word)
            elif "http://" in word:
                pattern = r"http://[^\s<*]*"
                word_link = re.search(pattern, word).group()
                if word_link.endswith(")"):
                    output.append(word)
                    continue
                word_full = f'<a href="{word_link}">{word_link}</a>'
                word = re.sub(pattern, word_full, word)
                output.append(word)
            else:
                output.append(word)
        content = " ".join(output)
        content = re.sub("<br>", "\n", content)
    return content


async def return_to_markdown(content):
    pattern = re.compile(r"<strong>(.*?)</strong>")
    match = re.search(pattern, content)
    while match is not None:
        affected_text = match.group(1)
        content = content.replace(content[match.start():match.end()],
                                  '**%s**' % affected_text)
        match = re.search(pattern, content)

    pattern = re.compile(r"<em>([^<>]+)</em>")
    match = re.search(pattern, content)
    while match is not None:
        affected_text = match.group(1)
        content = content.replace(content[match.start():match.end()],
                                  '*%s*' % affected_text)
        match = re.search(pattern, content)

    pattern = re.compile(r'<span style="text-decoration: underline">([^<>]+)</span>')
    match = re.search(pattern, content)
    while match is not None:
        affected_text = match.group(1)
        content = content.replace(content[match.start():match.end()],
                                  '__%s__' % affected_text)
        match = re.search(pattern, content)

    pattern = re.compile(r'<span style="text-decoration: line-through">([^<>]+)</span>')
    match = re.search(pattern, content)
    while match is not None:
        affected_text = match.group(1)
        content = content.replace(content[match.start():match.end()],
                                  '~~%s~~' % affected_text)
        match = re.search(pattern, content)

    pattern = re.compile(r'<span class="spoiler spoiler--hidden" onclick="showSpoiler\(event, this\)">'
                         r'<span class="spoiler-text">(.*?)</span></span>')
    match = re.search(pattern, content)
    while match is not None:
        affected_text = match.group(1)
        content = content.replace(content[match.start():match.end()],
                                  '||%s||' % affected_text)
        match = re.search(pattern, content)

    pattern = re.compile(r'<div class="quote">(.*?)</div>')
    match = re.search(pattern, content)
    while match is not None:
        affected_text = match.group(1)
        content = content.replace(content[match.start():match.end()],
                                  '> %s' % affected_text)
        match = re.search(pattern, content)

    pattern = re.compile(r'<a href="(.*?)">(.*?)</a>')
    match = re.search(pattern, content)
    while match is not None:
        affected_url = match.group(1)
        affected_text = match.group(1)
        if affected_url != affected_text:
            content = content.replace(content[match.start():match.end()],
                                      '[%s](%s)' % (affected_text, affected_url))
        else:
            content = content.replace(content[match.start():match.end()],
                                      '%s' % affected_url)

    return content
