import os
import sys
import discord
import pugQueue
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from utils.db import db


# Load environment variables from .env file
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
# Define the intents your bot needs
intents = discord.Intents.default()
intents.message_content = True

#MY_GUILD = discord.Object(id=0)

class MyClient(commands.Bot):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(command_prefix='!', intents=intents)
        #self.tree = app_commands.CommandTree(self)


    async def setup_hook(self):
        self.tree.clear_commands(guild=None)
        #self.tree.copy_global_to(guild=MY_GUILD)
        await self.add_cog(pugQueue.Queue(self))   
        await self.add_cog(pugQueue.AdminManagement(self))  
        #await self.tree.sync(guild=MY_GUILD)
        self.tree.sync

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})') # type: ignore
        print('------')


client = MyClient(intents=intents)

def main():
    client.run(TOKEN) # type: ignore

if __name__ == "__main__":
    main()