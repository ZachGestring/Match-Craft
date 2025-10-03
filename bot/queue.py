import discord
from discord import app_commands
from discord.ext import commands

# need to multithread so polling for one queue does not block others
# check on player add if match capacity is passed then pop queue
class Queue():
    def __init__(self,location,queueConfig, matchConfig) -> None:
        self.ID=0 #hash from location+queueConfig+Matchconfig?
        self.location=location
        self.queueConfig=queueConfig
        self.matchConfig=matchConfig
        self.state=0
        self.queueSize=queueConfig.queueSize
        self.queueMembers=[]
        self.matches=[]
        self.captainPriority=queueConfig.captainPriority
        self.description=queueConfig.description
    
    def adminOpenQueue(self):
        self.state=1
        self.runQueue()
        # need to send message containing queue state
    
    def AdminCloseQueue(self):
        self.state=0
        self.queueMembers.clear()
        for m in self.matches:
            m.cancelMatch()
            #log match result as canceled
        # need to send message containing queue state
        # need to end all active matches
        # need to remove all players still in queue from database

    def deleteQueue(self):
        pass
    
    def addPlayer(self,playerDiscord):
        self.queueMembers.append(playerDiscord)
        #need to update database here
        if len(self.queueMembers>=self.queueSize):
            self.popQueue
        #need to update database here
    
    def removePlayer(self,playerDiscord):
        self.queueMembers.pop(playerDiscord)
        #need to update database here
  
    def startMatch(self):
        matchParticipants=[]
        for x in range(0,self.queueSize):
          matchParticipants.append(self.queueMembers.pop(0))
        #update queue database
        self.matches.append(Match(matchParticipants,self.queueConfig,self.matchConfig))

    

# matches should be multithreaded so waiting on input in one queue does not shut down another
class Match():
    def __init__(self, participants, queueConfig, matchConfig) -> None:
        self.participants=participants
        self.queueConfig=queueConfig
        self.matchConfig=matchConfig
        self.checkInStatus=[]
        self.checkInTime=queueConfig.checkInTime  
        self.winnerVote=0
        self.votedForWinner=[]

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
    
    def cancelMatch(self):
        #set match result to canceled
        pass

    
    