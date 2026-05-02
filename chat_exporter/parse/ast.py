import datetime
import re
import time
from typing import List

import pytz


class Node:
    def render(self, guild=None, bot=None) -> str:
        raise NotImplementedError()


class TextNode(Node):
    def __init__(self, text: str):
        self.text = text

    def render(self, guild=None, bot=None):
        return self.text


class ContainerNode(Node):
    def __init__(self, children: List[Node]):
        self.children = children

    def render_children(self, guild=None, bot=None):
        return "".join(c.render(guild, bot) for c in self.children)


class BoldNode(ContainerNode):
    def render(self, guild=None, bot=None):
        return f"<strong>{self.render_children(guild, bot)}</strong>"


class ItalicNode(ContainerNode):
    def render(self, guild=None, bot=None):
        return f"<em>{self.render_children(guild, bot)}</em>"


class UnderlineNode(ContainerNode):
    def render(self, guild=None, bot=None):
        return f'<span style="text-decoration: underline">{self.render_children(guild, bot)}</span>'


class StrikethroughNode(ContainerNode):
    def render(self, guild=None, bot=None):
        return f'<span style="text-decoration: line-through">{self.render_children(guild, bot)}</span>'


class SpoilerNode(ContainerNode):
    def render(self, guild=None, bot=None):
        return (
            '<span class="spoiler spoiler--hidden" onclick="showSpoiler(event, this)">'
            f'<span class="spoiler-text">{self.render_children(guild, bot)}</span></span>'
        )


class InlineCodeNode(Node):
    def __init__(self, code: str):
        self.code = code

    def render(self, guild=None, bot=None):
        return f'<span class="pre pre-inline">{self.code}</span>'


class CodeBlockNode(Node):
    def __init__(self, lang: str, code: str):
        self.lang = lang
        self.code = code

    def render(self, guild=None, bot=None):
        lang_class = f"language-{self.lang}" if self.lang else "nohighlight"
        return f'<div class="pre pre--multiline {lang_class}">{self.code}</div>'


class QuoteNode(ContainerNode):
    def render(self, guild=None, bot=None):
        return (
            '<div class="quote"><div style="min-width: 0; flex: 1;">'
            f"{self.render_children(guild, bot)}</div></div>"
        )



class HeaderNode(ContainerNode):
    def __init__(self, level: int, children: List[Node]):
        super().__init__(children)
        self.level = level

    def render(self, guild=None, bot=None):
        return f"<h{self.level}>{self.render_children(guild, bot)}</h{self.level}>"


class SubtextNode(ContainerNode):
    def render(self, guild=None, bot=None):
        return f"<small>{self.render_children(guild, bot)}</small>"


class LinkNode(ContainerNode):
    def __init__(self, url: str, children: List[Node]):
        super().__init__(children)
        self.url = url

    def render(self, guild=None, bot=None):
        return f'<a href="{self.url}">{self.render_children(guild, bot)}</a>'


class HtmlNode(Node):
    def __init__(self, raw: str):
        self.raw = raw

    def render(self, guild=None, bot=None):
        return self.raw


class ListItemNode(ContainerNode):
    def __init__(self, indent_level: int, children: List[Node]):
        super().__init__(children)
        self.indent_level = indent_level

    def render(self, guild=None, bot=None):
        return f'<li class="markup">{self.render_children(guild, bot)}</li>'


class ListBlockNode(ContainerNode):
    def render(self, guild=None, bot=None):
        html = '<ul class="markup" style="padding-left: 20px;margin: 0 !important">\n'
        indent_stack = [0]

        for item in self.children:
            if not isinstance(item, ListItemNode):
                continue
            indent = item.indent_level

            if indent % 2 == 0:
                while indent < indent_stack[-1]:
                    html += "</ul>\n"
                    indent_stack.pop()
                if indent > indent_stack[-1]:
                    html += '<ul class="markup">\n'
                    indent_stack.append(indent)
            else:
                while indent + 1 < indent_stack[-1]:
                    html += "</ul>\n"
                    indent_stack.pop()
                if indent + 1 > indent_stack[-1]:
                    html += '<ul class="markup">\n'
                    indent_stack.append(indent + 1)

            html += item.render(guild, bot) + "\n"

        while len(indent_stack) > 1:
            html += "</ul>\n"
            indent_stack.pop()
        html += "</ul>"
        return html


