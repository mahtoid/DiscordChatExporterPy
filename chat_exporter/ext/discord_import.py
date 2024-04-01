discord_modules = ['nextcord', 'disnake', 'py-cord', 'discord']
for module in discord_modules:
    try:
        discord = __import__(module)
        discord.module = module
        break
    except ImportError:
        continue
