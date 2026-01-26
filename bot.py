import os

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Setup Intents
intents = discord.Intents.default()
intents.message_content = True
intents.emojis_and_stickers = True  # Enable the relevant intent
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)


# Connect to Discord
@bot.event
async def on_ready():
    # Syncing the slash commands
    await bot.tree.sync()
    print(f"Logged in as {bot.user} and synced commands!")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    print(f"Message from {message.author}: {message.content}")

    # Simple reply logic
    await message.channel.send(f"Hello, {message.author.mention}!")

    # IMPORTANT: Allow prefix commands to work alongside on_message
    await bot.process_commands(message)


@bot.tree.command(name="add_emoji", description="Add an Emoji to the server")
@app_commands.describe(url="The URL of the image")
@app_commands.describe(name="Name for the image")
async def add_emoji(interaction: discord.Interaction, url: str, name: str):
    await interaction.response.defer(thinking=True)

    if not interaction.user.guild_permissions.manage_emojis_and_stickers:
        await interaction.followup.send(
            "You do not have permission to manage emojis.", ephemeral=True
        )
        return

    if interaction.guild is None:
        await interaction.followup.send(
            "This command can only be used in a server.", ephemeral=True
        )
        return

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    await interaction.followup.send(
                        "Could not download image.", ephemeral=True
                    )
                    return
                image_bytes = await resp.read()
        if len(image_bytes) > 256000:
            await interaction.followup.send(
                "File size too large (max 256KB).", ephemeral=True
            )
            return

        new_emoji = await interaction.guild.create_custom_emoji(
            name=name,
            image=image_bytes,
            reason=f"Uploaded by {interaction.user.name} via bot command",
        )

        await interaction.followup.send(
            f"Successfully uploaded emoji: {new_emoji} (`:{new_emoji.name}:`)"
        )

    except discord.Forbidden:
        await interaction.followup.send(
            "I do not have the necessary permissions to create emojis.", ephemeral=True
        )
    except discord.HTTPException as e:
        await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)


bot.run(token=TOKEN)
