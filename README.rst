DiscordChatExporterPy
=====================

|version| |license| |language|

.. |license| image:: https://img.shields.io/pypi/l/chat-exporter

.. |version| image:: https://img.shields.io/pypi/v/chat-exporter

.. |language| image:: https://img.shields.io/github/languages/top/mahtoid/discordchatexporterpy

DiscordChatExporterPy is a Python plugin for your discord.py bot, allowing you to export a discord channels history within a guild.

Installing
----------
To install the library to your bot, run the command:

.. code:: sh

    pip install chat-exporter

To install the repository, run the command:

.. code:: sh

    git clone https://github.com/mahtoid/DiscordChatExporterPy

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
        chat_exporter.init_exporter(bot)
    
    
    @bot.command()
    async def save(ctx):
        await chat_exporter.quick_export(ctx)
    
    if __name__ == "__main__":
        bot.run("BOT_TOKEN_HERE")

*Optional: If you want the transcript to display Members (Role) Colours then enable the Members Intent.*

**Customisable Usage**

.. code:: py

    import io

    ...

    @bot.command()
    async def save(ctx, limit: int, tz_info):
        transcript = await chat_exporter.export(ctx.channel, limit, tz_info)

        if transcript is None:
            return

         transcript_file = discord.File(io.BytesIO(transcript.encode()),
                                        filename=f"transcript-{ctx.channel.name}.html")

        await ctx.send(file=transcript_file)

*Optional: limit and tz_info are both optional, but can be used to limit the amount of messages transcribed or set a 'local' (pytz) timezone for
the bot to transcribe message times to.*

**Raw Usage**

.. code:: py

    import io

    ...

    @bot.command()
    async def purge(ctx, tz_info):
        deleted_messages = await ctx.channel.purge()

        transcript = await chat_exporter.raw_export(ctx.channel, deleted_messages, tz_info)

        if transcript is None:
            return

         transcript_file = discord.File(io.BytesIO(transcript.encode()),
                                        filename=f"transcript-{ctx.channel.name}.html")

        await ctx.send(file=transcript_file)

*Optional: tz_info is optional, but can be used to set a 'local' (pytz) timezone for the bot to transcribe message times to.*

Screenshots
-----------

.. image:: https://raw.githubusercontent.com/mahtoid/DiscordChatExporterPy/master/.screenshots/channel_output.png

.. image:: https://raw.githubusercontent.com/mahtoid/DiscordChatExporterPy/master/.screenshots/html_output.png

Links
-----
- `Wiki <https://github.com/mahtoid/DiscordChatExporterPy/wiki/>`_
- `Discord Server <https://discord.gg/jeAdPaC>`_

Attributions
------------
*This project borrows CSS and HTML code from* `Tyrrrz's C# DiscordChatExporter <https://github.com/Tyrrrz/DiscordChatExporter/>`_ *repository.*
