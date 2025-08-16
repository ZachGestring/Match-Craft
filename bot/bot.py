import os
import sys
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from cogs.owner_controls import OwnerControls
from utils.database import db_manager

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')

# Define the intents your bot needs
intents = discord.Intents.default()
intents.message_content = True

class MyClient(commands.Bot):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Initialize the database
        await db_manager.initialize()
        
        # Clear all existing commands to start fresh
        self.tree.clear_commands(guild=None)
        
        # Add the cog (which will register all its commands)
        await self.add_cog(OwnerControls(self))
        
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})') # type: ignore
        print('------')

    async def close(self):
        # Clean up database connections
        await db_manager.close()
        await super().close()

client = MyClient(intents=intents)

def main():
    client.run(TOKEN) # type: ignore

if __name__ == "__main__":
    main()
