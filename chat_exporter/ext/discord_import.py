discord_modules = ['discord', 'nextcord', 'disnake']
for module in discord_modules:
    try:
        discord = __import__(module)
        break
    except ImportError:
        continue
