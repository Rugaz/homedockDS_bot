import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Cargar las variables de entorno del archivo .env
load_dotenv()

# Obtener el token del bot de las variables de entorno
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Definir los intents que tu bot usará
# Deben coincidir con los que activaste en el Discord Developer Portal
intents = discord.Intents.default()
intents.message_content = True # ¡Muy importante si tu bot va a leer mensajes!
intents.members = True        # Permite que el bot vea la lista de miembros

# Crear una instancia del bot con un prefijo de comando y los intents
# El prefijo '!' significa que los comandos se activarán con, por ejemplo, !ping
bot = commands.Bot(command_prefix='!', intents=intents)

# --- Eventos del Bot ---

# Evento: Cuando el bot se conecta a Discord
@bot.event
async def on_ready():
    print(f'¡Bot conectado como {bot.user}!')
    print(f'ID del bot: {bot.user.id}')
    # Puedes establecer el estado de "jugando" del bot
    await bot.change_presence(activity=discord.Game(name="con los comandos de Homedock"))

# Evento: Cuando llega un mensaje (ejemplo básico, los comandos son más estructurados)
@bot.event
async def on_message(message):
    # Ignorar mensajes del propio bot para evitar bucles infinitos
    if message.author == bot.user:
        return

    # Si el mensaje es "hola", el bot responderá
    if message.content.lower() == 'hola':
        await message.channel.send('¡Hola! Soy el bot de Homedock. ¿En qué puedo ayudarte?')

    # Es crucial llamar a process_commands para que los comandos definidos con @bot.command funcionen
    await bot.process_commands(message)

# --- Comandos del Bot ---

# Comando: !ping
@bot.command(name='ping')
async def ping(ctx):
    """Responde con 'Pong!' y la latencia del bot."""
    await ctx.send(f'Pong! Latencia: {round(bot.latency * 1000)}ms')

# Comando: !saludar [miembro]
@bot.command(name='saludar')
async def saludar(ctx, miembro: discord.Member = None):
    """Saluda a un miembro específico o al autor del comando."""
    if miembro:
        await ctx.send(f'¡Saludos, {miembro.display_name}! ¡Bienvenido a Homedock!')
    else:
        await ctx.send(f'¡Hola, {ctx.author.display_name}! Estoy aquí para ayudarte.')

# Comando: !ayuda
@bot.command(name='ayuda')
async def help_command(ctx):
    """Muestra una lista de comandos disponibles."""
    help_text = "Comandos disponibles:\n"
    for command in bot.commands:
        help_text += f"  `!{command.name}`: {command.help or 'Sin descripción.'}\n"
    await ctx.send(help_text)

# --- Ejecutar el Bot ---

# Asegurarse de que el token esté disponible antes de iniciar el bot
if TOKEN:
    bot.run(TOKEN)
else:
    print("Error: El token del bot no está configurado. Asegúrate de que la variable de entorno DISCORD_BOT_TOKEN esté establecida en tu archivo .env")