from typing import Optional
import discord
from discord.ui.item import Item
from utils.db import db
from discord import app_commands,ui
from discord.ext import commands

class Queue(commands.Cog):
    def __init__(self,bot) -> None:
        self.bot=bot
        self.adminWhitelistRole=[]
        self.queueDict={}
        self.inMatch={}

    #async database setup
    #populate admin whitelist and queue dictionary with values from the database
    async def cog_load(self):
        await db.connect()
        activeQueues= await db.execute("SELECT * FROM active_queues;")
        adminRoles = await db.execute("SELECT role_id FROM administrative_roles;")
        await db.close()
        for role in adminRoles:
            self.adminWhitelistRole.append(role['role_id']) 
        for active in activeQueues:
            self.queueDict.update({
                active['queue_id']:{
                    "game" : active['game'],
                    "max_players" : active['max_players'],
                    "player_queue" : [],
                    "queue_message_id": active['queue_message_id'],
                    "active_matches" : []
                    }
                })

    #Deletes the original queue message and reposts it any time a user posts in the queue channel so it is always visibile     
    @commands.Cog.listener(name='on_message')  
    async def repostQueueMessage(self,message):
        channel=message.channel
        if channel.id in self.queueDict.keys() and not (message.author == self.bot.user) :
            temp= await channel.fetch_message(self.queueDict[channel.id]["queue_message_id"])
            await temp.delete()
            #await channel.send(view=EmbedPugView(myQueueName=self.queueDict[channel.id]["game"],myText=self.queueMessage,myQueue=self)) #does not work because view is not serializable
            initMessage = await channel.send(view=EmbedView(myText="{game} PUGs\n\n{message}\n\n/add to join queue\n/remove to leave queue".format(game=self.queueDict[channel.id]["game"],message=self.queueMessage(channel))))
            self.queueDict[channel.id]["queue_message_id"]=initMessage.id

    #####ADMIN_COMMANDS################################################################################
    
    #check if the specified user is whitelisted or has discord admin perms
    def __verifyAdmin(self, user):
        for role in user.roles:
            if role in self.adminWhitelistRole or role.permissions.administrator:
                return True
        return False
    
    #Add the specified role to the pug admin whitelist
    @app_commands.command()
    async def addadminrole(self, interaction: discord.Interaction, role: discord.Role):
        if(self.__verifyAdmin(interaction.user)):
            outMessage=role.name + " already has pug admin perms"
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
        else:
            await interaction.response.send_message(view=EmbedView(myText="This command is reserved for administrators"))
            
    #Remove the specified role from the pug admin whitelist
    @app_commands.command()
    async def removeadminrole(self, interaction: discord.Interaction, role: discord.Role):
        if(self.__verifyAdmin(interaction.user)):
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
        else:
            await interaction.response.send_message(view=EmbedView(myText="This command is reserved for administrators"))

    #display a message containing all the whitelisted roles for pug administration
    @app_commands.command()
    async def getadminlist(self,interaction: discord.Interaction):
        outMessageServer="The following roles have admin perms on the server:"
        for r in self.adminWhitelistRole:
            for a in interaction.guild.roles:
                if r==a.id or a.permissions.administrator:
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
        
    #Starts a queue if one does not exist in the current channel
    @app_commands.command()
    @app_commands.describe(game='The game the queue is for', maxplayers='The number of players needed for a match')
    async def startqueue(self, interaction: discord.Interaction, game: str, maxplayers: int):
        if(self.__verifyAdmin(interaction.user)):
            channel=interaction.channel
            if channel.id not in self.queueDict.keys():
                #try:    
                    self.queueDict.update({
                        channel.id:{
                            "game" : game,
                            "max_players" : maxplayers,
                            "player_queue" : [],
                            "queue_message_id": None,
                            "active_matches" : []
                        }
                    })
                    initMessage = await interaction.response.send_message(view=EmbedView(myText="{game} PUGs\n\n{message}\n\n/add to join queue\n/remove to leave queue".format(game=game,message=self.queueMessage(channel))))
                    #initMessage = await interaction.response.send_message(view=EmbedPugView(myQueueName=game,myText=self.queueMessage,myQueue=self))
                    #await interaction.response.send_message(view=EmbedPugView(myQueueName=game,myText=self.queueMessage,myQueue=self))
                    self.queueDict[channel.id]["queue_message_id"]= initMessage.message_id
                    await db.connect()
                    await db.execute("INSERT INTO active_queues VALUES ($1, $2, $3, $4);", channel.id, str(game), int(maxplayers),initMessage.message_id)
                    await db.close()
                #except: 
                    #await interaction.response.send_message(view=EmbedView(myText="error adding new queue [{id}] to active_queues".format(id=channel.id)))
            else:
                await interaction.response.send_message(view=EmbedView(myText="A queue already exists in this channel"))
        else:
            await interaction.response.send_message(view=EmbedView(myText="This command is reserved for administrators"))

    #Stops the queue in the current channel if one exists
    @app_commands.command()
    async def stopqueue(self, interaction: discord.Interaction):
        if(self.__verifyAdmin(interaction.user)):
            channel=interaction.channel
        #try:
            mes = await channel.fetch_message(self.queueDict[channel.id]["queue_message_id"])
            await mes.edit(delete_after=0.0)
            del self.queueDict[channel.id]
            await db.connect()
            await db.execute("DELETE FROM active_queues WHERE queue_id=$1;",channel.id)
            await db.close()
            await interaction.response.send_message(view=EmbedView(myText="{name} is no longer a pug channel".format(name=channel.name)))
        #except: 
            #await interaction.response.send_message(view=EmbedView(myText="error removing queue [{id}] from active_queues".format(id=channel.id)))
        else:
            await interaction.response.send_message(view=EmbedView(myText="This command is reserved for administrators"))
        
    #displays a message containing all the active queues for debugging purposes
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
            await interaction.response.send_message(view=EmbedView(myText="failed to access active_queues relation"))

    #########QUEUE_COMMANDS###################    
    
    #returns a string that lists how many players players are in the requested queue
    def queueMessage(self,channel):
        queueMessage="("
        for x in range (0,len(self.queueDict[channel.id]["player_queue"])):
            queueMessage=queueMessage+self.queueDict[channel.id]["player_queue"][x]
            if(x<len(self.queueDict[channel.id]["player_queue"])-1):
                queueMessage=queueMessage+","
        queueMessage=queueMessage + ")["+str(len(self.queueDict[channel.id]["player_queue"]))+"/"+str(self.queueDict[channel.id]["max_players"])+"]"
        return queueMessage
    
    #initial outline for match flow
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
     
    #adds the player to the queue 
    @app_commands.command()
    async def add(self, interaction: discord.Interaction):
        channel=interaction.channel
        name=interaction.user.name
        output="cannot add player to non-queue channel"
        if channel.id in self.queueDict.keys():
            if name not in self.queueDict[channel.id]["player_queue"]:
                self.queueDict[channel.id]["player_queue"].append(name)
                if len(self.queueDict[channel.id]["player_queue"])<self.queueDict[channel.id]["max_players"]:
                    output=name + " joined the queue\n" + self.queueMessage(channel)
                else:
                    self.__startMatch()
            else:
                output="you are already in the queue\n" + self.queueMessage(channel)
        await interaction.response.send_message(view=EmbedPugView(myQueueName=self.queueDict[channel.id]["game"],myText=output,myQueue=self))

    #removes the player from the queue
    @app_commands.command()
    async def remove(self, interaction: discord.Interaction):
        channel=interaction.channel
        name=interaction.user.name
        output="cannot remove player from non-queue channel"
        if channel.id in self.queueDict.keys():
            if(name in self.queueDict[channel.id]["player_queue"]):
                self.queueDict[channel.id]["player_queue"].remove(name)
                output=name + " left the queue\n" + self.queueMessage(channel)
            else: 
                output="you are not in this queue"
        await interaction.response.send_message(view=EmbedPugView(myQueueName=self.queueDict[channel.id]["game"],myText=output,myQueue=self))

    #displays how many players are in the queue
    @app_commands.command()
    async def queuestatus(self, interaction: discord.Interaction):
        channel=interaction.channel
        output="cannot check queue in non-queue channel"
        if channel.id in self.queueDict.keys():
            output=self.queueMessage(channel)
        await interaction.response.send_message(view=EmbedView(myText=output))

