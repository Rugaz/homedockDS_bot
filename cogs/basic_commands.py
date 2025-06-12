# cogs/basic_commands.py
import discord
from discord.ext import commands
import datetime

class BasicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logging_cog = None # Para almacenar una referencia al LoggingCog

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Cog "{self.qualified_name}" de Comandos Básicos cargado y listo.')
        # Una vez que el bot está listo y todos los cogs cargados, obtenemos el logging_cog
        # Usamos self.bot.loop.create_task para no bloquear on_ready si LoggingCog tarda en inicializarse completamente.
        # aunque get_cog es sincrónico y rápido.
        self.logging_cog = self.bot.get_cog("LoggingCog")
        if self.logging_cog:
            print("Log: BasicCommands tiene acceso a LoggingCog.")
        else:
            print("Log: ADVERTENCIA: BasicCommands NO pudo obtener LoggingCog.")

    @commands.Cog.listener()
    async def on_command(self, ctx):
        """
        Este listener se dispara cada vez que un comando es invocado con éxito.
        Loguea la ejecución de cualquier comando en el canal de logs.
        """
        if self.logging_cog and self.logging_cog.log_channel:
            try:
                log_message = (
                    f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                    f"Comando `!{ctx.command.name}` ejecutado por **{ctx.author.display_name}** (ID: {ctx.author.id}) "
                    f"en `#{ctx.channel.name}` (ID: {ctx.channel.id})."
                )
                await self.logging_cog.log_channel.send(log_message)
            except discord.Forbidden:
                print(f"Log: ERROR: No tengo permisos para ESCRIBIR en el canal de logs ({self.logging_cog.log_channel.id}) desde on_command.")
            except Exception as e:
                print(f"Log: ERROR desconocido al loguear comando `!{ctx.command.name}` desde on_command: {e}")
        else:
            print(f"Log: No se pudo registrar el comando `!{ctx.command.name}`: Canal de logs no disponible o LoggingCog no accesible.")

    @commands.command(name='ping')
    async def ping(self, ctx):
        """Responde con Pong!"""
        await ctx.send('Pong!')

    @commands.command(name='saludar')
    async def greet(self, ctx):
        """Saluda al usuario."""
        await ctx.send(f'¡Hola, {ctx.author.display_name}!')

async def setup(bot):
    await bot.add_cog(BasicCommands(bot))