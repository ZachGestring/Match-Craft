import discord
from utils.db import db
import asyncpg
from discord import app_commands
from discord.ext import commands

#test with dpytest

class AdminManagement(commands.Cog):
    def __init__(self,bot)-> None:
        self.bot=bot
        self.adminWhitelistRole=[]


    @discord.app_commands.command()
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
                await interaction.channel.send("error adding {id} to the database".format(id=role.id))
        await db.close()
        await interaction.channel.send(outMessage)
            
    @discord.app_commands.command()
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
                await channel.send("error removing {id} from the database".format(id=role.id))
        await db.close()
        await channel.send(outMessage)

    @discord.app_commands.command()
    async def getadminlist(interaction: discord.Interaction,self):
        channel=interaction.message.channel
        outMessageServer="The following roles have admin perms on the server:"
        for r in self.adminWhitelistRole:
                outMessageServer=outMessageServer+" "+ r.name
        await channel.send(outMessageServer)
        
        outMessageDatabase="The following roles have admin perms in the database:"
        await db.connect()
        try:
            result = await db.execute("SELECT role_id FROM administrative_roles;")
            for x in result: 
                for a in interaction.guild.roles:
                    if x['role_id']==a.id:
                        outMessageDatabase=outMessageDatabase+" "+str(a.name)
            await channel.send(outMessageDatabase)
        except:
            await channel.send("Failed to access database")
        await db.close()

    @discord.app_commands.command()
    @app_commands.describe(game='The game the queue is for', maxplayers='The number of players needed for a match')
    async def startqueue(self,ctx,game: str, maxplayers: int):
        channel=ctx.message.channel
        await db.connect()
        try:
            await db.execute("INSERT INTO active_queues VALUES ($1, $2, $3);", channel.id, str(game), int(maxplayers))
            await channel.send("{name} is now a {game} pug channel [max {maxp} players]".format(name=channel.name, game=game, maxp=maxplayers))
        except: 
            await channel.send("error adding new queue [{id}] to active_queues".format(id=channel.id))
        await db.close()
    
    @discord.app_commands.command()
    async def stopqueue(self,ctx):
        channel=ctx.message.channel
        await db.connect()
        try:
            await db.execute("DELETE FROM active_queues WHERE queue_id=$1;",channel.id)
            await channel.send("{name} is no longer a pug channel".format(name=channel.name))
        except: 
            await channel.send("error removing queue [{id}] from active_queues".format(id=channel.id))
        await db.close()

    @discord.app_commands.command()
    async def checkqueue(self,ctx):
        channel=ctx.message.channel
        await db.connect()
        try:
            vals="active queues in DB:\n"
            queuedb=await db.execute("SELECT * FROM active_queues;")
            for x in queuedb:
                vals=vals+"  - queue_id: " + str(x['queue_id'])+", game: " + str(x['game'])+", max_players: " + str(x['max_players'])+"\n"
            await channel.send(vals)
        except: 
            #await channel.send("there is no active queue in this channel")
            await channel.send("failed to access active_queues relation")
        await db.close()

# need to multithread so polling for one queue does not block others
# check on player add if match capacity is passed then pop queue
class Queue(commands.Cog):
    #def __init__(self,location,queueConfig, matchConfig) -> None:
    def __init__(self,bot) -> None:
        self.bot=bot
        self.queueDict={}
        self.inMatch={}    #on match start, add all participating players here with their associated queue

    @discord.app_commands.command()
    async def prepqueuedict(self,ctx):
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
        await ctx.message.channel.send("dictionary setup complete")

    @discord.app_commands.command()
    async def printqueuedict(self,ctx):
        channel=ctx.message.channel

    def __queueMessage(self,channel):
        # Delete previous message? await delete_original_response()
        queueMessage="("
        for member in self.queueDict[channel.id]["player_queue"]:
            queueMessage=queueMessage+member+","
        queueMessage=queueMessage + ")[ "+str(len(self.queueDict[channel.id]["player_queue"]))+"/"+str(self.queueDict[channel.id]["max_players"])+"]"
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
    
    @discord.app_commands.command()
    async def add(self,ctx):
        channel=ctx.message.channel
        if channel.id in self.queueDict.keys():
            self.queueDict[channel.id]["player_queue"].append(ctx.message.author.name)
            if len(self.queueDict[channel.id]["player_queue"])<self.queueDict[channel.id]["max_players"]:
                await ctx.message.channel.send(ctx.message.author.name + " joined the queue\n" + self.__queueMessage(channel))
            else:
                self.__startMatch()
        else:
            await ctx.message.channel.send("cannot add player to non-queue channel")
                
    @discord.app_commands.command()
    async def remove(self,ctx):
        channel=ctx.message.channel
        if channel.id in self.queueDict.keys():
            if(ctx.message.author.name in self.queueDict[channel.id]["player_queue"]):
                self.queueDict[channel.id]["player_queue"].remove(ctx.message.author.name)
                #need to update database here
                await ctx.message.channel.send(ctx.message.author.name + " left the queue\n" + self.__queueMessage(channel))
            else: 
                await ctx.message.channel.send("you are not in this queue")
        else:
            await ctx.message.channel.send("cannot remove player from non-queue channel")

    @discord.app_commands.command()
    async def queuestatus(self,ctx):
        channel=ctx.message.channel
        if channel.id in self.queueDict.keys():
            await ctx.message.channel.send(self.__queueMessage(channel))
        else:
            await ctx.message.channel.send("cannot check queue in non-queue channel")

    