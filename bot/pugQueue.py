from typing import Optional
import discord
from utils.db import db
from discord import app_commands,ui
from discord.ext import commands

#test with dpytest
class EmbedView(ui.LayoutView):
    def __init__(self, *, myText: str) -> None:
        super().__init__()
        self.text = ui.TextDisplay(myText)
        container = ui.Container(self.text, accent_color=discord.Color.red())
        self.add_item(container)

# need to multithread so polling for one queue does not block others
# check on player add if match capacity is passed then pop queue
class Queue(commands.Cog):
    #def __init__(self,location,queueConfig, matchConfig) -> None:
    def __init__(self,bot) -> None:
        self.bot=bot
        self.adminWhitelistRole=[]
        self.queueDict={}
        self.inMatch={}    #on match start, add all participating players here with their associated queue

    #async database setup
    async def cog_load(self):
        await db.connect()
        activeQueues= await db.execute("SELECT * FROM active_queues;")
        adminRoles = await db.execute("SELECT role_id FROM administrative_roles;")
        await db.close()
        for x in adminRoles:
            self.adminWhitelistRole.append(x['role_id'])
        for active in activeQueues:
            self.queueDict.update({
                active['queue_id']:{
                    "game" : active['game'],
                    "max_players" : active['max_players'],
                    "player_queue" : [],
                    "queue_status_message": [],
                    "active_matches" : []
                    }
                })
    #####ADMIN_COMMANDS################################################################################
    @app_commands.command()
    async def addadminrole(self, interaction: discord.Interaction, role: discord.Role):
        #channel=ctx.message.channel
        outMessage=role.name + " already has pug admin perms"
        #for r in ctx.message.role_mentions:
        if role not in self.adminWhitelistRole:
            self.adminWhitelistRole.append(role)
            outMessage=role.name + " now has pug admin perms"
            try:
                await db.connect()
                await db.execute("INSERT INTO administrative_roles (role_id) VALUES ($1);",role.id)
                await db.close()
            except: 
                await interaction.response.send_message(view=EmbedView(myText="error adding {id} to the database".format(id=role.id)))
        await interaction.response.send_message(view=EmbedView(myText=outMessage))
            
    @app_commands.command()
    async def removeadminrole(self, interaction: discord.Interaction, role: discord.Role):
        outMessage=role.name + " does not have pug admin perms"
        if role in self.adminWhitelistRole:
            self.adminWhitelistRole.remove(role)
            outMessage=role.name + " no longer has pug admin perms"
            try:
                await db.connect()
                await db.execute("DELETE FROM administrative_roles WHERE role_id = $1;",role.id)
                await db.close()
            except: 
                await interaction.response.send_message(view=EmbedView(myText="error removing {id} from the database".format(id=role.id)))
        await interaction.response.send_message(view=EmbedView(myText=outMessage))

    @app_commands.command()
    async def getadminlist(self,interaction: discord.Interaction):
        outMessageServer="The following roles have admin perms on the server:"
        for r in self.adminWhitelistRole:
            for a in interaction.guild.roles:
                if r==a.id:
                    outMessageServer=outMessageServer+" "+str(a.name) 
        outMessageServer=outMessageServer+"\n\n"
        #await interaction.response.send_message(view=EmbedView(myText=outMessageServer))
        
        outMessageDatabase=outMessageServer+"The following roles have admin perms in the database:"
        
        try:
            await db.connect()
            result = await db.execute("SELECT role_id FROM administrative_roles;")
            await db.close()
            for x in result: 
                for a in interaction.guild.roles:
                    if x['role_id']==a.id:
                        outMessageDatabase=outMessageDatabase+" "+str(a.name)
            await interaction.response.send_message(view=EmbedView(myText=outMessageDatabase))
        except:
            await interaction.response.send_message(view=EmbedView(myText="Failed to access database"))
        
    @app_commands.command()
    @app_commands.describe(game='The game the queue is for', maxplayers='The number of players needed for a match')

    async def startqueue(self, interaction: discord.Interaction, game: str, maxplayers: int):
        channel=interaction.channel
        try:
            await db.connect()
            await db.execute("INSERT INTO active_queues VALUES ($1, $2, $3);", channel.id, str(game), int(maxplayers))
            await interaction.response.send_message(view=EmbedView(myText="{name} is now a {game} pug channel [max {maxp} players]".format(name=channel.name, game=game, maxp=maxplayers)))
            await db.close()
        except: 
            await interaction.response.send_message(view=EmbedView(myText="error adding new queue [{id}] to active_queues".format(id=channel.id)))
        
    @app_commands.command()
    async def stopqueue(self, interaction: discord.Interaction):
        channel=interaction.channel
        try:
            await db.connect()
            await db.execute("DELETE FROM active_queues WHERE queue_id=$1;",channel.id)
            await db.close()
            await interaction.response.send_message(view=EmbedView(myText="{name} is no longer a pug channel".format(name=channel.name)))
        except: 
            await interaction.response.send_message(view=EmbedView(myText="error removing queue [{id}] from active_queues".format(id=channel.id)))
        
    @app_commands.command()
    async def checkqueue(self, interaction: discord.Interaction):
        try:
            vals="active queues in DB:\n"
            await db.connect()
            queuedb=await db.execute("SELECT * FROM active_queues;")
            await db.close()
            for x in queuedb:
                vals=vals+"  - queue_id: " + str(x['queue_id'])+", game: " + str(x['game'])+", max_players: " + str(x['max_players'])+"\n"
            await interaction.response.send_message(view=EmbedView(myText=vals))
        except: 
            #await channel.send("there is no active queue in this channel")
            await interaction.response.send_message(view=EmbedView(myText="failed to access active_queues relation"))
    #########QUEUE_COMMANDS###################    
    def __queueMessage(self,channel):
        # Delete previous message? await delete_original_response()
        queueMessage="("
        for x in range (0,len(self.queueDict[channel.id]["player_queue"])):
            queueMessage=queueMessage+self.queueDict[channel.id]["player_queue"][x]
            if(x<len(self.queueDict[channel.id]["player_queue"])-1):
                queueMessage=queueMessage+","
        queueMessage=queueMessage + ")["+str(len(self.queueDict[channel.id]["player_queue"]))+"/"+str(self.queueDict[channel.id]["max_players"])+"]"
        return queueMessage
    
    def __startMatch(self,channel):
        #announce match start
        matchParticipants=[]
        for x in range(0,self.queueDict[channel.id]["max_players"]):
          matchParticipants.append(self.queueDict[channel.id]["player_queue"].pop(0))
        for a in matchParticipants:
            self.inMatch.update({a : channel.id})
        print("a match started with the following participants: " + matchParticipants)
        #perform check-in
        #captain voting and team selection
        #outcome reporting
         
    @app_commands.command()
    async def add(self, interaction: discord.Interaction):
        channel=interaction.channel
        name=interaction.user.name
        output="cannot add player to non-queue channel"
        if channel.id in self.queueDict.keys():
            self.queueDict[channel.id]["player_queue"].append(name)
            if len(self.queueDict[channel.id]["player_queue"])<self.queueDict[channel.id]["max_players"]:
                output=name + " joined the queue\n" + self.__queueMessage(channel)
            else:
                self.__startMatch()
        await interaction.response.send_message(view=EmbedView(myText=output))
                
    @app_commands.command()
    async def remove(self, interaction: discord.Interaction):
        channel=interaction.channel
        name=interaction.user.name
        output="cannot remove player from non-queue channel"
        if channel.id in self.queueDict.keys():
            if(name in self.queueDict[channel.id]["player_queue"]):
                self.queueDict[channel.id]["player_queue"].remove(name)
                output=name + " left the queue\n" + self.__queueMessage(channel)
            else: 
                output="you are not in this queue"
        await interaction.response.send_message(view=EmbedView(myText=output))

    @app_commands.command()
    async def queuestatus(self, interaction: discord.Interaction):
        channel=interaction.channel
        output="cannot check queue in non-queue channel"
        if channel.id in self.queueDict.keys():
            output=self.__queueMessage(channel)
        await interaction.response.send_message(view=EmbedView(myText=output))

async def setup(bot: commands.Bot)-> None:
    await bot.add_cog(Queue(bot))