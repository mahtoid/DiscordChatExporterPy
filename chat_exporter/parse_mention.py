import re
from typing import Optional

import discord


bot: Optional[discord.Client] = None


def pass_bot(_bot):
    global bot
    bot = _bot


class ParseMention:
    REGEX_ROLES = r"&lt;@&amp;([0-9]+)&gt;"
    REGEX_ROLES_2 = r"<@&([0-9]+)>"
    REGEX_MEMBERS = r"&lt;@!?([0-9]+)&gt;"
    REGEX_MEMBERS_2 = r"<@!?([0-9]+)>"
    REGEX_CHANNELS = r"&lt;#([0-9]+)&gt;"
    REGEX_CHANNELS_2 = r"<#([0-9]+)>"
    REGEX_EMOJIS = r"&lt;a?(:[^\n:]+:)[0-9]+&gt;"
    REGEX_EMOJIS_2 = r"<a?(:[^\n:]+:)[0-9]+>"

    ESCAPE_LT = "______lt______"
    ESCAPE_GT = "______gt______"
    ESCAPE_AMP = "______amp______"

    def __init__(self, content, guild):
        self.content = content
        self.guild = guild

    def flow(self):
        self.escape_mentions()
        self.escape_mentions()
        self.unescape_mentions()
        self.normal_channel_mention()
        self.html_channel_mention()
        self.normal_user_mention()
        self.html_user_mention()
        self.normal_role_mention()
        self.html_role_mention()

        return self.content

    def escape_mentions(self):
        for match in re.finditer("(%s|%s|%s|%s|%s|%s|%s|%s)"
                                 % (self.REGEX_ROLES, self.REGEX_MEMBERS, self.REGEX_CHANNELS, self.REGEX_EMOJIS,
                                    self.REGEX_ROLES_2, self.REGEX_MEMBERS_2, self.REGEX_CHANNELS_2,
                                    self.REGEX_EMOJIS_2), self.content):
            pre_content = self.content[:match.start()]
            post_content = self.content[match.end():]
            match_content = self.content[match.start():match.end()]

            match_content = match_content.replace("<", self.ESCAPE_LT)
            match_content = match_content.replace(">", self.ESCAPE_GT)
            match_content = match_content.replace("&", self.ESCAPE_AMP)

            self.content = pre_content + match_content + post_content

    def unescape_mentions(self):
        self.content = self.content.replace(self.ESCAPE_LT, "<")
        self.content = self.content.replace(self.ESCAPE_GT, ">")
        self.content = self.content.replace(self.ESCAPE_AMP, "&")
        pass

    def normal_channel_mention(self):
        offset = 0
        match = re.search(self.REGEX_CHANNELS, self.content)

        while match is not None:
            channel_id = int(match.group(1))
            channel = self.guild.get_channel(channel_id)

            if channel is None:
                replacement = '#deleted-channel'
            else:
                replacement = '<span class="mention" title="%s">#%s</span>' \
                              % (channel.name, channel.name)
            self.content = self.content.replace(self.content[match.start() + offset:match.end() + offset], replacement)

            offset += len(replacement) - (match.end() - match.start())
            match = re.search(self.REGEX_CHANNELS, self.content)

    def html_channel_mention(self):
        offset = 0
        match = re.search(self.REGEX_CHANNELS_2, self.content)

        while match is not None:
            channel_id = int(match.group(1))
            channel = self.guild.get_channel(channel_id)
            if channel is None:
                replacement = '#deleted-channel'
            else:
                replacement = '<span class="mention" title="%s">#%s</span>' \
                              % (channel.name, channel.name)
            self.content = self.content.replace(self.content[match.start() + offset:match.end() + offset],
                                                replacement)

            offset += len(replacement) - (match.end() - match.start())
            match = re.search(self.REGEX_CHANNELS_2, self.content)

    def normal_role_mention(self):
        offset = 0
        match = re.search(self.REGEX_ROLES, self.content)
        while match is not None:
            role_id = int(match.group(1))
            role = self.guild.get_role(role_id)

            if role is None:
                replacement = '@deleted-role'
            else:
                replacement = '<span style="color: #%02x%02x%02x;">@%s</span>' \
                              % (role.color.r, role.color.g, role.color.b, role.name)
            self.content = self.content.replace(self.content[match.start() + offset:match.end() + offset], replacement)

            offset += len(replacement) - (match.end() - match.start())
            match = re.search(self.REGEX_ROLES, self.content)

    def html_role_mention(self):
        offset = 0
        match = re.search(self.REGEX_ROLES_2, self.content)
        while match is not None:
            role_id = int(match.group(1))
            role = self.guild.get_role(role_id)

            if role is None:
                replacement = '@deleted-role'
            else:
                replacement = '<span style="color: #%02x%02x%02x;">@%s</span>' \
                              % (role.color.r, role.color.g, role.color.b, role.name)
            self.content = self.content.replace(self.content[match.start() + offset:match.end() + offset], replacement)

            offset += len(replacement) - (match.end() - match.start())
            match = re.search(self.REGEX_ROLES_2, self.content)

    def normal_user_mention(self):
        offset = 0
        match = re.search(self.REGEX_MEMBERS, self.content)
        while match is not None:
            member_id = int(match.group(1))

            member = None
            try:
                member = self.guild.get_member(member_id) or bot.get_user(member_id)
                member_name = member.display_name
            except AttributeError:
                member_name = member

            if member is not None:
                replacement = '<span class="mention" title="%s">@%s</span>' \
                              % (str(member_id), str(member_name))
            else:
                replacement = '<span class="mention" title="Unknown">@Unknown</span>'
            self.content = self.content.replace(self.content[match.start() + offset:match.end() + offset],
                                                replacement)

            offset += len(replacement) - (match.end() - match.start())
            match = re.search(self.REGEX_MEMBERS, self.content)

    def html_user_mention(self):
        offset = 0
        match = re.search(self.REGEX_MEMBERS_2, self.content)
        while match is not None:
            member_id = int(match.group(1))

            member = None
            try:
                member = self.guild.get_member(member_id) or bot.get_user(member_id)
                member_name = member.display_name
            except AttributeError:
                member_name = member

            if member is not None:
                replacement = '<span class="mention" title="%s">@%s</span>' \
                              % (str(member_id), str(member_name))
            else:
                replacement = '<span class="mention" title="Unknown">@Unknown</span>'
            self.content = self.content.replace(self.content[match.start() + offset:match.end() + offset],
                                                replacement)

            offset += len(replacement) - (match.end() - match.start())
            match = re.search(self.REGEX_MEMBERS_2, self.content)
