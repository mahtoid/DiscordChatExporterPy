DiscordChatExporterPy
=====================
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
        chat_exporter.init_exporter(bot)
    
    
    @bot.command()
    async def save(ctx):
        await chat_exporter.export(ctx)
    
    if __name__ == "__main__":
        bot.run("BOT_TOKEN_HERE")

Links
-----
- `Wiki <https://github.com/mahtoid/DiscordChatExporterPy/wiki/>`_
- `Discord Server <https://discord.gg/jeAdPaC>`_


