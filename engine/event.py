from engine.importlib import *
from engine.settings import *
from engine.tools import *


class EventData(dict):
	DEFAULT_VALUES = [
	    ('title',str),
	    ('maxPlayers',int),
	    ('dateStr',str),
	    ('messageID',int),
	    ('channelID',int),
		('guildID',int),
	    ('playersID',list),
	    ('waitingID',list)
	]

	def __init__(self,*args,**kwargs):
		dict.__init__(self,*args,**kwargs)
		for v in self.DEFAULT_VALUES:
			if not (v[0] in self):
				self.__setitem__(v[0],v[1]())




class Event:
	def __init__(self,manager,*args,**kwargs):
		self.manager = manager
		self.data = EventData(*args,**kwargs)
		self.configurable = [i for i in EventData.DEFAULT_VALUES[:3]]
		self.date = getTodayTime()

		self.loadData()
		self.updateDate(self.dateStr,verify=False)

		self.guild = self.manager.bot.get_guild(self.guildID)
		self.channel = self.manager.bot.get_channel(self.channelID)
		self.message = None
		self.alive = threading.Event()


	async def update(self):
		if self.channel and not self.message:
			self.message = await self.channel.fetch_message(self.messageID)
		if self.message:
			new_embed = self.generateEmbed()
			await self.message.edit(embed=new_embed)


	async def run(self):
		while not self.message:
			await asyncio.sleep(0.5)
			self.manager.updateEvent(self)
		self.alive.set()
		emojis = [str(r.emoji) for r in self.message.reactions]
		if not VALID_EMOJI in emojis:await self.message.add_reaction(VALID_EMOJI)
		if not FAIL_EMOJI in emojis: await self.message.add_reaction(FAIL_EMOJI)

	async def start(self):
		eventRole = discord.utils.get(self.guild.roles, id=EVENTPLAYERID)
		desc = """Hey tu t'étais inscit à l'event **{}**
		Et devine quoi... Il vient de commencer :tada:""".format(self.title)
		embed = discord.Embed(title="L'Event Commence !",
			description=desc,color=discord.Color.gold())
		for player in self.getPlayers(string=False):
			if player != None:
				await player.send(embed=embed)
				await player.add_roles(eventRole)
		try:
			new_embed = self.generateEmbed(dateOverride=" A déjà commencé !")
			await self.message.edit(embed=new_embed)
			await self.message.clear_reaction(VALID_EMOJI)
			await self.message.clear_reaction(FAIL_EMOJI)
		except:pass
		self.manager.removeEvent(self)
		print('Started Event: '+self.title)


	def generateEmbed(self,message=None,dateOverride=None):
		if not message and not(self.channel and self.message and self.guild):return
		if not message:message=self.message
		duration = self.date - getTodayTime()
		days = duration.days
		hours = divmod(duration.seconds,3600)[0]
		minutes = divmod(duration.seconds,60)[0] - hours*60
		if not dateOverride:
			timer = str(days)+' jours, '+str(hours)+' heures, '+str(minutes)+' minutes'
		else:timer = str(dateOverride)
		if message.embeds:content=message.embeds[0].description
		else:content=message.content
		embed= discord.Embed(title=' :tada: Event '+self.title+' !',
			description=content,color=discord.Color.gold())
		embed.add_field(name="Dans: ",
			value=timer, inline=True)
		embed.add_field(name="Prévu le:",
			value=self.date.strftime(DATE_FORMAT), inline=False)
		embed.add_field(name="Participants:", value=format_list(
			[str(self.guild.get_member(id)) for id in self.playersID],oneline=False), inline=False)
		embed.add_field(name="Liste d'Attente:", value=format_list(
			[str(self.guild.get_member(id)) for id in self.waitingID],oneline=False), inline=False)
		embed.add_field(name="Usage",
			value="Réagis avec {0} et {1} pour t'inscrire ou te désinscrire".format(VALID_EMOJI,FAIL_EMOJI), inline=False)
		return embed


	def updateDate(self,value,verify=True):
		value = getInputDate(value) if verify else value
		if not value:return
		date = string2Date(value)
		if date and (date > getTodayTime() or not verify):
			self.dateStr=value;self.date=date;return True

	def addPlayer(self,id,nomax=False):
		if id not in self.playersID:
			if nomax or not self.maxPlayers or len(self.playersID)<self.maxPlayers:
				if id in self.waitingID:self.waitingID.remove(id)
				self.playersID.append(id);return True
			else:self.waitingID.append(id);return True

	def delPlayer(self,id):
		if id in self.playersID:
			self.playersID.remove(id)
			if self.waitingID:self.addPlayer(self.waitingID[0])
			return True
		elif id in self.waitingID:
			self.waitingID.remove(id);return True

	def loadData(self):
		for var in self.data:
			self.__dict__[var]=self.data[var]

	def saveData(self):
		for var in self.data:
			self.data[var]=self.__dict__[var]

	def getPlayers(self,string=True):
		if string:
			return [str(self.guild.get_member(id)) for id in self.playersID]
		elif self.guild:return[self.guild.get_member(id) for id in self.playersID]

	def stop(self):
		self.alive.clear()
