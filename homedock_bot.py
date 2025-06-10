# homedock_bot.py
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio # Necesario para cargar cogs de forma asíncrona

# Cargar las variables de entorno
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Definir los intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True # Si tu cog necesita información de presencia

# Crear una instancia del bot
bot = commands.Bot(command_prefix='!', intents=intents)

# --- Eventos del Bot Principal ---

@bot.event
async def on_ready():
    print(f'¡Bot conectado como {bot.user}!')
    print(f'ID del bot: {bot.user.id}')
    await bot.change_presence(activity=discord.Game(name="con los comandos de Homedock"))
    print("Cargando cogs...")
    # Llama a la función para cargar todos los cogs
    await load_cogs()
    print("Cogs cargados.")

# --- Funcionalidad de Carga de Cogs ---

async def load_cogs():
    # Itera sobre los archivos en la carpeta 'cogs'
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            # El nombre del cog es el nombre del archivo sin .py
            cog_name = filename[:-3]
            try:
                # Carga el cog. El formato es 'nombre_de_la_carpeta.nombre_del_archivo'
                await bot.load_extension(f'cogs.{cog_name}')
                print(f'Cog "{cog_name}" cargado exitosamente.')
            except Exception as e:
                print(f'ERROR al cargar el cog "{cog_name}": {e}')

# --- Ejecutar el Bot ---

if TOKEN:
    # Ejecuta el bot. La función load_cogs se llamará cuando el bot esté listo.
    bot.run(TOKEN)
else:
    print("Error: El token del bot no está configurado. Asegúrate de que la variable de entorno DISCORD_BOT_TOKEN esté establecida en tu archivo .env")