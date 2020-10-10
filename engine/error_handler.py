from engine.importlib import *
from engine.tools import failed,confirm


class CommandErrorHandler(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):
		"""The event triggered when an error is raised while invoking a command.
		ctx   : Context
		error : Exception"""

		if hasattr(ctx.command, 'on_error'):
			return

		ignored = (commands.CommandNotFound)
		error = getattr(error, 'original', error)

		if isinstance(error, ignored):
			return

		elif isinstance(error,commands.UserInputError):
			return await failed(ctx)
		elif isinstance(error, commands.BadArgument):
			return await failed(ctx)
		elif isinstance(error,AttributeError):
			return await failed(ctx)

		elif isinstance(error, commands.DisabledCommand):
			return await ctx.channel.send(f'{ctx.command} has been disabled.')

		elif isinstance(error, commands.NoPrivateMessage):
			try:
				return await ctx.author.send(f'{ctx.command} can not be used in Private Messages.')
			except:pass

		print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
		traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
		return await failed(ctx)
