# homedock_bot.py
print("DEBUG: homedock_bot.py cargado desde:", __file__)
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio

# Cargar las variables de entorno
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Definir los intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

# Crear una instancia del bot
bot = commands.Bot(command_prefix='!', intents=intents)

# --- Eventos del Bot Principal ---
# ¡ELIMINA O COMENTA COMPLETAMENTE EL on_ready DE AQUÍ!
# Este on_ready es el que está 'pisando' el del cog.
# @bot.event
# async def on_ready():
#    print(f'¡Bot conectado como {bot.user}!')
#    print(f'ID del bot: {bot.user.id}')
#    await bot.change_presence(activity=discord.Game(name="con los comandos de Homedock"))
#    print("Cargando cogs...")
#    await load_cogs()
#    print("Cogs cargados.")


async def load_cogs():
    """Carga todos los cogs del directorio 'cogs'."""
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            cog_name = filename[:-3]
            try:
                await bot.load_extension(f'cogs.{cog_name}')
                print(f'Cog "{cog_name}" cargado exitosamente.')
            except Exception as e:
                print(f'ERROR al cargar el cog "{cog_name}": {e}')
                import traceback
                traceback.print_exc()

# --- Ejecutar el Bot ---

if TOKEN:
    # Llama a load_cogs ANTES de bot.run().
    # Los cogs deben cargarse antes de que el bot se conecte para que sus listeners on_ready se registren.
    async def main():
        await load_cogs()
        await bot.start(TOKEN) # Usamos bot.start() en lugar de bot.run() para poder await load_cogs()

    # Ejecuta la función main
    asyncio.run(main())
else:
    print("Error: El token del bot no está configurado. Asegúrate de que la variable de entorno DISCORD_BOT_TOKEN esté establecida en tu archivo .env")