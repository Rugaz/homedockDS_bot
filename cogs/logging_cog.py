# cogs/logging_cog.py
import discord
from discord.ext import commands
import datetime

# --- CONFIGURACIÓN DE IDS ---
# ID del canal donde quieres que se envíen los logs del bot
LOG_CHANNEL_ID = 1382493194016522353 # <-- ¡PEGAR LA ID DEL CANAL DE LOGS AQUÍ!
# ID de TU SERVIDOR (Guild ID). Necesario para verificar que el bot está en el servidor correcto.
YOUR_SERVER_ID_HERE = 1381296490923954226 # <-- ¡PEGAR LA ID DE TU SERVIDOR AQUÍ!

class LoggingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel = None # Se inicializará con el objeto del canal de logs

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Este listener se ejecuta cuando el bot está completamente conectado a Discord.
        Es el punto central para la inicialización y verificación de logs.
        """
        print(f'Log: Cog "{self.qualified_name}" de Logging cargado y listo.')
        
        # Impresiones generales de inicio del bot en la consola
        print(f'¡Bot conectado como {self.bot.user}!')
        print(f'ID del bot: {self.bot.user.id}')
        await self.bot.change_presence(activity=discord.Game(name="con los comandos de Homedock"))
        print("Cogs cargados y bot listo para operar.")


        print("\n--- INICIO DE VERIFICACIÓN DE SERVIDOR Y CANAL DE LOGS ---")
        target_guild = self.bot.get_guild(YOUR_SERVER_ID_HERE)

        if not target_guild:
            print(f"Log: ERROR CRÍTICO: El bot NO está conectado al servidor con ID {YOUR_SERVER_ID_HERE}.")
            print("Log: Por favor, verifica la ID del servidor y que el bot esté invitado a él.")
            print("--- FIN DE VERIFICACIÓN ---")
            return # No podemos continuar sin el servidor

        print(f"Log: Bot conectado al servidor objetivo: '{target_guild.name}' (ID: {target_guild.id})")
        print(f"Log: Intentando obtener el canal de logs con ID: {LOG_CHANNEL_ID}")

        # Intentar obtener el canal de logs
        try:
            # Primero intentar desde la caché (más rápido)
            channel_from_cache = self.bot.get_channel(LOG_CHANNEL_ID)
            if channel_from_cache:
                self.log_channel = channel_from_cache
                print(f"Log: Canal de logs encontrado en caché: #{self.log_channel.name} (ID: {LOG_CHANNEL_ID})")
            else:
                # Si no está en caché, intentar con fetch_channel (pide a la API de Discord)
                print(f"Log: Canal NO encontrado en caché. Intentando con fetch_channel...")
                self.log_channel = await self.bot.fetch_channel(LOG_CHANNEL_ID)
                print(f"Log: Canal de logs obtenido con fetch_channel: #{self.log_channel.name} (ID: {LOG_CHANNEL_ID})")

            # Una vez que tenemos el objeto del canal, intentamos enviar un mensaje de prueba
            if self.log_channel:
                try:
                    await self.log_channel.send(f"Bot **{self.bot.user.display_name}** iniciado y sistema de logs activado. ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
                    print(f"Log: Mensaje de inicio enviado al canal de logs exitosamente.")
                except discord.Forbidden:
                    print(f"Log: ERROR CRÍTICO: No tengo permisos para ESCRIBIR en el canal de logs ({LOG_CHANNEL_ID}) aunque lo encontré.")
                    print("Log: Asegúrate de que el bot tenga el permiso 'Enviar Mensajes' (Send Messages) en el canal de logs.")
                    self.log_channel = None # Marca como no disponible si no puede escribir
                except Exception as e:
                    print(f"Log: ERROR desconocido al enviar mensaje de inicio al log: {e}")
                    self.log_channel = None

            else: # Esto ocurrirá si fetch_channel también falla (ej. canal no existe, ID incorrecta)
                print(f"Log: ADVERTENCIA CRÍTICA: El canal con ID {LOG_CHANNEL_ID} NO PUDO SER ENCONTRADO O ACCEDIDO.")
                print("Log: Posibles causas: ID incorrecta, canal eliminado, o permisos de 'Ver Canal' faltantes para el bot.")
                self.log_channel = None

        except discord.Forbidden:
            print(f"Log: ERROR CRÍTICO: El bot NO tiene permisos de 'Ver Canal' para el canal de logs ({LOG_CHANNEL_ID}).")
            print("Log: Asegúrate de que el bot tenga el permiso 'Ver Canal' en Discord para este canal específico.")
            self.log_channel = None
        except discord.NotFound:
            print(f"Log: ERROR CRÍTICO: El canal de logs con ID {LOG_CHANNEL_ID} NO FUE ENCONTRADO en Discord. La ID podría ser incorrecta o el canal fue eliminado.")
            self.log_channel = None
        except Exception as e:
            print(f"Log: ERROR CRÍTICO DESCONOCIDO al intentar obtener el canal de logs: {e}")
            self.log_channel = None
        
        print("--- FIN DE VERIFICACIÓN DE SERVIDOR Y CANAL DE LOGS ---\n")

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignorar mensajes del propio bot
        if message.author == self.bot.user:
            return
        # Ignorar mensajes en el propio canal de logs (para evitar bucles de logs)
        if message.channel.id == LOG_CHANNEL_ID:
            return
        
        # En esta versión, no logueamos todos los mensajes, solo los comandos y los eventos de reacción.
        pass

async def setup(bot):
    await bot.add_cog(LoggingCog(bot))