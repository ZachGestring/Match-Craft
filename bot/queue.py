import discord
from discord import app_commands
from discord.ext import commands

# This example requires the 'message_content' intent

intents = discord.Intents.default()
intents.messages=True
intents.presences=False 
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

client = discord.Client(intents=intents)
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    pugQueue=Queue.__init__
    #init queue

@bot.command(name='add')
async def add_to_queue(ctx):
    if ctx.message.content.startswith('/add'):
        Queue.addPlayer(ctx.message.author)
        await ctx.message.channel.send(ctx.message.author + " joined the queue\n" + Queue.queueMessage)

@bot.command(name='remove')
async def remove_from_queue(ctx):
    if ctx.message.content.startswith('/remove'):
        Queue.removePlayer(ctx.message.author)
        await ctx.message.channel.send(ctx.message.author + " left the queue\n" + Queue.queueMessage)

@bot.command(name='report')
async def report_match_outcome(ctx):
    if ctx.message.content.startswith('/report'):
        Queue.removePlayer(ctx.message.author)
        await ctx.message.channel.send(ctx.message.author+"'s match has ended")

client.run('your token here')

# need to multithread so polling for one queue does not block others
# check on player add if match capacity is passed then pop queue
class Queue():
    #def __init__(self,location,queueConfig, matchConfig) -> None:
    def __init__(self) -> None:
        #self.ID=0 #hash from location+queueConfig+Matchconfig?
        #self.location=location
        #self.queueConfig=queueConfig
        #self.matchConfig=matchConfig
        #self.state=0
        #self.queueSize=queueConfig.queueSize
        self.queueMembers=[]
        self.matches=[]
        #self.captainPriority=queueConfig.captainPriority
        #self.description=queueConfig.description

    def queueMessage(self):
        # Delete previous message? await delete_original_response()
        queueMessage="("
        for member in self.queueMembers:
            queueMessage=queueMessage+member+","
        queueMessage=queueMessage + ")[ "+len(self.queueMembers)+"/"+self.queueSize+"]"
        return queueMessage
    
    def adminOpenQueue(self):
        self.state=1
        self.runQueue()
        # need to send message containing queue state
    
    def adminCloseQueue(self):
        self.state=0
        self.queueMembers.clear()
        for m in self.matches:
            m.cancelMatch()
            #log match result as canceled
        # need to send message containing queue state
        # need to end all active matches
        # need to remove all players still in queue from database

    def adminDeleteQueue(self):
        pass
    
    def addPlayer(self,playerDiscord):
        self.queueMembers.append(playerDiscord)
        if len(self.queueMembers>=self.queueSize):
            self.startMatch()
        #need to update database here
    
    def removePlayer(self,playerDiscord):
        self.queueMembers.pop(playerDiscord)
        #need to update database here
  
    def startMatch(self):
        #announce match start
        matchParticipants=[]
        for x in range(0,self.queueSize):
          matchParticipants.append(self.queueMembers.pop(0))
        print("a match started with the following participants: "+matchParticipants)
        #self.matches.append(Match(matchParticipants,self.queueConfig,self.matchConfig))
        #update queue database

    def endMatch(self,Match):
        pass

# matches should be multithreaded so waiting on input in one queue does not shut down another
class Match():
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
    
    def playerCheckIn(self,playerDiscord):
        self.checkInStatus.append(playerDiscord)
    
    def playerReportWinner(self,playerDiscord,playerVote):
        if playerDiscord not in self.votedForWinner:
          self.votedForWinner.append(playerDiscord)
          self.winnerVote+=playerVote

    def report(self,team):
        #announce [team] has won
        #delete match

        for a in range (0,len(self.participants)):
            self.participants.pop(0)
    
    def cancelMatch(self):
        #set match result to canceled
        pass

    
    