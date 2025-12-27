import html
import re
from chat_exporter.ext.emoji_convert import convert_emoji


class ParseMarkdown:
    def __init__(self, content):
        self.content = content
        self.code_blocks_content = []


    async def standard_message_flow(self):
        self.parse_code_block_markdown()
        self.https_http_links()
        self.parse_embed_markdown()
        self.parse_normal_markdown()

        await self.parse_emoji()
        self.reverse_code_block_markdown()
        return self.content

    async def link_embed_flow(self):
        self.parse_embed_markdown()
        await self.parse_emoji()

    async def standard_embed_flow(self):
        self.parse_code_block_markdown()
        self.https_http_links()
        self.parse_embed_markdown()
        self.parse_normal_markdown()

        await self.parse_emoji()
        self.reverse_code_block_markdown()
        return self.content

    async def special_embed_flow(self):
        self.https_http_links()
        self.parse_code_block_markdown()
        self.parse_normal_markdown()

        await self.parse_emoji()
        self.reverse_code_block_markdown()
        return self.content

    async def message_reference_flow(self):
        self.strip_preserve()
        self.parse_code_block_markdown(reference=True)
        self.https_http_links()
        self.parse_embed_markdown()
        self.parse_normal_markdown()
        self.reverse_code_block_markdown()
        self.parse_br()

        return self.content

    async def special_emoji_flow(self):
        await self.parse_emoji()
        return self.content

    def parse_br(self):
        self.content = self.content.replace("<br>", " ")

    async def parse_emoji(self):
        holder = (
            [r"&lt;:.*?:(\d*)&gt;", '<img class="emoji emoji--small" src="https://cdn.discordapp.com/emojis/%s.png">'],
            [r"&lt;a:.*?:(\d*)&gt;", '<img class="emoji emoji--small" src="https://cdn.discordapp.com/emojis/%s.gif">'],
            [r"<:.*?:(\d*)>", '<img class="emoji emoji--small" src="https://cdn.discordapp.com/emojis/%s.png">'],
            [r"<a:.*?:(\d*)>", '<img class="emoji emoji--small" src="https://cdn.discordapp.com/emojis/%s.gif">'],
        )

        self.content = await convert_emoji([word for word in self.content])

        for x in holder:
            p, r = x
            match = re.search(p, self.content)
            while match is not None:
                emoji_id = match.group(1)
                self.content = self.content.replace(self.content[match.start():match.end()],
                                                    r % emoji_id)
                match = re.search(p, self.content)

    def strip_preserve(self):
        p = r'<span class="chatlog__markdown-preserve">(.*)</span>'
        r = '%s'

        pattern = re.compile(p)
        match = re.search(pattern, self.content)
        while match is not None:
            affected_text = match.group(1)
            self.content = self.content.replace(self.content[match.start():match.end()],
                                                r % affected_text)
            match = re.search(pattern, self.content)

    def order_list_markdown_to_html(self):
        lines = self.content.split('\n')
        html = ''
        indent_stack = [0]
        started = True

        for line in lines:
            match = re.match(r'^(\s*)([-*])\s+(.+)$', line)
            if match:
                indent, bullet, content = match.groups()
                indent = len(indent)

                if started:
                    html += '<ul class="markup" style="padding-left: 20px;margin: 0 !important">\n'
                    started = False
                if indent % 2 == 0:
                    while indent < indent_stack[-1]:
                        html += '</ul>\n'
                        indent_stack.pop()
                    if indent > indent_stack[-1]:
                        html += '<ul class="markup">\n'
                        indent_stack.append(indent)
                else:
                    while indent + 1 < indent_stack[-1]:
                        html += '</ul>\n'
                        indent_stack.pop()
                    if indent + 1 > indent_stack[-1]:
                        html += '<ul class="markup">\n'
                        indent_stack.append(indent + 1)

                html += f'<li class="markup">{content.strip()}</li>\n'
            else:
                while len(indent_stack) > 1:
                    html += '</ul>'
                    indent_stack.pop()
                if not started:
                    html += '</ul>'
                    started = True
                html += line + '\n'

        while len(indent_stack) > 1:
            html += '</ul>\n'
            indent_stack.pop()

        self.content = html

    def parse_normal_markdown(self):
        self.order_list_markdown_to_html()
        holder = (
            [r"__(.*?)__", '<span style="text-decoration: underline">%s</span>'],
            [r"\*\*(.*?)\*\*", '<strong>%s</strong>'],
            [r"\*(.*?)\*", '<em>%s</em>'],
            [r"~~(.*?)~~", '<span style="text-decoration: line-through">%s</span>'],
            [r"^###\s(.*?)\n", '<h3>%s</h1>'],
            [r"^##\s(.*?)\n", '<h2>%s</h1>'],
            [r"^#\s(.*?)\n", '<h1>%s</h1>'],
            [r"\|\|(.*?)\|\|", '<span class="spoiler spoiler--hidden" onclick="showSpoiler(event, this)"> <span '
                               'class="spoiler-text">%s</span></span>'],
        )

        for x in holder:
            p, r = x

            pattern = re.compile(p, re.M)
            match = re.search(pattern, self.content)
            while match is not None:
                affected_text = match.group(1)
                self.content = self.content.replace(self.content[match.start():match.end()], r % affected_text)
                match = re.search(pattern, self.content)

        # > quote (group consecutive lines into a single block so the bar spans them)
        self.content = self.merge_quote_lines(self.content)

    def parse_code_block_markdown(self, reference=False):
        markdown_languages = ["asciidoc", "autohotkey", "bash", "coffeescript", "cpp", "cs", "css",
                              "diff", "fix", "glsl", "ini", "json", "md", "ml", "prolog", "py",
                              "tex", "xl", "xml", "js", "html"]
        self.content = re.sub(r"\n", "<br>", self.content)

        # ```code```
        pattern = re.compile(r"```(.*?)```")
        match = re.search(pattern, self.content)
        while match is not None:
            language_class = "nohighlight"
            affected_text = match.group(1)

            for language in markdown_languages:
                if affected_text.lower().startswith(language):
                    language_class = f"language-{language}"
                    _, _, affected_text = affected_text.partition('<br>')

            affected_text = self.return_to_markdown(affected_text)

            second_pattern = re.compile(r"^<br>|<br>$")
            second_match = re.search(second_pattern, affected_text)
            while second_match is not None:
                affected_text = re.sub(r"^<br>|<br>$", '', affected_text)
                second_match = re.search(second_pattern, affected_text)
            affected_text = re.sub("  ", "&nbsp;&nbsp;", affected_text)

            self.code_blocks_content.append(affected_text)
            if not reference:
                self.content = self.content.replace(
                    self.content[match.start():match.end()],
                    '<div class="pre pre--multiline %s">%s</div>' % (language_class, f'%s{len(self.code_blocks_content)}')
                )
            else:
                self.content = self.content.replace(
                    self.content[match.start():match.end()],
                    '<span class="pre pre-inline">%s</span>' % f'%s{len(self.code_blocks_content)}'
                )

            match = re.search(pattern, self.content)

        # ``code``
        pattern = re.compile(r"``(.*?)``")
        match = re.search(pattern, self.content)
        while match is not None:
            affected_text = match.group(1)
            affected_text = self.return_to_markdown(affected_text)
            self.code_blocks_content.append(affected_text)
            self.content = self.content.replace(self.content[match.start():match.end()],
                                                '<span class="pre pre-inline">%s</span>' % f'%s{len(self.code_blocks_content)}')
            match = re.search(pattern, self.content)

        # `code`
        pattern = re.compile(r"`(.*?)`")
        match = re.search(pattern, self.content)
        while match is not None:
            affected_text = match.group(1)
            affected_text = self.return_to_markdown(affected_text)
            self.code_blocks_content.append(affected_text)
            self.content = self.content.replace(self.content[match.start():match.end()],
                                                '<span class="pre pre-inline">%s</span>' % f'%s{len(self.code_blocks_content)}')
            match = re.search(pattern, self.content)

        self.content = re.sub(r"<br>", "\n", self.content)

    def reverse_code_block_markdown(self):
        for x in range(len(self.code_blocks_content)):
            self.content = self.content.replace(f'%s{x + 1}', self.code_blocks_content[x])

    def parse_embed_markdown(self):
        # [Message](Link)
        pattern = re.compile(r"\[(.+?)]\((https?://[^\s)]+)\)")
        match = re.search(pattern, self.content)
        while match is not None:
            affected_text = match.group(1)
            affected_url = match.group(2)
            self.content = self.content.replace(self.content[match.start():match.end()],
                                                '<a href="%s">%s</a>' % (affected_url, affected_text))
            match = re.search(pattern, self.content)

        self.content = self.merge_quote_lines(self.content)

    @staticmethod
    def order_list_html_to_markdown(content):
        lines = content.split('<br>')
        html = ''
        ul_level = -1

        for line in lines:
            if '<ul class="markup">' in line:
                ul_level += 1
                line = line.replace('<ul class="markup">', '')
                if line != "":
                    html += line + "\n"
            elif "</ul>" in line:
                ul_level -= 1
            elif '<li class="markup">' in line:
                match = re.match(r'<li class="markup">(.+?)</li>', line)
                if match:
                    matched_content = match.group(1)
                    spaces = ul_level * 2
                    html += " " * spaces + "-" + matched_content + "\n"
                else:
                    html += line
            else:
                html += line

        return html

    def return_to_markdown(self, content):
        # content = self.order_list_html_to_markdown(content)
        holders = (
            [r"<strong>(.*?)</strong>", '**%s**'],
            [r"<em>([^<>]+)</em>", '*%s*'],
            [r"<h1>([^<>]+)</h1>", '# %s'],
            [r"<h2>([^<>]+)</h2>", '## %s'],
            [r"<h3>([^<>]+)</h3>", '### %s'],
            [r'<span style="text-decoration: underline">([^<>]+)</span>', '__%s__'],
            [r'<span style="text-decoration: line-through">([^<>]+)</span>', '~~%s~~'],
            [r'<div class="quote">(.*?)</div>', '> %s'],
            [r'<span class="spoiler spoiler--hidden" onclick="showSpoiler\(event, this\)"> <span '
             r'class="spoiler-text">(.*?)<\/span><\/span>', '||%s||'],
            [r'<span class="unix-timestamp" data-timestamp=".*?" raw-content="(.*?)">.*?</span>', '%s']
        )

        for x in holders:
            p, r = x

            pattern = re.compile(p)
            match = re.search(pattern, content)
            while match is not None:
                affected_text = match.group(1)
                content = content.replace(content[match.start():match.end()],
                                          r % html.escape(affected_text))
                match = re.search(pattern, content)

        pattern = re.compile(r'<a href="(.*?)">(.*?)</a>')
        match = re.search(pattern, content)
        while match is not None:
            affected_url = match.group(1)
            affected_text = match.group(2)
            if affected_url != affected_text:
                content = content.replace(content[match.start():match.end()],
                                          '[%s](%s)' % (affected_text, affected_url))
            else:
                content = content.replace(content[match.start():match.end()],
                                          '%s' % affected_url)
            match = re.search(pattern, content)

        return content.lstrip().rstrip()

    @staticmethod
    def merge_quote_lines(content: str) -> str:
        """
        Convert consecutive blockquote-style lines into a single quote block so the visual bar spans all lines.
        """
        lines = content.split("\n")
        merged_content = []
        quote_buffer = []
        quote_pattern = re.compile(r"^(?:&gt;|>)\s?(.*)")

        for line in lines:
            match = quote_pattern.match(line)
            if match:
                quote_buffer.append(match.group(1))
            else:
                if quote_buffer:
                    merged_content.append(f'<div class="quote">{"\n".join(quote_buffer)}</div>')
                    quote_buffer = []
                merged_content.append(line)

        if quote_buffer:
            merged_content.append(f'<div class="quote">{"\n".join(quote_buffer)}</div>')

        merged = "\n".join(merged_content)
        # Remove a single trailing newline after a quote block; the block element already provides separation.
        merged = re.sub(r"</div>[ \t]*\n(?!\n)", "</div>", merged)
        return merged

    def https_http_links(self):
        def remove_silent_link(url, raw_url=None):
            pattern = rf"`.*{raw_url}.*`"
            match = re.search(pattern, self.content)

            if "&lt;" in url and "&gt;" in url and not match:
                return url.replace("&lt;", "").replace("&gt;", "")
            return url

        content = re.sub("\n", "<br>", self.content)
        output = []
        if "http://" in content or "https://" in content:
            for word in content.replace("<br>", " <br>").split():

                # Skip markdown links to avoid wrapping the URL twice
                if "](" in word:
                    output.append(word)
                    continue

                if "http" not in word:
                    output.append(word)
                    continue

                if "&lt;" in word and "&gt;" in word:
                    pattern = r"&lt;https?:\/\/(.*)&gt;"
                    match_url = re.search(pattern, word)
                    if match_url:
                        match_url = match_url.group(1)
                        url = f'<a href="https://{match_url}">https://{match_url}</a>'
                        word = word.replace("https://" + match_url, url)
                        word = word.replace("http://" + match_url, url)
                    output.append(remove_silent_link(word, match_url))
                elif "https://" in word:
                    pattern = r"https://[^\s>`\"*]*"
                    word_link = re.search(pattern, word)
                    if word_link and word_link.group().endswith(")"):
                        output.append(word)
                        continue
                    elif word_link:
                        word_link = word_link.group()
                        word_full = f'<a href="{word_link}">{word_link}</a>'
                        word = re.sub(pattern, word_full, word)
                    output.append(remove_silent_link(word))
                elif "http://" in word:
                    pattern = r"http://[^\s>`\"*]*"
                    word_link = re.search(pattern, word)
                    if word_link and word_link.group().endswith(")"):
                        output.append(word)
                        continue
                    elif word_link:
                        word_link = word_link.group()
                        word_full = f'<a href="{word_link}">{word_link}</a>'
                        word = re.sub(pattern, word_full, word)
                    output.append(remove_silent_link(word))
                else:
                    output.append(word)
            content = " ".join(output)
            self.content = re.sub("<br>", "\n", content)