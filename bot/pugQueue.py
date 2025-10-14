import discord
from discord import app_commands
from discord.ext import commands

#midsemester report on friday

# need to multithread so polling for one queue does not block others
# check on player add if match capacity is passed then pop queue
class Queue(commands.cog):
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
        if ctx.message.content.startswith('/add'):
            self.queueMembers.append(ctx.message.author)
            #need to update database here
            if len(self.queueMembers)<self.queueSize:
                await ctx.message.channel.send(ctx.message.author + " joined the queue\n" + self.__queueMessage)
            else:
                self.__startMatch()
                
    
    @commands.command(name='remove')
    async def remove_from_queue(self,ctx):
        if ctx.message.content.startswith('/remove'):
            self.queueMembers.pop(ctx.message.author)
            #need to update database here
            await ctx.message.channel.send(ctx.message.author + " left the queue\n" + self.__queueMessage)

    