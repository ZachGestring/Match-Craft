from typing import Optional
import discord
from utils.db import db
import asyncpg
from discord import app_commands
from discord import ui
from discord.ext import commands

#test with dpytest

# need to multithread so polling for one queue does not block others
# check on player add if match capacity is passed then pop queue
class Queue(commands.Cog):
    #def __init__(self,location,queueConfig, matchConfig) -> None:
    def __init__(self,bot) -> None:
        self.bot=bot
        self.adminWhitelistRole=[]
        self.queueDict={}
        self.inMatch={}    #on match start, add all participating players here with their associated queue
    #####ADMIN_COMMANDS################################################################################
    @app_commands.command()
    async def addadminrole(self, interaction: discord.Interaction, role: discord.Role):
        #channel=ctx.message.channel
        outMessage="added admin perms to the following roles:"
        await db.connect()
        #for r in ctx.message.role_mentions:
        if role not in self.adminWhitelistRole:
            self.adminWhitelistRole.append(role)
            outMessage=outMessage+" " + role.name
            try:
                await db.execute("INSERT INTO administrative_roles (role_id) VALUES ($1);",role.id)
            except: 
                await interaction.response.send_message("error adding {id} to the database".format(id=role.id))
        await db.close()
        await interaction.response.send_message(outMessage)
            
    @app_commands.command()
    async def removeadminrole(self, interaction: discord.Interaction, role: discord.Role):
        channel=interaction.channel
        outMessage="removed admin perms from the following roles:"
        await db.connect()
        if role in self.adminWhitelistRole:
            self.adminWhitelistRole.remove(role)
            outMessage=outMessage+" " + role.name
            try:
                await db.execute("DELETE FROM administrative_roles WHERE role_id = $1;",role.id)
            except: 
                await interaction.response.send_message("error removing {id} from the database".format(id=role.id))
        await db.close()
        await interaction.response.send_message(outMessage)

    @app_commands.command()
    async def getadminlist(interaction: discord.Interaction,self):
        outMessageServer="The following roles have admin perms on the server:"
        for r in self.adminWhitelistRole:
                outMessageServer=outMessageServer+" "+ r.name
        await interaction.response.send_message(outMessageServer)
        
        outMessageDatabase="The following roles have admin perms in the database:"
        await db.connect()
        try:
            result = await db.execute("SELECT role_id FROM administrative_roles;")
            for x in result: 
                for a in interaction.guild.roles:
                    if x['role_id']==a.id:
                        outMessageDatabase=outMessageDatabase+" "+str(a.name)
            await interaction.response.send_message(outMessageDatabase)
        except:
            await interaction.response.send_message("Failed to access database")
        await db.close()

    @app_commands.command()
    @app_commands.describe(game='The game the queue is for', maxplayers='The number of players needed for a match')
    async def startqueue(self, interaction: discord.Interaction, game: str, maxplayers: int):
        channel=interaction.channel
        await db.connect()
        try:
            await db.execute("INSERT INTO active_queues VALUES ($1, $2, $3);", channel.id, str(game), int(maxplayers))
            await interaction.response.send_message("{name} is now a {game} pug channel [max {maxp} players]".format(name=channel.name, game=game, maxp=maxplayers))
        except: 
            await interaction.response.send_message("error adding new queue [{id}] to active_queues".format(id=channel.id))
        await db.close()
    
    @app_commands.command()
    async def stopqueue(self, interaction: discord.Interaction):
        channel=interaction.channel
        await db.connect()
        try:
            await db.execute("DELETE FROM active_queues WHERE queue_id=$1;",channel.id)
            await interaction.response.send_message("{name} is no longer a pug channel".format(name=channel.name))
        except: 
            await interaction.response.send_message("error removing queue [{id}] from active_queues".format(id=channel.id))
        await db.close()

    @app_commands.command()
    async def checkqueue(self, interaction: discord.Interaction):
        await db.connect()
        try:
            vals="active queues in DB:\n"
            queuedb=await db.execute("SELECT * FROM active_queues;")
            for x in queuedb:
                vals=vals+"  - queue_id: " + str(x['queue_id'])+", game: " + str(x['game'])+", max_players: " + str(x['max_players'])+"\n"
            await interaction.response.send_message(vals)
        except: 
            #await channel.send("there is no active queue in this channel")
            await interaction.response.send_message("failed to access active_queues relation")
        await db.close()
    #########QUEUE_COMMANDS###################    
    @app_commands.command()
    async def prepqueuedict(self, interaction: discord.Interaction):
        await db.connect()
        activeQueues= await db.execute("SELECT * FROM active_queues;")
        await db.close()
        for active in activeQueues:
            self.queueDict.update({
                active['queue_id']:{
                    "game" : active['game'],
                    "max_players" : active['max_players'],
                    "player_queue" : []
                    }
                })
        await interaction.response.send_message("dictionary setup complete")

    @app_commands.command()
    async def printqueuedict(self, interaction: discord.Interaction):
        channel=interaction.channel

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

        #self.matches.append(Match(matchParticipants,self.queueConfig,self.matchConfig))
        #update queue database
    
    @app_commands.command()
    async def add(self, interaction: discord.Interaction):
        channel=interaction.channel
        name=interaction.user.name
        if channel.id in self.queueDict.keys():
            self.queueDict[channel.id]["player_queue"].append(name)
            if len(self.queueDict[channel.id]["player_queue"])<self.queueDict[channel.id]["max_players"]:
                await interaction.response.send_message(name + " joined the queue\n" + self.__queueMessage(channel))
            else:
                self.__startMatch()
        else:
            await interaction.response.send_message("cannot add player to non-queue channel")
                
    @app_commands.command()
    async def remove(self, interaction: discord.Interaction):
        channel=interaction.channel
        name=interaction.user.name
        if channel.id in self.queueDict.keys():
            if(name in self.queueDict[channel.id]["player_queue"]):
                self.queueDict[channel.id]["player_queue"].remove(name)
                #need to update database here
                await interaction.response.send_message(name + " left the queue\n" + self.__queueMessage(channel))
            else: 
                await interaction.response.send_message("you are not in this queue")
        else:
            await interaction.response.send_message("cannot remove player from non-queue channel")

    @app_commands.command()
    async def queuestatus(self, interaction: discord.Interaction):
        channel=interaction.channel
        if channel.id in self.queueDict.keys():
            message=self.__queueMessage(channel)
            #await interaction.response.send_message(self.__queueMessage(channel))
            #await interaction.response.send_modal(discord.ui.Modal(title="[Queue Name]").add_item(discord.ui.text_display(self.__queueMessage(channel))))
            #await interaction.response.send_message(,view=embedLikeView(message="wack"))
        else:
            message="cannot check queue in non-queue channel"
            #await interaction.response.send_message("cannot check queue in non-queue channel")
            #await interaction.response.send_modal(discord.ui.modal(title="[Queue Name]").add_item(discord.ui.text_display("cannot check queue in non-queue channel")))
            #await interaction.response.send_message(,view=embedLikeView(message="wack"))
        myView=ui.View()
        myView.add_item(ui.text_display(message))
        await interaction.response.send_message(view=myView)

async def setup(bot: commands.Bot)-> None:
    #await bot.add_cog(AdminManagement(bot))
    await bot.add_cog(Queue(bot))