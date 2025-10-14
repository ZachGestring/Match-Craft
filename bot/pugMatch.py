import discord
from discord import app_commands
from discord.ext import commands

# matches should be multithreaded so waiting on input in one queue does not shut down another
class Match(commands.cog):
    #def __init__(self, participants, queueConfig, matchConfig) -> None:
    def __init__(self, participants,parentQueue) -> None:
        self.participants=participants
        self.parentQueue=parentQueue
        #self.queueConfig=queueConfig
        #self.matchConfig=matchConfig
        #self.checkInStatus=[]
        #self.checkInTime=queueConfig.checkInTime  
        #self.winnerVote=0
        #self.votedForWinner=[]

        #create and run match here, once the match finishes terminate

    def __checkInPhase(self):
        pass
    
    def __teamSelectionPhase(self):
        pass
    
    #this includes gameplay
    def __reportingPhase(self): 
        pass
    
    @commands.command(name='checkin')
    def playerCheckIn(self,playerDiscord):
        self.checkInStatus.append(playerDiscord)
    
    @commands.command(name='add')
    def playerReportWinner(self,playerDiscord,playerVote):
        if playerDiscord not in self.votedForWinner:
          self.votedForWinner.append(playerDiscord)
          self.winnerVote+=playerVote

    @commands.command(name='report')
    async def report_match_outcome(self,ctx):
        if ctx.message.content.startswith('/report'):
            self.participants.clear()
            self.matches.pop() #update to remove specific match id and get that id from the author
            await ctx.message.channel.send(ctx.message.author+"'s match has ended")
    
    