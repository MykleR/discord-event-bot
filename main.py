from engine.__init__ import *


"""
# ~ =====================================================================
# ~ =========================     BOT TOOLS      ========================
# ~ =====================================================================
"""
def check_whitelist(member,rolesID):
	for r in rolesID:
		if discord.utils.get(member.roles, id=r) != None:
			return True
	return False
	
def check(user,wl=WHITELIST):
	return not user.bot and check_whitelist(user,wl)



"""
# ~ =====================================================================
# ~ ========================     BOT EVENTS      ========================
# ~ =====================================================================
"""
@bot.event
async def on_ready():
	print("Logged in as:",bot.user.name)
	print("ID:",bot.user.id)
	eventManager.loadEvents()
	eventManager.start()

@bot.event
async def on_raw_reaction_add(payload):
	if payload.member.bot:return
	if str(payload.emoji)!=VALID_EMOJI and str(payload.emoji)!=FAIL_EMOJI:return

	event=None
	for e in eventManager.events:
		if payload.message_id == e.messageID:
			if payload.channel_id == e.channelID:
				if payload.guild_id == e.guildID:event=e;break
	if not(event and event.alive.isSet()) :return

	if str(payload.emoji) == VALID_EMOJI:
		event.addPlayer(payload.member.id)
	elif str(payload.emoji) == FAIL_EMOJI:
		event.delPlayer(payload.member.id)
	await event.message.remove_reaction(payload.emoji, payload.member)
	eventManager.updateEvent(event)



"""
# ~ =====================================================================
# ~ =====================    BOT EVENT COMMANDS     =====================
# ~ =====================================================================
"""
class EventManagement(commands.Cog):
	def __init__(self,bot):
		super().__init__()
		self.bot = bot
	# ~
	# ~	=> All Commands for managing events:
	# ~ 	-newevent   : Pour créer un nouvel event.                        ✅
	# ~		-delevent   : Pour supprimer un event.							 ✅
	# ~		-edit       : Pour éditer un event.                              ✅
	# ~		-start      : Pour forcer le début d'un event.					 ✅
	# ~		-listevents : Pour obtenir la liste des participants à un event  ✅

	#---------------------------------------------------------------------------
	#---------------------------------------------------------------------------
	@commands.command(pass_context=True)
	async def newevent(self,ctx,#COMMAND ARGS:
			title:str,date:str,target_message_ID:int,max_players:int=0,
			announce_channel_ID:int=EVENTSCHANNELID,target_channel_ID:int=-1):
		''' : Pour créer un nouvel event.
		*(Format de la date:"jour-mois heures:minutes")*'''
		if not check(ctx.message.author):return
		final_date = getInputDate(date)
		channel = self.bot.get_channel(target_channel_ID)if target_channel_ID>0 else ctx.message.channel
		announceChannel = self.bot.get_channel(announce_channel_ID)
		try:message = await channel.fetch_message(target_message_ID)
		except:return await failed(ctx)
		if message and final_date and announceChannel and message.content:
			new_event=eventManager.createEvent({
				"title":title,
				"maxPlayers":max_players,
				"messageID":0,
				"channelID":announce_channel_ID,
				"guildID":ctx.guild.id,
				"dateStr":final_date})
			if new_event:
				embed = new_event.generateEmbed(message)
				msg = await announceChannel.send(embed=embed)
				new_event.messageID = msg.id
				eventManager.updateEvent(new_event)
				eventManager.saveEvent(new_event)
				return await confirm(ctx)
		await failed(ctx)


	#---------------------------------------------------------------------------
	#---------------------------------------------------------------------------
	@commands.command(pass_context=True)
	async def delevent(self,ctx,#COMMAND ARGS:
			event_title:str,clear_announce:bool=False):
		''' : Pour supprimer un event.'''
		if not check(ctx.message.author):return
		event = eventManager.titleExists(event_title)
		if not event:return await failed(ctx)
		if clear_announce:
			await self.bot.http.delete_message(event.channelID,event.messageID)
		eventManager.removeEvent(event)
		return await confirm(ctx)


	#---------------------------------------------------------------------------
	#---------------------------------------------------------------------------
	@commands.command(pass_context=True)
	async def edit(self,ctx,#COMMAND ARGS:
			event_title:str,key:str,value:str):
		''' : Pour éditer un event.'''
		if not check(ctx.message.author):return
		event = eventManager.titleExists(event_title)
		if not event or not value:return await failed(ctx)
		keys = [i[0] for i in event.configurable]
		if key=='date':
			if not event.updateDate(value):
				return await failed(ctx)
		elif key=='title':
			if not eventManager.changeEventTitle(event,value):
				return await failed(ctx)
		else:
			#try:
			event.__dict__[key]=event.configurable[keys.index(key)][1](value)
			#except:return await failed(ctx)
		eventManager.updateEvent(event)
		eventManager.saveEvent(event)
		await confirm(ctx)


	#---------------------------------------------------------------------------
	#---------------------------------------------------------------------------
	@commands.command(pass_context=True)
	async def start(self,ctx,#COMMAND ARGS:
			event_title:str):
		''' : Pour forcer le début d'un event.'''
		if not check(ctx.message.author):return
		event = eventManager.titleExists(event_title)
		if not event:return await failed(ctx)
		eventManager.startEvent(event)
		await confirm(ctx)


	#---------------------------------------------------------------------------
	#---------------------------------------------------------------------------
	@commands.command(pass_context=True)
	async def listevents(self,ctx):
		''' : Donne la liste des participants à un event'''
		if not check(ctx.message.author):return
		events = format_list(eventManager.listEvent())
		if events and len(events)>2:
			return await ctx.send("Voici la liste des events:\n"+events)
		await ctx.send("Il n'y a aucun event :confused:")



