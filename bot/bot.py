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

class MyClient(commands.Bot):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(command_prefix="!", intents=intents)


    async def setup_hook(self):
        self.tree.clear_commands(guild=None)
        await db.connect()
        #await db.execute("CREATE TABLE IF NOT EXISTS administrative_roles (role_id BIGINT PRIMARY KEY);")
        await db.close()
        await self.add_cog(pugQueue.Queue(self))   
        await self.add_cog(pugQueue.AdminManagement(self))  
        self.tree.sync

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})') # type: ignore
        print('------')


client = MyClient(intents=intents)

def main():
    client.run(TOKEN) # type: ignore

if __name__ == "__main__":
    main()