# homedock_bot.py
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio

# Cargar las variables de entorno
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Definir los intents que tu bot necesita
intents = discord.Intents.default()
intents.message_content = True # Necesario para leer el contenido de los comandos (ej. !ping)
intents.members = True         # Necesario para gestionar roles y obtener información de miembros (CRÍTICO para reaction_roles)
intents.presences = True       # Necesario si quieres ver el estado de presencia de los miembros

# Crear una instancia del bot
bot = commands.Bot(command_prefix='!', intents=intents)

async def load_cogs():
    """Carga todos los cogs del directorio 'cogs'."""
    print("Iniciando carga de cogs...")
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            cog_name = filename[:-3]
            if cog_name == '__init__': # Ignorar el archivo __init__.py
                continue
            try:
                await bot.load_extension(f'cogs.{cog_name}')
                print(f'-> Cog "{cog_name}" cargado exitosamente.')
            except Exception as e:
                print(f'ERROR al cargar el cog "{cog_name}": {e}')
                import traceback
                traceback.print_exc()
    print("Carga de cogs completada.")

# --- Ejecutar el Bot ---
if TOKEN:
    async def main():
        # Cargar los cogs ANTES de que el bot se conecte.
        # Esto asegura que los listeners on_ready de los cogs estén registrados
        # y se disparen correctamente una vez que el bot esté listo.
        await load_cogs()
        await bot.start(TOKEN)

    # Ejecuta la función main
    asyncio.run(main())
else:
    print("Error: El token del bot no está configurado. Asegúrate de que la variable de entorno DISCORD_BOT_TOKEN esté establecida en tu archivo .env")