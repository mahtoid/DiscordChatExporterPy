import os
import asyncio
import discord
import chat_exporter
import sys

# Configuration from environment variables
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 715959114647208017
CHANNEL_ID = 1456616358681772135

if not TOKEN:
    print("Error: DISCORD_TOKEN environment variable is not set.")
    sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print(f"Error: Could not find guild with ID {GUILD_ID}")
        await bot.close()
        sys.exit(1)
        
    channel = guild.get_channel(CHANNEL_ID)
    if not channel:
        print(f"Error: Could not find channel with ID {CHANNEL_ID} in guild {GUILD_ID}")
        await bot.close()
        sys.exit(1)
        
    print(f"Exporting channel: {channel.name} ({channel.id})")
    
    try:
        transcript = await chat_exporter.export(
            channel,
            bot=bot,
        )
        
        if transcript:
            os.makedirs("tests/artifacts", exist_ok=True)
            with open("tests/artifacts/integration_transcript.html", "w", encoding="utf-8") as f:
                f.write(transcript)
            print("Successfully saved transcript to tests/artifacts/integration_transcript.html")
        else:
            print("Error: Export returned empty transcript.")
            await bot.close()
            sys.exit(1)
            
    except Exception as e:
        print(f"Error during export: {e}")
        await bot.close()
        sys.exit(1)
    
    print("Integration test completed successfully.")
    await bot.close()

if __name__ == "__main__":
    bot.run(TOKEN)
