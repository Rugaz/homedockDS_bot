# cogs/basic_commands.py
import discord
from discord.ext import commands

# Cada cog debe ser una clase que herede de commands.Cog
class BasicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot # Necesitas una referencia al objeto bot

    # Un evento on_ready específico para este cog
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Cog "{self.qualified_name}" cargado y listo.')

    # Comando: !ping
    # Los comandos dentro de un cog deben ser métodos de la clase y usar @commands.command()
    @commands.command(name='ping')
    async def ping(self, ctx):
        """Responde con 'Pong!' y la latencia del bot."""
        await ctx.send(f'Pong! Latencia: {round(self.bot.latency * 1000)}ms')

    # Comando: !saludar [miembro]
    @commands.command(name='saludar')
    async def saludar(self, ctx, miembro: discord.Member = None):
        """Saluda a un miembro específico o al autor del comando."""
        if miembro:
            await ctx.send(f'¡Saludos, {miembro.display_name}! ¡Bienvenido a Homedock!')
        else:
            await ctx.send(f'¡Hola, {ctx.author.display_name}! Estoy aquí para ayudarte.')

    # Si tienes eventos generales que no son comandos específicos de un cog,
    # pueden ir aquí usando @commands.Cog.listener()
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if message.content.lower() == 'hola':
            await message.channel.send('¡Hola! Soy el bot de Homedock desde el cog de comandos básicos.')
        
        # OJO: No llames a process_commands aquí en un listener on_message dentro de un cog
        # El bot principal ya lo hace. Si lo haces, los comandos se ejecutarán dos veces.
        # Solo necesitas process_commands en el on_message general del bot principal si lo tienes.


# Esta es la función de setup que discord.py busca para cargar el cog
async def setup(bot):
    await bot.add_cog(BasicCommands(bot))