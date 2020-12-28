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
.. code:: py
    
    import discord
    import chat_exporter
    from discord.ext import commands
    
    bot = commands.Bot(command_prefix="!")
    
    
    @bot.event
    async def on_ready():
        print("Live: " + bot.user.name)
    
    
    @bot.command()
    async def save(ctx):
        await chat_exporter.export(ctx)
    
    if __name__ == "__main__":
        bot.run("BOT_TOKEN_HERE")

*Optional: If you want the transcript to display Members (Role) Colours then enable the Members Intent.*

Screenshots
-----------

.. image:: https://raw.githubusercontent.com/mahtoid/DiscordChatExporterPy/master/.screenshots/channel_output.png

.. image:: https://raw.githubusercontent.com/mahtoid/DiscordChatExporterPy/master/.screenshots/html_output.png

Links
-----
- `Wiki <https://github.com/mahtoid/DiscordChatExporterPy/wiki/>`_
- `Discord Server <https://discord.gg/jeAdPaC>`_


