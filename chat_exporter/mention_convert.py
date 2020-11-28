import re

REGEX_ROLES = r"&lt;@&amp;([0-9]+)&gt;"
REGEX_MEMBERS = r"&lt;@!?([0-9]+)&gt;"
REGEX_CHANNELS = r"&lt;#([0-9]+)&gt;"
REGEX_EMOJIS = r"&lt;a?(:[^\n:]+:)[0-9]+&gt;"
REGEX_ROLES_2 = r"<@&([0-9]+)>"
REGEX_MEMBERS_2 = r"<@!?([0-9]+)>"
REGEX_CHANNELS_2 = r"<#([0-9]+)>"
REGEX_EMOJIS_2 = r"<a?(:[^\n:]+:)[0-9]+>"

ESCAPE_LT = "______lt______"
ESCAPE_GT = "______gt______"
ESCAPE_AMP = "______amp______"


async def escape_mentions(content):
    for match in re.finditer("(%s|%s|%s|%s|%s|%s|%s|%s)"
                             % (REGEX_ROLES, REGEX_MEMBERS, REGEX_CHANNELS,
                                REGEX_EMOJIS, REGEX_EMOJIS_2, REGEX_ROLES_2, REGEX_CHANNELS_2, REGEX_MEMBERS_2),
                             content):

        pre_content = content[:match.start()]
        post_content = content[match.end():]
        match_content = content[match.start():match.end()]

        match_content = match_content.replace("<", ESCAPE_LT)
        match_content = match_content.replace(">", ESCAPE_GT)
        match_content = match_content.replace("&", ESCAPE_AMP)

        content = pre_content + match_content + post_content

    return content


async def unescape_mentions(content):
    content = content.replace(ESCAPE_LT, "<")
    content = content.replace(ESCAPE_GT, ">")
    content = content.replace(ESCAPE_AMP, "&")
    return content


async def parse_mentions(content, guild, bot):
    # parse mentions
    # channels
    offset = 0
    for match in re.finditer(REGEX_CHANNELS, content):
        channel_id = int(match.group(1))
        channel = guild.get_channel(channel_id)
        if channel is None:
            replacement = '#deleted-channel'
        else:
            replacement = '<span class="mention" title="%s">#%s</span>' \
                      % (channel.name, channel.name)
        content = content.replace(content[match.start() + offset:match.end() + offset],
                                  replacement)
        offset += len(replacement) - (match.end() - match.start())

    for match in re.finditer(REGEX_CHANNELS_2, content):
        channel_id = int(match.group(1))
        channel = guild.get_channel(channel_id)
        if channel is None:
            replacement = '#deleted-channel'
        else:
            replacement = '<span class="mention" title="%s">#%s</span>' \
                      % (channel.name, channel.name)
        content = content.replace(content[match.start() + offset:match.end() + offset],
                                  replacement)
        offset += len(replacement) - (match.end() - match.start())
    # roles
    offset = 0
    for match in re.finditer(REGEX_ROLES, content):
        role_id = int(match.group(1))
        role = guild.get_role(role_id)
        if role is None:
            replacement = '@deleted-role'
        else:
            replacement = '<span style="color: #%02x%02x%02x;">@%s</span>' \
                          % (role.color.r, role.color.g, role.color.b, role.name)
        content = content.replace(content[match.start() + offset:match.end() + offset], replacement)
        offset += len(replacement) - (match.end() - match.start())

    for match in re.finditer(REGEX_ROLES_2, content):
        role_id = int(match.group(1))
        role = guild.get_role(role_id)
        if role is None:
            replacement = '@deleted-role'
        else:
            replacement = '<span style="color: #%02x%02x%02x;">@%s</span>' \
                          % (role.color.r, role.color.g, role.color.b, role.name)
        content = content.replace(content[match.start() + offset:match.end() + offset], replacement)
        offset += len(replacement) - (match.end() - match.start())

    # members
    offset = 0

    for match in re.finditer(REGEX_MEMBERS, content):
        member_id = int(match.group(1))
        member = guild.get_member(member_id) or bot.get_user(member_id)

        try:
            member_name = member.display_name
        except AttributeError:
            member_name = member

        if member is not None:
            replacement = '<span class="mention" title="%s">@%s</span>' \
                          % (member, str(member_name))
            content = content.replace(content[match.start() + offset:match.end() + offset],
                                      replacement)
            offset += len(replacement) - (match.end() - match.start())

    for match in re.finditer(REGEX_MEMBERS_2, content):
        member_id = int(match.group(1))
        member = guild.get_member(member_id) or bot.get_user(member_id)

        try:
            member_name = member.display_name
        except AttributeError:
            member_name = member

        if member is not None:
            replacement = '<span class="mention" title="%s">@%s</span>' \
                          % (member, str(member_name))
            content = content.replace(content[match.start() + offset:match.end() + offset],
                                      replacement)
            offset += len(replacement) - (match.end() - match.start())

    # custom emoji
    offset = 0
    for match in re.finditer(REGEX_EMOJIS, content):
        name = match.group(1)
        replacement = name
        content = content.replace(content[match.start() + offset:match.end() + offset],
                                  replacement)
        offset += len(replacement) - (match.end() - match.start())

    for match in re.finditer(REGEX_EMOJIS_2, content):
        name = match.group(1)
        replacement = name
        content = content.replace(content[match.start() + offset:match.end() + offset],
                                  replacement)
        offset += len(replacement) - (match.end() - match.start())

    return content
