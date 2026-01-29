import re
from typing import Optional

import pytz
import datetime
import time

from chat_exporter.ext.discord_import import discord
from chat_exporter.parse.markdown import ParseMarkdown
bot: Optional[discord.Client] = None


def pass_bot(_bot):
    # Bot is used to fetch a user who is no longer inside a guild
    # This will stop the user from appearing as 'Unknown' which some people do not want
    global bot
    bot = _bot


class ParseMention:
    REGEX_ROLES = r"&lt;@&amp;([0-9]+)&gt;"
    REGEX_ROLES_2 = r"<@&([0-9]+)>"
    REGEX_EVERYONE = r"@(everyone)(?:[$\s\t\n\f\r\0]|$)"
    REGEX_HERE = r"@(here)(?:[$\s\t\n\f\r\0]|$)"
    REGEX_MEMBERS = r"&lt;@!?([0-9]+)&gt;"
    REGEX_MEMBERS_2 = r"<@!?([0-9]+)>"
    REGEX_CHANNELS = r"&lt;#([0-9]+)&gt;"
    REGEX_CHANNELS_2 = r"<#([0-9]+)>"
    REGEX_EMOJIS = r"&lt;a?(:[^\n:]+:)[0-9]+&gt;"
    REGEX_EMOJIS_2 = r"<a?(:[^\n:]+:)[0-9]+>"
    REGEX_TIME_HOLDER = (
        [r"&lt;t:([0-9]{1,13}):t&gt;", "%H:%M"],
        [r"&lt;t:([0-9]{1,13}):T&gt;", "%T"],
        [r"&lt;t:([0-9]{1,13}):d&gt;", "%d/%m/%Y"],
        [r"&lt;t:([0-9]{1,13}):D&gt;", "%e %B %Y"],
        [r"&lt;t:([0-9]{1,13}):f&gt;", "%e %B %Y %H:%M"],
        [r"&lt;t:([0-9]{1,13}):F&gt;", "%A, %e %B %Y %H:%M"],
        [r"&lt;t:([0-9]{1,13}):R&gt;", "%e %B %Y %H:%M"],
        [r"&lt;t:([0-9]{1,13})&gt;", "%e %B %Y %H:%M"]
    )
    REGEX_SLASH_COMMAND = r"&lt;\/([\w]+ ?[\w]*):[0-9]+&gt;"
    CYCLE_SECONDS = 12_622_780_800  # Exactly 400 years in seconds
    ESCAPE_LT = "______lt______"
    ESCAPE_GT = "______gt______"
    ESCAPE_AMP = "______amp______"

    def __init__(self, content, guild):
        self.content = content
        self.guild = guild
        self.code_blocks_content = []

    async def flow(self):
        markdown = ParseMarkdown(self.content)
        markdown.parse_code_block_markdown()
        self.content = markdown.content
        await self.escape_mentions()
        await self.escape_mentions()
        await self.unescape_mentions()
        await self.channel_mention()
        await self.member_mention()
        await self.role_mention()
        await self.time_mention()
        await self.slash_command_mention()
        markdown.content = self.content
        markdown.reverse_code_block_markdown()
        self.content = markdown.content
        return self.content


    async def escape_mentions(self):
        content = ""
        previous_match_end = 0
        for match in re.finditer("(%s|%s|%s|%s|%s|%s|%s|%s)"
                                 % (self.REGEX_ROLES, self.REGEX_MEMBERS, self.REGEX_CHANNELS, self.REGEX_EMOJIS,
                                    self.REGEX_ROLES_2, self.REGEX_MEMBERS_2, self.REGEX_CHANNELS_2,
                                    self.REGEX_EMOJIS_2), self.content):
            pre_content = self.content[previous_match_end:match.start()]
            post_content = self.content[match.end():]
            match_content = self.content[match.start():match.end()]
            match_content = await self.escape_mention_starters(match_content)

            content += pre_content + match_content
            previous_match_end = match.end()
        if previous_match_end < len(self.content) - 1:
            content += self.content[previous_match_end:]
        self.content = content

    async def unescape_mentions(self, content: str = None):
        had_content = content is not None
        if content is None:
            content = self.content
        content = content.replace(self.ESCAPE_LT, "<")
        content = content.replace(self.ESCAPE_GT, ">")
        content = content.replace(self.ESCAPE_AMP, "&")
        if not had_content:
            self.content = content
        return content
    
    async def escape_mention_starters(self, content: str = None):
        had_content = content is not None
        if content is None:
            content = self.content
        content = content.replace("<", self.ESCAPE_LT)
        content = content.replace(">", self.ESCAPE_GT)
        content = content.replace("&", self.ESCAPE_AMP)
        if not had_content:
            self.content = content
        return content

    async def channel_mention(self):
        holder = self.REGEX_CHANNELS, self.REGEX_CHANNELS_2
        for regex in holder:
            match = re.search(regex, self.content)
            while match is not None:
                channel_id = int(match.group(1))
                channel = self.guild.get_channel(channel_id)

                if channel is None:
                    replacement = '#deleted-channel'
                else:
                    replacement = '<span class="mention" title="%s">#%s</span>' \
                                  % (channel.id, channel.name)
                self.content = self.content.replace(self.content[match.start():match.end()], replacement)

                match = re.search(regex, self.content)

    async def role_mention(self):
        holder = self.REGEX_EVERYONE, self.REGEX_HERE
        for regex in holder:
            match = re.search(regex, self.content)
            while match is not None:
                role_name = match.group(1)
                replacement = '<span class="mention" title="%s">@%s</span>' % (str(role_name), str(role_name))

                self.content = self.content.replace(self.content[match.start():match.end()],
                                                    replacement)
                match = re.search(regex, self.content)
        holder = self.REGEX_ROLES, self.REGEX_ROLES_2
        for regex in holder:
            match = re.search(regex, self.content)
            while match is not None:
                role_id = int(match.group(1))
                role = self.guild.get_role(role_id)

                if role is None:
                    replacement = '@deleted-role'
                else:
                    if role.color.r == 0 and role.color.g == 0 and role.color.b == 0:
                        colour = "#dee0fc"
                    else:
                        colour = "#%02x%02x%02x" % (role.color.r, role.color.g, role.color.b)
                    replacement = '<span style="color: %s;">@%s</span>' % (colour, role.name)
                self.content = self.content.replace(self.content[match.start():match.end()], replacement)
                match = re.search(regex, self.content)

    async def slash_command_mention(self):
        match = re.search(self.REGEX_SLASH_COMMAND, self.content)
        while match is not None:
            slash_command_name = match.group(1)
            replacement = (
                    '<span class="mention" title="%s">/%s</span>'
                    % (slash_command_name, slash_command_name)
            )
            self.content = self.content.replace(self.content[match.start():match.end()], replacement)

            match = re.search(self.REGEX_SLASH_COMMAND, self.content)

    async def member_mention(self):
        holder = self.REGEX_MEMBERS, self.REGEX_MEMBERS_2
        for regex in holder:
            match = re.search(regex, self.content)
            while match is not None:
                member_id = int(match.group(1))

                member = None
                try:
                    member = self.guild.get_member(member_id) or bot.get_user(member_id)
                    member_name = member.display_name
                except AttributeError:
                    member_name = member
                member_name = await self.escape_mention_starters(member_name)
                if member is not None:
                    replacement = '<span class="mention" title="%s">@%s</span>' \
                                  % (str(member_id), str(member_name))
                else:
                    replacement = '<span class="mention" title="%s">&lt;@%s></span>' \
                                  % (str(member_id), str(member_id))
                self.content = self.content.replace(self.content[match.start():match.end()],
                                                    replacement)

                match = re.search(regex, self.content)
                
        await self.unescape_mentions()

    async def time_mention(self):
        holder = self.REGEX_TIME_HOLDER

        for p in holder:
            regex, strf = p
            match = re.search(regex, self.content)
            while match is not None:
                timestamp = int(match.group(1)) - 1
                try:
                    time_stamp = time.gmtime(timestamp)
                    datetime_stamp = datetime.datetime(2010, *time_stamp[1:6], tzinfo=pytz.utc)
                    ui_time = datetime_stamp.strftime(strf)
                    ui_time = ui_time.replace(str(datetime_stamp.year), str(time_stamp[0]))
                    tooltip_time = datetime_stamp.strftime("%A, %e %B %Y at %H:%M")
                    tooltip_time = tooltip_time.replace(str(datetime_stamp.year), str(time_stamp[0]))
                except (OSError, OverflowError, ValueError):
                    # overflow error occurs when timestamp is too large, manual parsing
                    # Project the timestamp into a safe range that doesn't cause issues with system or python limitations
                    # Strip out 400-year chunks until the timestamp fits in Python's logic
                    safe_ts = timestamp % self.CYCLE_SECONDS
                    years_shifted = (timestamp // self.CYCLE_SECONDS) * 400
                    # Create the datetime object using the safe timestamp
                    dt = datetime.datetime.fromtimestamp(safe_ts, pytz.utc)
                    # Format normally, but inject the real year calculation
                    final_year = dt.year + years_shifted
                    ui_time = dt.strftime(strf)
                    ui_time = ui_time.replace(str(dt.year), str(final_year))
                    tooltip_time = dt.strftime("%A, %e %B %Y at %H:%M")
                    tooltip_time = tooltip_time.replace(str(dt.year), str(final_year))
                original = match.group().replace("&lt;", "<").replace("&gt;", ">")
                replacement = (
                    f'<span class="unix-timestamp" data-timestamp="{tooltip_time}" raw-content="{original}">'
                    f'{ui_time}</span>'
                )

                self.content = self.content.replace(self.content[match.start():match.end()],
                                                    replacement)

                match = re.search(regex, self.content)
