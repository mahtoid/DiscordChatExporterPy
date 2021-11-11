import io
from typing import List, Optional

import discord

from chat_exporter.construct.transcript import Transcript


async def quick_export(
    channel: discord.TextChannel,
    guild: Optional[discord.Guild],
):
    if guild:
        channel.guild = guild

    transcript = (
        await Transcript(
            channel=channel,
            limit=None,
            messages=None,
            pytz_timezone="UTC",
            ).export()
        ).html

    if not transcript:
        return

    transcript_embed = discord.Embed(
        description=f"**Transcript Name:** transcript-{channel.name}\n\n",
        colour=discord.Colour.blurple()
    )

    transcript_file = discord.File(io.BytesIO(transcript.html.encode()), filename=f"transcript-{channel.name}.html")
    await channel.send(embed=transcript_embed, file=transcript_file)


async def export(
    channel: discord.TextChannel,
    limit: Optional[int] = None,
    tz_info="UTC",
    guild: Optional[discord.Guild] = None,
):
    if guild:
        channel.guild = guild

    return (
        await Transcript(
            channel=channel,
            limit=limit,
            messages=None,
            pytz_timezone=tz_info,
        ).export()
    ).html


async def raw_export(
    channel: discord.TextChannel,
    messages: List[discord.Message],
    tz_info="UTC",
    guild: Optional[discord.Guild] = None,
):
    if guild:
        channel.guild = guild

    return (
        await Transcript(
            channel=channel,
            limit=None,
            messages=messages,
            pytz_timezone=tz_info,
        ).export()
    ).html
