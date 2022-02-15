DiscordChatExporterPy
=====================

|version| |license| |language|

.. |license| image:: https://img.shields.io/pypi/l/chat-exporter

.. |version| image:: https://img.shields.io/pypi/v/chat-exporter

.. |language| image:: https://img.shields.io/github/languages/top/mahtoid/discordchatexporterpy

DiscordChatExporterPy is a Python lib for your discord.py (or forks) bot, allowing you to export Discord channel history in to a HTML file.

Installing
----------
To install the library to your bot, run the command:

.. code:: sh

    pip install chat-exporter

To install the repository, run the command:

.. code:: sh

    git clone https://github.com/mahtoid/DiscordChatExporterPy

**NOTE: If you are using discord.py 1.7.3, please use chat-exporter v1.7.3**

Usage
-----
**Basic Usage**

.. code:: py
    
    import discord
    import chat_exporter
    from discord.ext import commands

    intents = discord.Intents.default()
    intents.members = True
    
    bot = commands.Bot(command_prefix="!", intents=intents)
    
    
    @bot.event
    async def on_ready():
        print("Live: " + bot.user.name)
    
    
    @bot.command()
    async def save(ctx: commands.Context):
        await chat_exporter.quick_export(ctx.channel)
    
    if __name__ == "__main__":
        bot.run("BOT_TOKEN_HERE")


**Customisable Usage**

.. code:: py

    import io

    ...

    @bot.command()
    async def save(ctx: commands.Context, limit: int, tz_info):
        transcript = await chat_exporter.export(
            ctx.channel,
            limit=limit,
            tz_info=tz_info,
        )

        if transcript is None:
            return

        transcript_file = discord.File(
            io.BytesIO(transcript.encode()),
            filename=f"transcript-{ctx.channel.name}.html",
        )

        await ctx.send(file=transcript_file)

| *Optional: limit and tz_info are both optional.*
|     *'limit' is to set the amount of messages to acquire from the history.*
|     *'tz_info' is to set your own custom timezone.*

**Raw Usage**

.. code:: py

    import io

    ...

    @bot.command()
    async def purge(ctx: commands.Context, tz_info):
        deleted_messages = await ctx.channel.purge()

        transcript = await chat_exporter.raw_export(
            ctx.channel,
            messages=deleted_messages,
            tz_info=tz_info,
        )

        if transcript is None:
            return

        transcript_file = discord.File(
            io.BytesIO(transcript.encode()),
            filename=f"transcript-{ctx.channel.name}.html",
        )

        await ctx.send(file=transcript_file)

| *Optional: tz_info is optional.*
|     *'tz_info' is to set your own custom timezone.*

Screenshots
-----------

.. image:: https://raw.githubusercontent.com/mahtoid/DiscordChatExporterPy/master/.screenshots/channel_output.png

.. image:: https://raw.githubusercontent.com/mahtoid/DiscordChatExporterPy/master/.screenshots/html_output.png

Links
-----
- `Wiki <https://github.com/mahtoid/DiscordChatExporterPy/wiki/>`_
- `Discord Server <https://discord.gg/mq3hYaJSfa>`_

Attributions
------------
*This project borrows CSS and HTML code from* `Tyrrrz's C# DiscordChatExporter <https://github.com/Tyrrrz/DiscordChatExporter/>`_ *repository.*