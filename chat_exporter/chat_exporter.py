import io
from typing import List, Optional

from chat_exporter.construct.transcript import Transcript
from chat_exporter.ext.discord_import import discord


async def quick_export(
    channel: discord.TextChannel,
    guild: Optional[discord.Guild] = None,
    bot: Optional[discord.Client] = None,
):
    if guild:
        channel.guild = guild

    transcript = (
        await Transcript(
            channel=channel,
            limit=None,
            messages=None,
            pytz_timezone="UTC",
            military_time=True,
            fancy_times=True,
            support_dev=True,
            bot=bot,
            ).export()
        ).html

    if not transcript:
        return

    transcript_embed = discord.Embed(
        description=f"**Transcript Name:** transcript-{channel.name}\n\n",
        colour=discord.Colour.blurple()
    )

    transcript_file = discord.File(io.BytesIO(transcript.encode()), filename=f"transcript-{channel.name}.html")
    return await channel.send(embed=transcript_embed, file=transcript_file)


async def export(
    channel: discord.TextChannel,
    limit: Optional[int] = None,
    tz_info="UTC",
    guild: Optional[discord.Guild] = None,
    bot: Optional[discord.Client] = None,
    military_time: Optional[bool] = True,
    fancy_times: Optional[bool] = True,
    support_dev: Optional[bool] = True,
):
    if guild:
        channel.guild = guild

    return (
        await Transcript(
            channel=channel,
            limit=limit,
            messages=None,
            pytz_timezone=tz_info,
            military_time=military_time,
            fancy_times=fancy_times,
            support_dev=support_dev,
            bot=bot,
        ).export()
    ).html


async def raw_export(
    channel: discord.TextChannel,
    messages: List[discord.Message],
    tz_info="UTC",
    guild: Optional[discord.Guild] = None,
    bot: Optional[discord.Client] = None,
    military_time: Optional[bool] = False,
    fancy_times: Optional[bool] = True,
    support_dev: Optional[bool] = True,
):
    if guild:
        channel.guild = guild

    return (
        await Transcript(
            channel=channel,
            limit=None,
            messages=messages,
            pytz_timezone=tz_info,
            military_time=military_time,
            fancy_times=fancy_times,
            support_dev=support_dev,
            bot=bot,
        ).export()
    ).html


async def quick_link(
    channel: discord.TextChannel,
    message: discord.Message
):
    embed = discord.Embed(
        title="Transcript Link",
        description=(
            f"[Click here to view the transcript](https://mahto.id/chat-exporter?url={message.attachments[0].url})"
        ),
        colour=discord.Colour.blurple(),
    )

    return await channel.send(embed=embed)


async def link(
    message: discord.Message
):
    return "https://mahto.id/chat-exporter?url=" + message.attachments[0].url
