# cogs/reaction_roles_cog.py
import discord
from discord.ext import commands
import datetime
import asyncio

# --- CONFIGURACIÓN DE IDS ---
REACTION_CHANNEL_ID = 1382490687391400057
# ¡IMPORTANTE! Para que el bot genere un nuevo mensaje, esta línea DEBE ser:
REACTION_MESSAGE_ID = 1382654357127954453 
# Si el bot ya ha generado un mensaje y tienes su ID, actualízala aquí para que el bot lo use.
# Por ejemplo: REACTION_MESSAGE_ID = 1382528541052112899

EMOJI_ROLE_MAP = {
    "🪟": 1382519354629029928,  # ID del rol de Windows
    "🍎": 1382519429736304650,  # ID del rol de macOS
    "🐧": 1382519529455747072,  # ID del rol de Linux
    "🍓": 1382519599861338212   # ID del rol de Raspberry Pi
}

class ReactionRolesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reaction_message = None

    async def _remove_other_os_roles(self, member, current_role_id_to_keep):
        """
        Quita todos los roles de sistema operativo del usuario, excepto el que se le acaba de dar.
        """
        guild = member.guild
        roles_to_remove = []
        
        all_os_role_ids = list(EMOJI_ROLE_MAP.values())

        for os_role_id in all_os_role_ids:
            if os_role_id == current_role_id_to_keep:
                continue

            role_obj = guild.get_role(os_role_id)
            if role_obj and role_obj in member.roles:
                roles_to_remove.append(role_obj)
        
        if roles_to_remove:
            try:
                await member.remove_roles(*roles_to_remove)
                removed_names = ", ".join([r.name for r in roles_to_remove])
                print(f"Log: Roles '{removed_names}' eliminados de {member.display_name} para asegurar selección única de SO.")
                
                logging_cog = self.bot.get_cog("LoggingCog")
                if logging_cog and logging_cog.log_channel:
                    await logging_cog.log_channel.send(
                        f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                        f"Roles **{removed_names}** eliminados de **{member.display_name}** (ID: {member.id}) "
                        f"para mantener una única selección de SO."
                    )
            except discord.Forbidden:
                print(f"Log: ERROR: No tengo permisos para eliminar roles al asegurar selección única de {member.display_name}. Verifique la jerarquía de roles del bot.")
            except Exception as e:
                print(f"Log: ERROR desconocido al intentar eliminar roles para selección única: {e}")

    async def _clear_other_reactions_for_user(self, message, user, correct_emoji_str):
        """
        Asegura que un usuario solo tenga la reacción de `correct_emoji_str` en el mensaje,
        eliminando cualquier otra reacción de rol que haya podido tener previamente.
        """
        try:
            # Siempre obtenemos el mensaje fresco para trabajar con las reacciones más actuales.
            fresh_message = await message.channel.fetch_message(message.id)
        except (discord.NotFound, discord.Forbidden) as e:
            print(f"Log: ERROR: No se pudo obtener el mensaje fresco para limpiar reacciones: {e}")
            return

        for reaction in fresh_message.reactions:
            if str(reaction.emoji) in EMOJI_ROLE_MAP and str(reaction.emoji) != correct_emoji_str:
                try:
                    await reaction.remove(user)
                    print(f"Log: Reacción '{reaction.emoji}' de {user.display_name} eliminada para asegurar selección única visual.")
                    await asyncio.sleep(0.1) 
                except discord.NotFound:
                    pass
                except discord.Forbidden:
                    print(f"Log: ERROR: No tengo permisos para eliminar reacciones de {user.display_name}. Verifique el permiso 'Gestionar Mensajes' del bot.")
                except Exception as e:
                    print(f"Log: ERROR desconocido al limpiar la reacción '{reaction.emoji}': {e}")


    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Cog "{self.qualified_name}" de Reaction Roles cargado y listo.')
        
        reaction_channel = self.bot.get_channel(REACTION_CHANNEL_ID)
        if not reaction_channel:
            print(f"Log: ADVERTENCIA: Canal de reacción con ID {REACTION_CHANNEL_ID} no encontrado o no accesible. Verifique la ID y permisos.")
            return

        global REACTION_MESSAGE_ID 
        
        # Intentar obtener el mensaje existente si la ID está configurada
        if REACTION_MESSAGE_ID is not None:
            try:
                self.reaction_message = await reaction_channel.fetch_message(REACTION_MESSAGE_ID)
                print(f"Log: Mensaje de reacción EXISTENTE obtenido. ID: {REACTION_MESSAGE_ID}")
            except discord.NotFound:
                print(f"Log: ADVERTENCIA: Mensaje de reacción con ID {REACTION_MESSAGE_ID} no encontrado en el canal {REACTION_CHANNEL_ID}.")
                print(f"Log: Se procederá a crear un nuevo mensaje.")
                REACTION_MESSAGE_ID = None # <--- ¡Resetear a None para que el bot cree uno nuevo!
            except discord.Forbidden:
                print(f"Log: ERROR: No tengo permisos para leer el historial del canal {REACTION_CHANNEL_ID}. Verifique los permisos 'Leer Historial de Mensajes'.")
                return # Si no hay permisos para leer, no podemos hacer nada.
            except Exception as e:
                print(f"Log: ERROR desconocido al obtener el mensaje de reacción: {e}")
                return

        # Si REACTION_MESSAGE_ID es None (porque lo era desde el inicio o porque el mensaje no se encontró),
        # entonces creamos un nuevo mensaje.
        if REACTION_MESSAGE_ID is None:
            try:
                embed = discord.Embed(
                    title="Selecciona tu Sistema Operativo",
                    description="Reacciona con el emoji correspondiente para obtener tu rol de SO:",
                    color=discord.Color.blue()
                )
                embed.add_field(name="🪟 Windows", value="Reacciona para obtener el rol de **Windows**.", inline=False)
                embed.add_field(name="🍎 macOS", value="Reacciona para obtener el rol de **macOS**.", inline=False)
                embed.add_field(name="🐧 Linux", value="Reacciona para obtener el rol de **Linux**.", inline=False)
                embed.add_field(name="🍓 Raspberry Pi", value="Reacciona para obtener el rol de **Raspberry Pi**.", inline=False)
                embed.set_footer(text="Haz clic en una reacción para obtener el rol, o desclic para quitarlo.\n(Solo puedes tener un rol de SO a la vez).")

                self.reaction_message = await reaction_channel.send(embed=embed)
                REACTION_MESSAGE_ID = self.reaction_message.id
                print(f"Log: Mensaje de reacción ENVIADO EXITOSAMENTE. ID: {REACTION_MESSAGE_ID}")
                print(f"Log: ¡¡¡IMPORTANTE!!! Por favor, actualiza la variable REACTION_MESSAGE_ID en este archivo (cogs/reaction_roles_cog.py)")
                print(f"Log: con la ID: {REACTION_MESSAGE_ID} y REINICIA el bot para que funcione correctamente en futuros inicios.")

            except discord.Forbidden:
                print(f"Log: ERROR: No tengo permisos para enviar mensajes en el canal {REACTION_CHANNEL_ID}. Verifique los permisos 'Enviar Mensajes'.")
                return
            except Exception as e:
                print(f"Log: ERROR al enviar el mensaje de reacción: {e}")
                return
        
        # Si self.reaction_message está definido (ya sea uno existente o uno nuevo), añadimos las reacciones
        if self.reaction_message:
            for emoji_str in EMOJI_ROLE_MAP.keys():
                try:
                    found_reaction = False
                    for reaction in self.reaction_message.reactions:
                        if str(reaction.emoji) == emoji_str and reaction.me: 
                            found_reaction = True
                            break
                    if not found_reaction:
                        await self.reaction_message.add_reaction(emoji_str)
                        print(f"Log: Reacción '{emoji_str}' añadida por el bot a mensaje {self.reaction_message.id}.")
                except discord.HTTPException as e:
                    if "Already added" not in str(e): 
                        print(f"Log: Advertencia/Error al añadir reacción '{emoji_str}' a mensaje {self.reaction_message.id}: {e}")
                except Exception as e:
                    print(f"Log: Error inesperado al añadir reacción '{emoji_str}': {e}")
        else:
            print("Log: No se pudo configurar el mensaje de reacción para añadir emojis (objeto de mensaje no disponible).")


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """
        Se ejecuta cuando un usuario añade una reacción a un mensaje.
        Asigna el rol correspondiente y quita los demás roles y reacciones del SO para selección única.
        """
        if payload.message_id != REACTION_MESSAGE_ID:
            return

        if payload.user_id == self.bot.user.id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild: return

        member = guild.get_member(payload.user_id)
        if not member:
            try: member = await guild.fetch_member(payload.user_id)
            except (discord.NotFound, discord.Forbidden): return
        if not member: return

        emoji_identifier = str(payload.emoji)
        role_id_to_add = EMOJI_ROLE_MAP.get(emoji_identifier)

        if role_id_to_add:
            role_to_add = guild.get_role(role_id_to_add)
            if role_to_add:
                await self._remove_other_os_roles(member, role_id_to_add)
                
                if role_to_add not in member.roles:
                    try:
                        await member.add_roles(role_to_add)
                        print(f"Log: Rol '{role_to_add.name}' añadido a {member.display_name} por reacción '{emoji_identifier}'.")
                        logging_cog = self.bot.get_cog("LoggingCog")
                        if logging_cog and logging_cog.log_channel:
                            await logging_cog.log_channel.send(
                                f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                                f"Rol **{role_to_add.name}** añadido a **{member.display_name}** (ID: {member.id}) "
                                f"por reacción '{emoji_identifier}' en mensaje ID {payload.message_id}."
                            )
                    except discord.Forbidden:
                        print(f"Log: ERROR: No tengo permisos para añadir el rol '{role_to_add.name}' a {member.display_name}. Verifique la jerarquía de roles del bot.")
                    except Exception as e:
                        print(f"Log: ERROR desconocido al añadir rol por reacción: {e}")

                if self.reaction_message:
                    await self._clear_other_reactions_for_user(self.reaction_message, member, emoji_identifier)
                else:
                    print(f"Log: Advertencia: No se pudo limpiar reacciones redundantes porque reaction_message no está disponible.")
            else:
                print(f"Log: ADVERTENCIA: Rol con ID {role_id_to_add} no encontrado en el gremio para emoji '{emoji_identifier}'.")


    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """
        Se ejecuta cuando un usuario elimina una reacción de un mensaje.
        Quita el rol correspondiente.
        """
        if payload.message_id != REACTION_MESSAGE_ID:
            return

        if payload.user_id == self.bot.user.id:
            # Ignorar eliminaciones de reacciones del propio bot para evitar bucles.
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild: return

        member = guild.get_member(payload.user_id)
        if not member:
            try: member = await guild.fetch_member(payload.user_id)
            except (discord.NotFound, discord.Forbidden): return
        if not member: return
        
        emoji_identifier = str(payload.emoji)

        role_id_to_remove = EMOJI_ROLE_MAP.get(emoji_identifier)

        if role_id_to_remove:
            role_to_remove = guild.get_role(role_id_to_remove)
            if role_to_remove:
                if role_to_remove in member.roles:
                    try:
                        await member.remove_roles(role_to_remove)
                        print(f"Log: Rol '{role_to_remove.name}' eliminado de {member.display_name} por quitar reacción '{emoji_identifier}'.")
                        logging_cog = self.bot.get_cog("LoggingCog")
                        if logging_cog and logging_cog.log_channel:
                            await logging_cog.log_channel.send(
                                f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                                f"Rol **{role_to_remove.name}** eliminado de **{member.display_name}** (ID: {member.id}) "
                                f"por quitar reacción '{emoji_identifier}' en mensaje ID {payload.message_id}."
                            )
                    except discord.Forbidden:
                        print(f"Log: ERROR: No tengo permisos para eliminar el rol '{role_to_remove.name}' de {member.display_name}. Verifique la jerarquía de roles del bot.")
                    except Exception as e:
                        print(f"Log: ERROR al eliminar rol por reacción: {e}")
            else:
                print(f"Log: ADVERTENCIA: Rol con ID {role_id_to_remove} no encontrado en el gremio para emoji '{emoji_identifier}'.")

async def setup(bot):
    await bot.add_cog(ReactionRolesCog(bot))