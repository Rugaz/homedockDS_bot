# homedock_bot.py
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import traceback # Importar traceback para mejor depuración

# Cargar las variables de entorno desde .env
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Definir los intents que tu bot necesita
# Estos intents deben estar activados también en el Portal de Desarrolladores de Discord
intents = discord.Intents.default()
intents.message_content = True # Necesario para leer el contenido de los comandos (ej. !ping)
intents.members = True         # Necesario para gestionar roles y obtener información de miembros (CRÍTICO para reaction_roles y tickets)
intents.presences = True       # Necesario si quieres ver el estado de presencia de los miembros
intents.guilds = True          # CRUCIAL para que el bot pueda acceder a información del servidor y gestionar canales, roles, etc.
intents.reactions = True       # Necesario para manejar interacciones con reacciones (ej. reaction_roles)


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
                traceback.print_exc() # Imprimir el stack trace completo para depuración
    print("Carga de cogs completada.")

@bot.event
async def on_ready():
    """Evento que se dispara cuando el bot está conectado y listo."""
    print(f'{bot.user} ha iniciado sesión y está online!')
    # Aquí puedes añadir código que quieras que se ejecute una vez que el bot esté listo,
    # por ejemplo, establecer un estado de actividad.
    await bot.change_presence(activity=discord.Game(name="Homedocks | !help"))


# --- Ejecutar el Bot ---
if TOKEN:
    async def main():
        # Cargar los cogs ANTES de que el bot se conecte.
        # Esto asegura que los listeners on_ready de los cogs estén registrados
        # y se disparen correctamente una vez que el bot esté listo.
        await load_cogs()
        print("Intentando iniciar el bot...")
        await bot.start(TOKEN)

    # Ejecuta la función main
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot apagado manualmente.")
    except Exception as e:
        print(f"Error fatal al iniciar el bot: {e}")
        traceback.print_exc()
else:
    print("Error: El token del bot no está configurado. Asegúrate de que la variable de entorno DISCORD_BOT_TOKEN esté establecida en tu archivo .env")