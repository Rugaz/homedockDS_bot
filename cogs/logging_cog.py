# cogs/logging_cog.py
print("DEBUG: logging_cog.py cargado desde:", __file__)
import discord
from discord.ext import commands
import datetime

# ID del canal donde quieres que se envíen los logs
LOG_CHANNEL_ID = 1382493194016522353
# ID de TU SERVIDOR. Asegúrate de que esta ID sea la de tu servidor de Discord.
YOUR_SERVER_ID_HERE = 1381296490923954226 # ¡CONFIRMA que esta es la ID CORRECTA de tu servidor!

class LoggingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel = None

    @commands.Cog.listener()
    async def on_ready(self):
        # Esta es la única función on_ready que se ejecutará en tu bot.
        print(f'Log: Cog "{self.qualified_name}" de Logging cargado y listo.')
        print(f"Log: Intentando encontrar el canal de logs con ID: {LOG_CHANNEL_ID}")
        
        # Mover las impresiones generales del bot aquí, si quieres que se vean.
        print(f'¡Bot conectado como {self.bot.user}!')
        print(f'ID del bot: {self.bot.user.id}')
        await self.bot.change_presence(activity=discord.Game(name="con los comandos de Homedock"))
        print("Cogs cargados y bot listo para operar.")


        print("\n--- INICIO DE LISTADO DE CANALES ACCESIBLES PARA EL BOT ---")
        found_target_guild = False
        target_guild = None

        for guild in self.bot.guilds:
            print(f"Log: Bot conectado al Gremio: '{guild.name}' (ID: {guild.id})")
            if guild.id == YOUR_SERVER_ID_HERE:
                target_guild = guild
                found_target_guild = True
                print(f"Log: ---> Este es el servidor objetivo: '{guild.name}' <---")

                print(f"Log: Canales visibles en '{guild.name}':")
                log_channel_found_in_list = False
                for channel in guild.channels:
                    channel_type = "Texto" if isinstance(channel, discord.TextChannel) else \
                                 "Voz" if isinstance(channel, discord.VoiceChannel) else \
                                 "Categoría" if isinstance(channel, discord.CategoryChannel) else \
                                 "Desconocido"
                    print(f"Log:   - #{channel.name} (ID: {channel.id}, Tipo: {channel_type})")
                    if channel.id == LOG_CHANNEL_ID:
                        log_channel_found_in_list = True
                        print(f"Log:   ---> ¡El canal de logs {LOG_CHANNEL_ID} FUE ENCONTRADO EN LA LISTA DEL SERVIDOR! <---")

                if not log_channel_found_in_list:
                    print(f"Log: ADVERTENCIA: El canal de logs {LOG_CHANNEL_ID} NO APARECE en la lista de canales visibles de '{guild.name}'.")
                    print("Log: Esto sugiere un problema de permisos de 'Ver Canal' MUY específico o anulación en una categoría.")
                
            else:
                print(f"Log: Nota: El bot está conectado a otro gremio: '{guild.name}' (ID: {guild.id}).")


        if not found_target_guild:
            print(f"Log: ERROR: El bot NO está conectado al servidor con ID {YOUR_SERVER_ID_HERE}.")
            print("Log: Por favor, verifica la ID del servidor y que el bot esté invitado a él.")

        print("--- FIN DE LISTADO DE CANALES ACCESIBLES PARA EL BOT ---\n")


        # --- INTENTO DE OBTENER EL CANAL DE LOGS ESPECÍFICO (Lógica principal) ---
        try:
            channel_from_cache = self.bot.get_channel(LOG_CHANNEL_ID)
            if channel_from_cache:
                self.log_channel = channel_from_cache
                print(f"Log: Canal de logs encontrado en caché: #{self.log_channel.name} (ID: {LOG_CHANNEL_ID})")
            else:
                print(f"Log: Canal NO encontrado en caché. Intentando con fetch_channel (directo de la API).")
                self.log_channel = await self.bot.fetch_channel(LOG_CHANNEL_ID)

            if self.log_channel:
                print(f"Log: ÉXITO! Canal de logs encontrado exitosamente: #{self.log_channel.name} (ID: {LOG_CHANNEL_ID})")
                try:
                    await self.log_channel.send(f"Bot **{self.bot.user.display_name}** iniciado y sistema de logs activado. ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
                    print(f"Log: Mensaje de inicio enviado al canal de logs.")
                except discord.Forbidden:
                    print(f"Log: ERROR CRÍTICO: No tengo permisos para ESCRIBIR en el canal de logs ({LOG_CHANNEL_ID}) aunque lo encontré.")
                    print("Log: Asegúrate de que el bot tenga el permiso 'Enviar Mensajes' (Send Messages) en el canal de logs.")
                    self.log_channel = None 
                except Exception as e:
                    print(f"Log: ERROR desconocido al enviar mensaje de inicio al log: {e}")
                    self.log_channel = None

            else:
                print(f"Log: ADVERTENCIA CRÍTICA: Ni get_channel ni fetch_channel pudieron encontrar el canal con ID: {LOG_CHANNEL_ID}")
                print("Log: Posibles causas: ID incorrecta, bot no en el servidor, o permisos de 'Ver Canal' faltantes, o canal inaccesible.")
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

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignorar mensajes del propio bot para evitar bucles infinitos
        if message.author == self.bot.user:
            return

        # Ignorar mensajes en el propio canal de logs para evitar logs redundantes del log
        if message.channel.id == LOG_CHANNEL_ID:
            return
        
        # NO HAY LÓGICA DE ENVÍO AQUÍ, SOLO SI ES NECESARIO PARA OTROS TIPOS DE LOGS
        pass # Puedes poner pass, o simplemente eliminar todo lo de abajo si lo habías comentado
        # ... (aquí no debería haber más lógica de envío de mensajes si solo quieres comandos)

async def setup(bot):
    await bot.add_cog(LoggingCog(bot))