class ChannelMentionNode(Node):
    def __init__(self, channel_id: int):
        self.channel_id = channel_id

    def render(self, guild=None, bot=None):
        channel = guild.get_channel(self.channel_id) if guild else None
        if channel is None:
            return "#deleted-channel"
        return f'<span class="mention" title="{channel.id}">#{channel.name}</span>'


class UserMentionNode(Node):
    ESCAPE_LT = "______lt______"
    ESCAPE_GT = "______gt______"
    ESCAPE_AMP = "______amp______"

    def __init__(self, user_id: int):
        self.user_id = user_id

    def render(self, guild=None, bot=None):
        member = None
        if guild:
            member = guild.get_member(self.user_id)
        if not member and bot:
            member = bot.get_user(self.user_id)

        if member:
            member_name = member.display_name
            escaped_name = (
                member_name.replace("<", self.ESCAPE_LT)
                .replace(">", self.ESCAPE_GT)
                .replace("&", self.ESCAPE_AMP)
            )
            return f'<span class="mention" title="{self.user_id}">@{escaped_name}</span>'
        else:
            return f'<span class="mention" title="{self.user_id}">&lt;@{self.user_id}&gt;</span>'


class RoleMentionNode(Node):
    def __init__(self, role_id: int):
        self.role_id = role_id

    def render(self, guild=None, bot=None):
        role = guild.get_role(self.role_id) if guild else None
        if role is None:
            return "@deleted-role"
        if role.color.r == 0 and role.color.g == 0 and role.color.b == 0:
            colour = "#dee0fc"
        else:
            colour = "#%02x%02x%02x" % (role.color.r, role.color.g, role.color.b)
        return f'<span style="color: {colour};">@{role.name}</span>'


class EveryoneMentionNode(Node):
    def render(self, guild=None, bot=None):
        return '<span class="mention" title="everyone">@everyone</span>'


class HereMentionNode(Node):
    def render(self, guild=None, bot=None):
        return '<span class="mention" title="here">@here</span>'


class SlashCommandNode(Node):
    def __init__(self, name: str):
        self.name = name

    def render(self, guild=None, bot=None):
        return f'<span class="mention" title="{self.name}">/{self.name}</span>'


