import discord
from utils.db import db
import asyncpg
from discord import app_commands
from discord.ext import commands

class AdminManagement(commands.Cog):
    def __init__(self,bot)-> None:
        self.bot=bot
        self.adminWhitelistRole=[]

    @commands.command(name='addrole')
    async def addRole(self,ctx):
        if ctx.message.content.startswith('!addrole'):
            channel=ctx.message.channel
            outMessage="added admin perms to the following roles:"
            await db.connect()
            for r in ctx.message.role_mentions:
                if r not in self.adminWhitelistRole:
                    self.adminWhitelistRole.append(r)
                    outMessage=outMessage+" " + r.name
                    try:
                        await db.execute("INSERT INTO administrative_roles (role_id) VALUES ($1);",r.id)
                    except: 
                        await channel.send("error adding {id} to the database".format(id=r.id))
            await db.close()
            await channel.send(outMessage)
            
    @commands.command(name='removerole')
    async def removeWhitelistRole(self,ctx):
        if ctx.message.content.startswith('!removerole'):
            channel=ctx.message.channel
            outMessage="removed admin perms from the following roles:"
            await db.connect()
            for r in ctx.message.role_mentions:
                if r in self.adminWhitelistRole:
                    self.adminWhitelistRole.remove(r)
                    outMessage=outMessage+" " + r.name
                    try:
                        await db.execute("DELETE FROM administrative_roles WHERE role_id = $1;",r.id)
                    except: 
                        await channel.send("error removing {id} from the database".format(id=r.id))
            await db.close()
            await channel.send(outMessage)

    @commands.command(name='getadminlist')
    async def getadminlist(self,ctx):
        if ctx.message.content.startswith('!getadminlist'):
            channel=ctx.message.channel
            outMessageServer="The following roles have admin perms on the server:"
            for r in self.adminWhitelistRole:
                    outMessageServer=outMessageServer+" "+ r.name
            await channel.send(outMessageServer)
            
            outMessageDatabase="The following roles have admin perms in the database:"
            await db.connect()
            try:
                result = await db.execute("SELECT role_id FROM administrative_roles;")
                for x in result: 
                    for a in ctx.guild.roles:
                        if x['role_id']==a.id:
                            outMessageDatabase=outMessageDatabase+" "+str(a.name)
                await channel.send(outMessageDatabase)
            except:
                await channel.send("Failed to access database")
            await db.close()

    @commands.command(name='startqueue')
    async def startqueue(self,ctx,game,maxplayers):
        if ctx.message.content.startswith('!startqueue'):
            channel=ctx.message.channel
            await db.connect()
            try:
                await channel.send("attempting to access database")
                await channel.send("name: {name}, game: {game}, max players: {maxp}".format(name=channel.name, game=game, maxp=maxplayers))
                #await db.execute("INSERT INTO active_queues (queue_id) VALUES ($1);", (channel.id))
                await db.execute("INSERT INTO active_queues VALUES ($1, $2, $3);", (channel.id , str(game), int(maxplayers)))
                await channel.send("database access attempt successful")
                await channel.send("{name} is now a {game} pug channel, [max {maxp} players]".format(name=channel.name, game=game, maxp=maxplayers))
            except: 
                await channel.send("error adding new queue [{id}] to active_queues".format(id=channel.id))
            await db.close()
    
    @commands.command(name='stopqueue')
    async def stopqueue(self,ctx):
        if ctx.message.content.startswith('!stopqueue'):
            channel=ctx.message.channel
            await db.connect()
            try:
                await db.execute("DELETE FROM active_queues WHERE queue_id=$1;",channel.id)
                await channel.send("{name} is no longer a pug channel".format(name=channel.name))
            except: 
                await channel.send("error removing queue [{id}] from active_queues".format(id=channel.id))
            await db.close()

    @commands.command(name='checkqueue')
    async def checkqueue(self,ctx):
        if ctx.message.content.startswith('!checkqueue'):
            channel=ctx.message.channel
            await db.connect()
            try:
                vals="queuedb output:"
                await channel.send("attempting to access database")
                queuedb=await db.execute("SELECT * FROM active_queues;")
                await channel.send("database access attempt successful")
                for x in queuedb:
                    vals=vals+" "+str(x)
                await channel.send("string built successfully")
                await channel.send(vals)
                #queuedb=await db.execute("SELECT game, max_players FROM active_queues (queue_id, game, max_players) WHERE queue_id=$1;",channel.id)
                
                #await channel.send("{name} is a {game} pug channel [max {maxp} players]".format(name=channel.name,))
            except: 
                #await channel.send("there is no active queue in this channel")
                await channel.send("failed to access active_queues relation")
            await db.close()

# need to multithread so polling for one queue does not block others
# check on player add if match capacity is passed then pop queue
class Queue(commands.Cog):
    #def __init__(self,location,queueConfig, matchConfig) -> None:
    def __init__(self,bot) -> None:
        #self.ID=0 #hash from location+queueConfig+Matchconfig?
        #self.location=location
        #self.queueConfig=queueConfig
        #self.matchConfig=matchConfig
        #self.state=0
        self.queueSize=10
        self.bot=bot
        self.queueMembers=[]
        self.matches=[]
        #self.captainPriority=queueConfig.captainPriority
        #self.description=queueConfig.description

    def __queueMessage(self):
        # Delete previous message? await delete_original_response()
        queueMessage="("
        for member in self.queueMembers:
            queueMessage=queueMessage+member+","
        queueMessage=queueMessage + ")[ "+len(self.queueMembers)+"/"+self.queueSize+"]"
        return queueMessage
    
    def __startMatch(self):
        #announce match start
        matchParticipants=[]
        for x in range(0,self.queueSize):
          matchParticipants.append(self.queueMembers.pop(0))
        print("a match started with the following participants: " + matchParticipants)
        #self.matches.append(Match(matchParticipants,self.queueConfig,self.matchConfig))
        #update queue database
    
    @commands.command(name='add')
    async def add_to_queue(self,ctx):
        if ctx.message.content.startswith('!add'):
            self.queueMembers.append(ctx.message.author.name)
            #need to update database here
            if len(self.queueMembers)<self.queueSize:
                await ctx.message.channel.send(ctx.message.author.name + " joined the queue\n" + self.__queueMessage)
            else:
                self.__startMatch()
                
    
    @commands.command(name='remove')
    async def remove_from_queue(self,ctx):
        if ctx.message.content.startswith('!remove'):
            self.queueMembers.pop(ctx.message.author.name)
            #need to update database here
            await ctx.message.channel.send(ctx.message.author.name + " left the queue\n" + self.__queueMessage)

    