#button template from discord.py api
class MyActionRow(ui.ActionRow):
    def __init__(self, queue: Queue) -> None:
        super().__init__()
        self.queue=queue
    
    #Adds player to the queue when the press the add button
    @ui.button(label='Add', style=discord.ButtonStyle.green)
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel=interaction.channel
        name=interaction.user.name
        output="cannot add player to non-queue channel"
        if channel.id in self.queue.queueDict.keys():
            self.queue.queueDict[channel.id]["player_queue"].append(name)
            if len(self.queue.queueDict[channel.id]["player_queue"])<self.queue.queueDict[channel.id]["max_players"]:
                output=name + " joined the queue\n" + self.queue.queueMessage(channel)
            else:
                self.queue.__startMatch()
        await interaction.response.send_message(view=EmbedPugView(myQueueName=self.queue.queueDict[channel.id]["game"],myText=output,myQueue=self.queue))

    #Removes the player from the queue when they press the remove button
    @ui.button(label='Remove',style=discord.ButtonStyle.red)
    async def remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel=interaction.channel
        name=interaction.user.name
        output="cannot remove player from non-queue channel"
        if channel.id in self.queue.queueDict.keys():
            if(name in self.queue.queueDict[channel.id]["player_queue"]):
                self.queue.queueDict[channel.id]["player_queue"].remove(name)
                output=name + " left the queue\n" + self.queue.queueMessage(channel)
            else: 
                output="you are not in this queue"
        await interaction.response.send_message(view=EmbedPugView(myQueueName=self.queue.queueDict[channel.id]["game"],myText=output,myQueue=self.queue))

#standard embed view for sending messages with the bot
class EmbedView(ui.LayoutView):
    def __init__(self, *, myText: str) -> None:
        super().__init__(timeout=None)
        self.text = ui.TextDisplay(myText)
        container = ui.Container(self.text, accent_color=discord.Color.red())
        self.add_item(container)

#embed view that makes use of buttons to add and remove the user from the queue
class EmbedPugView(ui.LayoutView):
    def __init__(self, *, myQueueName: str, myText: str, myQueue: Queue) -> None:
        super().__init__()
        self.myQueue=myQueue
        self.queueName = ui.TextDisplay(myQueueName)
        self.text = ui.TextDisplay(myText)
        self.sep=ui.Separator(visible=True)
        self.row=MyActionRow(myQueue)
        container = ui.Container(self.queueName, self.sep, self.text, self.sep, self.row, accent_color=discord.Color.red())
        self.add_item(container)

#applies the cog to the bot on startup
async def setup(bot: commands.Bot)-> None:
    await bot.add_cog(Queue(bot))