class TimeMentionNode(Node):
    CYCLE_SECONDS = 12_622_780_800

    def __init__(self, timestamp: int, format_str: str, original: str):
        self.timestamp = timestamp
        self.format_str = format_str
        self.original = original

    def render(self, guild=None, bot=None):
        timestamp = self.timestamp - 1
        try:
            time_stamp = time.gmtime(timestamp)
            datetime_stamp = datetime.datetime(2010, *time_stamp[1:6], tzinfo=pytz.utc)
            ui_time = datetime_stamp.strftime(self.format_str).replace(
                str(datetime_stamp.year), str(time_stamp[0])
            )
            tooltip_time = datetime_stamp.strftime("%A, %e %B %Y at %H:%M").replace(
                str(datetime_stamp.year), str(time_stamp[0])
            )
        except (OSError, OverflowError, ValueError):
            safe_ts = timestamp % self.CYCLE_SECONDS
            years_shifted = (timestamp // self.CYCLE_SECONDS) * 400
            dt = datetime.datetime.fromtimestamp(safe_ts, pytz.utc)
            final_year = dt.year + years_shifted
            ui_time = dt.strftime(self.format_str).replace(str(dt.year), str(final_year))
            tooltip_time = dt.strftime("%A, %e %B %Y at %H:%M").replace(
                str(dt.year), str(final_year)
            )

        original_escaped = self.original.replace("<", "&lt;").replace(">", "&gt;")
        return (
            f'<span class="unix-timestamp" data-timestamp="{tooltip_time}" raw-content="{original_escaped}">'
            f"{ui_time}"
            "</span>"
        )


class AstParser:
    def parse(self, text: str) -> List[Node]:
        if not text:
            return []
        nodes = self._parse_inline(str(text))
        nodes = self._merge_text_nodes(nodes)
        nodes = self._merge_quote_nodes(nodes)
        nodes = self._merge_list_nodes(nodes)
        return nodes

    def _parse_inline(self, text: str) -> List[Node]:
        nodes = []
        i = 0
        n = len(text)

        while i < n:
            # Check HTML and Mentions
            if text[i] == "<" or (text[i : i + 4] == "&lt;"):
                is_escaped = text[i] == "&"

                # Channel
                chan_match = re.match(r"&lt;#([0-9]+)&gt;" if is_escaped else r"<#([0-9]+)>", text[i:])
                if chan_match:
                    nodes.append(ChannelMentionNode(int(chan_match.group(1))))
                    i += len(chan_match.group(0))
                    continue

                # Role
                role_match = re.match(r"&lt;@&amp;([0-9]+)&gt;" if is_escaped else r"<@&([0-9]+)>", text[i:])
                if role_match:
                    nodes.append(RoleMentionNode(int(role_match.group(1))))
                    i += len(role_match.group(0))
                    continue

                # Member
                mem_match = re.match(r"&lt;@!?([0-9]+)&gt;" if is_escaped else r"<@!?([0-9]+)>", text[i:])
                if mem_match:
                    nodes.append(UserMentionNode(int(mem_match.group(1))))
                    i += len(mem_match.group(0))
                    continue

                # Slash Command
                slash_match = re.match(
                    r"&lt;\/([\w]+ ?[\w]*):[0-9]+&gt;" if is_escaped else r"<\/([\w]+ ?[\w]*):[0-9]+>",
                    text[i:],
                )
                if slash_match:
                    nodes.append(SlashCommandNode(slash_match.group(1)))
                    i += len(slash_match.group(0))
                    continue

                # Time
                time_patterns = [
                    [r"&lt;t:([0-9]{1,13}):t&gt;", "%H:%M"],
                    [r"&lt;t:([0-9]{1,13}):T&gt;", "%T"],
                    [r"&lt;t:([0-9]{1,13}):d&gt;", "%d/%m/%Y"],
                    [r"&lt;t:([0-9]{1,13}):D&gt;", "%e %B %Y"],
                    [r"&lt;t:([0-9]{1,13}):f&gt;", "%e %B %Y %H:%M"],
                    [r"&lt;t:([0-9]{1,13}):F&gt;", "%A, %e %B %Y %H:%M"],
                    [r"&lt;t:([0-9]{1,13}):R&gt;", "%e %B %Y %H:%M"],
                    [r"&lt;t:([0-9]{1,13})&gt;", "%e %B %Y %H:%M"],
                ] if is_escaped else [
                    [r"<t:([0-9]{1,13}):t>", "%H:%M"],
                    [r"<t:([0-9]{1,13}):T>", "%T"],
                    [r"<t:([0-9]{1,13}):d>", "%d/%m/%Y"],
                    [r"<t:([0-9]{1,13}):D>", "%e %B %Y"],
                    [r"<t:([0-9]{1,13}):f>", "%e %B %Y %H:%M"],
                    [r"<t:([0-9]{1,13}):F>", "%A, %e %B %Y %H:%M"],
                    [r"<t:([0-9]{1,13}):R>", "%e %B %Y %H:%M"],
                    [r"<t:([0-9]{1,13})>", "%e %B %Y %H:%M"],
                ]
                time_found = False
                for pattern, strf in time_patterns:
                    t_match = re.match(pattern, text[i:])
                    if t_match:
                        nodes.append(TimeMentionNode(int(t_match.group(1)), strf, t_match.group(0)))
                        i += len(t_match.group(0))
                        time_found = True
                        break
                if time_found:
                    continue

                # HTML fallback
                if text[i] == "<":
                    tag_match = re.match(r"(<[^>]+>)", text[i:])
                    if tag_match:
                        nodes.append(HtmlNode(tag_match.group(1)))
                        i += len(tag_match.group(1))
                        continue

            # Newline handler (crucial to restart cursor for block elements)
            if text[i] == "\n":
                nodes.append(TextNode("\n"))
                i += 1
                continue

            # Code block ```
            if text[i : i + 3] == "```":
                endtag = text.find("```", i + 3)
                if endtag != -1:
                    inner = text[i + 3 : endtag]
                    lines = inner.split("\n", 1)
                    if len(lines) > 1 and " " not in lines[0]:
                        lang = lines[0]
                        code = lines[1]
                    else:
                        lang = ""
                        code = inner
                    if code.startswith("\n"):
                        code = code[1:]
                    if code.endswith("\n"):
                        code = code[:-1]
                    nodes.append(CodeBlockNode(lang, code))
                    i = endtag + 3
                    continue

            # Code block ``
            if text[i : i + 2] == "``":
                endtag = text.find("``", i + 2)
                if endtag != -1:
                    nodes.append(InlineCodeNode(text[i + 2 : endtag]))
                    i = endtag + 2
                    continue

            # Inline code `
            if text[i] == "`":
                endtag = text.find("`", i + 1)
                if endtag != -1:
                    nodes.append(InlineCodeNode(text[i + 1 : endtag]))
                    i = endtag + 1
                    continue

            # Bold
            if text[i : i + 2] == "**":
                endtag = text.find("**", i + 2)
                if endtag != -1:
                    nodes.append(BoldNode(self._parse_inline(text[i + 2 : endtag])))
                    i = endtag + 2
                    continue

            # Underline
            if text[i : i + 2] == "__":
                endtag = text.find("__", i + 2)
                if endtag != -1:
                    nodes.append(UnderlineNode(self._parse_inline(text[i + 2 : endtag])))
                    i = endtag + 2
                    continue

            # Strikethrough
            if text[i : i + 2] == "~~":
                endtag = text.find("~~", i + 2)
                if endtag != -1:
                    nodes.append(StrikethroughNode(self._parse_inline(text[i + 2 : endtag])))
                    i = endtag + 2
                    continue

            # Spoiler
            if text[i : i + 2] == "||":
                endtag = text.find("||", i + 2)
                if endtag != -1:
                    nodes.append(SpoilerNode(self._parse_inline(text[i + 2 : endtag])))
                    i = endtag + 2
                    continue

            # Italic 1
            if text[i] == "*":
                endtag = text.find("*", i + 1)
                if endtag != -1 and text[i : i + 2] != "**":
                    nodes.append(ItalicNode(self._parse_inline(text[i + 1 : endtag])))
                    i = endtag + 1
                    continue

            # Italic 2
            if text[i] == "_":
                endtag = text.find("_", i + 1)
                # Ensure it's not part of __ and ideally isolated, but basic parse for discord
                if endtag != -1 and text[i : i + 2] != "__":
                    nodes.append(ItalicNode(self._parse_inline(text[i + 1 : endtag])))
                    i = endtag + 1
                    continue

            # Everyone / Here
            if text[i] == "@":
                everyone_match = re.match(r"@(everyone)(?:[$\s\t\n\f\r\0]|$)", text[i:])
                if everyone_match:
                    nodes.append(EveryoneMentionNode())
                    i += 9  # len("@everyone")
                    continue
                here_match = re.match(r"@(here)(?:[$\s\t\n\f\r\0]|$)", text[i:])
                if here_match:
                    nodes.append(HereMentionNode())
                    i += 5  # len("@here")
                    continue

            # Headers
            if (i == 0 or text[i - 1] == "\n") and text[i] == "#":
                level_match = re.match(r"^(#{1,3})\s+", text[i:])
                if level_match:
                    level = len(level_match.group(1))
                    prefix_len = len(level_match.group(0))
                    endtag = text.find("\n", i + prefix_len)
                    if endtag == -1:
                        endtag = n
                    nodes.append(HeaderNode(level, self._parse_inline(text[i + prefix_len : endtag])))
                    # consume the trailing newline if present, DO NOT append it so we don't get <br>
                    if endtag < n:
                        i = endtag + 1
                        while i < n and text[i] == "\n":
                            i += 1
                    else:
                        break
                    continue

            # Subtext
            if (i == 0 or text[i - 1] == "\n") and text[i : i + 3] == "-# ":
                endtag = text.find("\n", i + 3)
                if endtag == -1:
                    endtag = n
                nodes.append(SubtextNode(self._parse_inline(text[i + 3 : endtag])))
                if endtag < n:
                    nodes.append(TextNode("\n"))
                    i = endtag + 1
                else:
                    break
                continue

            # Blockquote (>>>)
            if (
                (i == 0 or text[i - 1] == "\n") and
                (text[i : i + 13] == "&gt;&gt;&gt; " or text[i : i + 12] == "&gt;&gt;&gt;")
            ):
                prefix_len = 13 if text[i : i + 13] == "&gt;&gt;&gt; " else 12
                if text[i + prefix_len : i + prefix_len + 4] != "&gt;":
                    nodes.append(QuoteNode(self._parse_inline(text[i + prefix_len :])))
                    break

            # Single line quote (>)
            if (i == 0 or text[i - 1] == "\n") and text[i : i + 5] == "&gt; ":
                prefix_len = 5
                endtag = text.find("\n", i + prefix_len)
                if endtag == -1:
                    endtag = n
                nodes.append(QuoteNode(self._parse_inline(text[i + prefix_len : endtag])))

                if endtag < n:
                    i = endtag + 1
                    continue
                else:
                    break

            # Lists
            if i == 0 or text[i - 1] == "\n":
                list_match = re.match(r"^(\s*)([-*])\s+", text[i:])
                if list_match:
                    indent = len(list_match.group(1))
                    prefix_len = len(list_match.group(0))
                    endtag = text.find("\n", i + prefix_len)
                    if endtag == -1:
                        endtag = n
                    nodes.append(ListItemNode(indent, self._parse_inline(text[i + prefix_len : endtag])))
                    if endtag < n:
                        i = endtag + 1
                    else:
                        break
                    continue

            # Link [text](url)
            if text[i] == "[":
                close_bracket = text.find("](", i + 1)
                if close_bracket != -1:
                    end_paren = text.find(")", close_bracket + 2)
                    if end_paren != -1:
                        link_text = text[i + 1 : close_bracket]
                        link_url = text[close_bracket + 2 : end_paren]
                        nodes.append(LinkNode(link_url, self._parse_inline(link_text)))
                        i = end_paren + 1
                        continue

            # Raw HTTP
            if text[i : i + 4] == "http":
                match = re.search(r"^https?://[^\s<*\n\)]+", text[i:])
                if match:
                    url = match.group(0)
                    nodes.append(LinkNode(url, [TextNode(url)]))
                    i += len(url)
                    continue

            # Fallback consume characters to next special marker
            next_special_options = [
                text.find("<", i + 1),
                text.find("`", i + 1),
                text.find("*", i + 1),
                text.find("_", i + 1),
                text.find("~", i + 1),
                text.find("|", i + 1),
                text.find("[", i + 1),
                text.find("h", i + 1),
                text.find("\n", i + 1),
                text.find("&", i + 1),
                text.find("#", i + 1),
                text.find("-", i + 1),
                text.find("@", i + 1),
            ]
            valid_specials = [pos for pos in next_special_options if pos != -1]
            next_special = min(valid_specials) if valid_specials else n

            if next_special == i:  # rare edge case fallback
                nodes.append(TextNode(text[i]))
                i += 1
            else:
                raw_text = text[i:next_special]
                # small mitigation for missing < inside url but we already parse urls
                nodes.append(TextNode(raw_text))
                i = next_special

        return nodes

    def _merge_text_nodes(self, nodes: List[Node]) -> List[Node]:
        merged = []
        for node in nodes:
            if isinstance(node, TextNode):
                node.text = node.text.replace("\n", "<br>")
                if merged and isinstance(merged[-1], TextNode):
                    merged[-1].text += node.text
                else:
                    merged.append(node)
            else:
                if isinstance(node, ContainerNode):
                    node.children = self._merge_text_nodes(node.children)
                merged.append(node)
        return merged

    def _merge_quote_nodes(self, nodes: List[Node]) -> List[Node]:
        merged = []
        pending_spaces = []
        for node in nodes:
            if isinstance(node, ContainerNode):
                node.children = self._merge_quote_nodes(node.children)

            if isinstance(node, QuoteNode):
                pending_spaces.clear()
                if merged and isinstance(merged[-1], QuoteNode):
                    merged[-1].children.append(TextNode("<br>"))
                    merged[-1].children.extend(node.children)
                else:
                    merged.append(node)
            elif (
                merged
                and isinstance(merged[-1], QuoteNode)
                and isinstance(node, TextNode)
                and node.text.replace("<br>", "").strip() == ""
            ):
                pending_spaces.append(node)
            else:
                if pending_spaces:
                    merged.extend(pending_spaces)
                    pending_spaces.clear()
                merged.append(node)
        if pending_spaces:
            merged.extend(pending_spaces)
        return merged

    def _merge_list_nodes(self, nodes: List[Node]) -> List[Node]:
        merged = []
        current_list = []
        pending_spaces = []

        def commit_list():
            if current_list:
                merged.append(ListBlockNode(current_list.copy()))
                current_list.clear()
            if pending_spaces:
                merged.extend(pending_spaces)
                pending_spaces.clear()

        for node in nodes:
            if isinstance(node, ContainerNode):
                node.children = self._merge_list_nodes(node.children)

            if isinstance(node, ListItemNode):
                pending_spaces.clear()
                current_list.append(node)
            elif current_list and isinstance(node, TextNode) and node.text.replace("<br>", "").strip() == "":
                pending_spaces.append(node)
            else:
                commit_list()
                merged.append(node)

        commit_list()
        return merged