"""
# ~ =====================================================================
# ~ =====================   BOT PLAYERS COMMANDS    =====================
# ~ =====================================================================
"""
class PlayerManagement(commands.Cog):
	def __init__(self,bot):
		super().__init__()
		self.bot = bot
	# ~
	# ~	=> All Commands for managing players:
	# ~ 	-giveplayers : Donne EventPlayer aux participants d'un Event.    ✅
	# ~ 	-addplayers : Donne EventPlayer aux personnes mentionées.		 ✅
	# ~		-delplayers : Enlève EventPlayer aux personnes mentionées.       ✅
	# ~    	-register : Inscris à un event les personnes mentionées.         ✅
	# ~     -unregister : Désinscris à un event les personnes mentionées.    ✅
	# ~		-clearplayers : Enlève EventPlayer à tout le monde.              ✅
	# ~		-listplayers : Donne la liste des participants à un event.       ✅

	#---------------------------------------------------------------------------
	#---------------------------------------------------------------------------
	@commands.command(pass_context=True)
	async def giveplayers(self,ctx,#COMMAND ARGS:
			event_title : str):
		''' : Donne EventPlayer aux participants d'un Event.'''
		if not check(ctx.message.author):return
		event = eventManager.titleExists(event_title)
		if not event:return await failed(ctx)
		for id in event.playersID:
			user = ctx.guild.get_member(id)
			await self.addplayers(ctx,user)
		await confirm(ctx)


	#---------------------------------------------------------------------------
	#---------------------------------------------------------------------------
	@commands.command(pass_context=True)
	async def addplayers(self,ctx,#COMMAND ARGS:
			*users : discord.Member):
		''' : Donne EventPlayer aux personnes mentionées.'''
		if not check(ctx.message.author):return
		eventRole = discord.utils.get(ctx.guild.roles, id=EVENTPLAYERID)
		users = rmDoublon(users)
		for user in users:
			await user.add_roles(eventRole)
		await confirm(ctx)


	#---------------------------------------------------------------------------
	#---------------------------------------------------------------------------
	@commands.command(pass_context=True)
	async def delplayers(self,ctx,#COMMAND ARGS:
			*users : discord.Member):
		''' : Enlève EventPlayer aux personnes mentionées.'''
		if not check(ctx.message.author):return
		eventRole = discord.utils.get(ctx.guild.roles, id=EVENTPLAYERID)
		users = rmDoublon(users)
		for user in users:
			await user.remove_roles(eventRole)
		await confirm(ctx)


	#---------------------------------------------------------------------------
	#---------------------------------------------------------------------------
	@commands.command(pass_context=True)
	async def register(self,ctx,#COMMAND ARGS:
			*args):
		''' : Inscris à un event les personnes mentionées.'''
		if not check(ctx.message.author):return
		args,events,added,fail,users = rmDoublon(args),[],[],[],[]
		for arg in args:
			event = eventManager.titleExists(arg)
			if event:events.append(event);continue
			try:users.append(ctx.guild.get_member(int(arg[3:-1])))
			except:users.append(arg)
		for event in events:
			for user in users:
				if not isinstance(user,discord.Member):
					fail.append(str(user)+' à '+event.title+" raison: Mention introuvable")
					continue
				if event.addPlayer(user.id):added.append(str(user)+' à '+event.title)
				else:fail.append(str(user)+' à '+event.title+" raison: Participe déjà.")
			if(users and added):
				eventManager.updateEvent(event)
		if added:
			await ctx.send("Inscriptions de:\n"+format_list(added))
		elif not fail:await failed(ctx)
		if fail:await ctx.send("Impossible d'inscrire:\n"+format_list(fail))


	#---------------------------------------------------------------------------
	#---------------------------------------------------------------------------
	@commands.command(pass_context=True)
	async def unregister(self,ctx,#COMMAND ARGS:
			*args):
		''' : Désinscris à un event les personnes mentionées.'''
		if not check(ctx.message.author):return
		args,events,removed,fail,users = rmDoublon(args),[],[],[],[]
		for arg in args:
			event = eventManager.titleExists(arg)
			if event:events.append(event);continue
			try:users.append(ctx.guild.get_member(int(arg[3:-1])))
			except:users.append(arg)
		for event in events:
			for user in users:
				if not isinstance(user,discord.Member):
					fail.append(str(user)+' à '+event.title+" raison: Mention introuvable")
					continue
				if event.delPlayer(user.id):removed.append(str(user)+' à '+event.title)
				else:fail.append(str(user)+' à '+event.title+" raison: Ne participe déjà pas.")
			if(users and removed):
				eventManager.updateEvent(event)
		if removed:
			await ctx.send("Désinscriptions de:\n"+format_list(removed))
		elif not fail:await failed(ctx)
		if fail:await ctx.send("Impossible de désinscrire:\n"+format_list(fail))


	#---------------------------------------------------------------------------
	#---------------------------------------------------------------------------
	@commands.command(pass_context=True)
	async def clearplayers(self,ctx):
		''' : Enlève EventPlayer à tout le monde.'''
		if not check(ctx.message.author):return
		eventRole = discord.utils.get(ctx.guild.roles, id=EVENTPLAYERID)
		members = self.bot.get_all_members()
		for member in members:
			if check_whitelist(member,[EVENTPLAYERID]):
				await member.remove_roles(eventRole)
		await confirm(ctx)


	#---------------------------------------------------------------------------
	#---------------------------------------------------------------------------
	@commands.command(pass_context=True)
	async def listplayers(self,ctx,#COMMAND ARGS:
			event_title:str):
		''' : Donne la liste des participants à un event.'''
		if not check(ctx.message.author):return
		event = eventManager.titleExists(event_title)
		if not event:return await failed(ctx)
		players = format_list(event.getPlayers())
		if players and len(players)>2:
			return await ctx.send("Voici la liste des participants:\n"+players)
		await ctx.send("Il n'y a aucun participant :confused:")


"""
# ~ ==========================================================
# ~ =======================  BOT RUN   =======================
# ~ ==========================================================
"""

TOKEN = "YOUR APP TOKEN HERE"
PREFIX = "-"

bot = commands.Bot(command_prefix=PREFIX)
eventManager = EventManager(bot,asyncio.get_event_loop())


bot.help_command = PrettyHelp(color=discord.Color.gold())
bot.add_cog(EventManagement(bot))
bot.add_cog(PlayerManagement(bot))
bot.add_cog(CommandErrorHandler(bot))
bot.run(TOKEN)
