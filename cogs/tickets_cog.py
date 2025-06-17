# cogs/tickets_cog.py
import discord
from discord.ext import commands
import datetime
import json
import hashlib
import asyncio
import os
import io

# --- CONFIGURATION IDs ---
# Dictionary mapping support channel IDs to their display names for the message
SUPPORT_CHANNELS = {
    1382444394312896633: "General Support", # support
    1382486713883951204: "Gaming Support", # support gaming
    1382486905098076210: "Web Support",     # support web
    1382486478118060142: "AI Support",      # support ia
    1382045233268789268: "Media Support",    # support media
    1382046270310453349: "Networking Support", # support networking
    1382456916134985750: "Dev Tools Support", # support dev tools (Corrected ID if typo was present, check this one)
    1382486039012180010: "Files & Productivity Support", # support files productivity
    1382486278917853264: "Home Automation Support", # support home automation
    1382486837154807891: "Social Support"    # support social
}

ARCHIVE_CHANNEL_ID = 1382761178551291924 # ID of the channel where tickets will be archived

# ID de la categoría donde se crearán los canales de ticket
TICKET_CATEGORY_ID = 1382766193232056340

# IDs de los roles de administrador/moderador que deben tener acceso a los tickets.
ADMIN_OR_MOD_ROLE_IDS = [
    1382054051130118327, # ID del primer rol (ej. 'Administrador' o 'Staff')
    1382762909897064528  # ID del segundo rol (ej. 'Moderador' o 'Soporte')
]

# ID del canal de logs, debe ser la misma que en logging_cog.py
LOG_CHANNEL_ID = 1382493194016522353 

CONFIG_FILE = 'config/tickets_config.json' # File to save message IDs and hashes per channel

# Max messages to fetch for transcript to prevent timeouts on very long tickets
MAX_TRANSCRIPT_MESSAGES = 1000 

# --- Views for Ticket Creation Buttons ---

# Define the view for the main ticket creation message in support channels
class TicketCreationView(discord.ui.View):
    def __init__(self, cog_instance: commands.Cog):
        super().__init__(timeout=None) # Keep view persistent even after bot restarts
        self.cog = cog_instance # Reference to the cog instance to call its methods

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Prevent bots from creating tickets (including this bot itself)
        if interaction.user.bot:
            await interaction.response.send_message("Bots cannot create tickets.", ephemeral=True)
            return False
        return True

    # Callback for App Problem button
    @discord.ui.button(label="App Problem", style=discord.ButtonStyle.blurple, custom_id="ticket_app_problem", emoji="💻")
    async def app_problem_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Always defer immediately to prevent "interaction failed" due to Discord's 3-second rule
        await interaction.response.defer(ephemeral=True)
        await self.cog.create_ticket_channel(interaction, "App Problem")

    # Callback for Web Problem button
    @discord.ui.button(label="Web Problem", style=discord.ButtonStyle.blurple, custom_id="ticket_web_problem", emoji="🌐")
    async def web_problem_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Always defer immediately
        await interaction.response.defer(ephemeral=True)
        await self.cog.create_ticket_channel(interaction, "Web Problem")

    # Callback for Discord Problem button
    @discord.ui.button(label="Discord Problem", style=discord.ButtonStyle.blurple, custom_id="ticket_discord_problem", emoji="💬")
    async def discord_problem_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Always defer immediately
        await interaction.response.defer(ephemeral=True)
        await self.cog.create_ticket_channel(interaction, "Discord Problem")


# --- Views for Ticket Closure Buttons ---
class TicketCloseView(discord.ui.View):
    def __init__(self, cog_instance: commands.Cog):
        super().__init__(timeout=None)
        self.cog = cog_instance
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Prevent bots from interacting with closure buttons
        if interaction.user.bot:
            return False
        
        # 1. Check if the user is an Administrator (highest permission)
        if interaction.user.guild_permissions.administrator:
            return True

        # 2. Check if the user has one of the specified ADMIN_OR_MOD_ROLE_IDS
        user_has_admin_mod_role = False
        for role_id in ADMIN_OR_MOD_ROLE_IDS:
            admin_mod_role = interaction.guild.get_role(role_id)
            if admin_mod_role and admin_mod_role in interaction.user.roles:
                user_has_admin_mod_role = True
                break
        
        if user_has_admin_mod_role:
            return True

        # 3. Check if the user is the channel creator by parsing the topic
        ticket_creator_id = None
        if interaction.channel.topic:
            try:
                # Assuming topic format: "Support ticket for Display Name (ID: 1234567890)"
                start_index = interaction.channel.topic.find("(ID: ")
                if start_index != -1:
                    end_index = interaction.channel.topic.find(")", start_index)
                    if end_index != -1:
                        ticket_creator_id = int(interaction.channel.topic[start_index + 5:end_index])
            except ValueError:
                pass # ID not found or not an integer

        if ticket_creator_id == interaction.user.id:
            return True

        await interaction.response.send_message("You do not have permission to close this ticket.", ephemeral=True)
        return False

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, custom_id="ticket_close_button", emoji="🔒")
    async def close_ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Defer immediately if not already deferred. This is crucial for the 3-second rule.
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True) 

        # Deshabilita los botones de esta vista inmediatamente para evitar clicks múltiples
        for item in self.children:
            item.disabled = True
        try:
            # Edita el mensaje original para deshabilitar los botones.
            await interaction.edit_original_response(view=self) 
        except discord.NotFound:
            print("Log: Original message for close button not found, probably already deleted.")
        except discord.Forbidden:
            print("Log: Bot lacks permissions to edit original message for close button.")
        except Exception as e:
            print(f"Log: Error editing original message to disable close button: {e}")

        # Extract ticket creator ID from channel topic
        ticket_creator_id = None
        if interaction.channel.topic and "(ID: " in interaction.channel.topic:
            try:
                ticket_creator_id = int(interaction.channel.topic.split('(ID: ')[1].split(')')[0])
            except (ValueError, IndexError):
                pass # Fallback to None

        # Determine if the closer is an admin/mod/server admin
        closer_is_admin_or_mod = False
        if interaction.user.guild_permissions.administrator:
            closer_is_admin_or_mod = True
        else:
            for role_id in ADMIN_OR_MOD_ROLE_IDS:
                admin_mod_role = interaction.guild.get_role(role_id)
                if admin_mod_role and admin_mod_role in interaction.user.roles:
                    closer_is_admin_or_mod = True
                    break

        if not closer_is_admin_or_mod and interaction.user.id == ticket_creator_id:
            # If the closer is NOT an admin/mod AND IS the creator, directly finalize as "user-closed"
            await interaction.followup.send("Closing your ticket. Archiving the conversation...", ephemeral=True)
            await self.cog.finalize_ticket_closure(interaction.channel, interaction.user, "user-closed", ticket_creator_id, closer_is_admin=False)
        elif closer_is_admin_or_mod:
            # If the closer IS an admin/mod, show confirmation buttons to mark status
            confirmation_embed = discord.Embed(
                title="Confirm Ticket Closure",
                description="Are you sure you want to close this ticket? Please mark its final status:",
                color=discord.Color.orange()
            )
            
            # Send a new message to the ticket channel with the confirmation buttons
            # Create the view instance here to pass to the message, and then store the message in it.
            confirmation_message_view = TicketClosureConfirmationView(self.cog, ticket_creator_id, closer_is_admin_or_mod)
            confirmation_message = await interaction.channel.send(
                embed=confirmation_embed, 
                view=confirmation_message_view 
            )
            confirmation_message_view.message = confirmation_message # Attach the message to the view instance

            await interaction.followup.send("Please confirm the ticket status in the channel.", ephemeral=True)
        else:
            # This case should ideally be caught by interaction_check, but good for safety
            await interaction.followup.send("You do not have permission to close this ticket in this manner.", ephemeral=True)


class TicketClosureConfirmationView(discord.ui.View):
    def __init__(self, cog_instance: commands.Cog, original_creator_id: int, closer_is_admin: bool):
        super().__init__(timeout=600) # Timeout after 10 minutes
        self.cog = cog_instance
        self.original_creator_id = original_creator_id # To pass to the cog for DM
        self.closer_is_admin = closer_is_admin # Pass this state to finalize_ticket_closure
        self.message = None # To store the message this view is attached to

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Only admins/mods should be able to confirm closure status
        if interaction.user.bot:
            return False
        
        # Check if the user has Administrator permission
        if interaction.user.guild_permissions.administrator:
            return True

        # Check if the user has one of the specified ADMIN_OR_MOD_ROLE_IDS
        for role_id in ADMIN_OR_MOD_ROLE_IDS:
            admin_mod_role = interaction.guild.get_role(role_id)
            if admin_mod_role and admin_mod_role in interaction.user.roles:
                return True
        
        await interaction.response.send_message("Only staff can mark ticket status.", ephemeral=True)
        return False

    async def on_timeout(self):
        # Disable buttons if nobody confirms within timeout
        for item in self.children:
            item.disabled = True
        # If the message exists, try to edit it to remove clickable buttons.
        if self.message:
            try:
                # Ensure the message still exists before trying to edit
                await self.message.edit(view=self, content="Ticket closure confirmation timed out. Please click 'Close Ticket' again to restart the process.")
            except discord.NotFound:
                print("Log: Confirmation message not found during timeout, likely already deleted with channel.")
                self.message = None # Clear message reference
            except discord.Forbidden:
                print("Log: Bot lacks permissions to edit confirmation message during timeout.")
                self.message = None
            except Exception as e:
                print(f"Log: Error disabling confirmation view on timeout: {e}")
        self.stop() # Stop the view to clean up its resources

    async def _handle_confirmation_click(self, interaction: discord.Interaction, status: str):
        # Disable buttons immediately to prevent further interactions
        for item in self.children:
            item.disabled = True
        try:
            # Edit the confirmation message itself to remove clickable buttons
            await interaction.message.edit(view=self)
        except discord.NotFound:
            print("Log: Confirmation message not found when trying to disable buttons after click.")
        except discord.Forbidden:
            print("Log: Bot lacks permissions to edit confirmation message to disable buttons.")
        except Exception as e:
            print(f"Log: Error disabling confirmation buttons: {e}")

        # The initial `close_ticket_button` already deferred the interaction.
        # For these follow-up buttons, we want to send a new message as a response,
        # or edit the original deferred response if we deferred it ephemeral.
        # Since the first defer was ephemeral, we use followup.send for public messages.
        await interaction.response.send_message(f"Initiating ticket closure with status: **{status.upper()}**...", ephemeral=True)

        # Finalize the closure process
        await self.cog.finalize_ticket_closure(
            interaction.channel, 
            interaction.user, 
            status, 
            self.original_creator_id, 
            self.closer_is_admin
        )
        self.stop() # Stop the view after the action is complete

    @discord.ui.button(label="Mark as Solved", style=discord.ButtonStyle.green, custom_id="ticket_solved_button", emoji="✅")
    async def solved_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_confirmation_click(interaction, "solved")

    @discord.ui.button(label="Mark as Unresolved", style=discord.ButtonStyle.red, custom_id="ticket_unresolved_button", emoji="❌")
    async def unresolved_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_confirmation_click(interaction, "unresolved")

# --- Main Ticket Cog ---
class TicketsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tickets_data = {} 
        self._load_config()

        self.bot.add_view(TicketCreationView(self))
        self.bot.add_view(TicketCloseView(self)) 

    def _load_config(self):
        """Loads the ticket message IDs and hashes for all support channels from the config file."""
        try:
            with open(CONFIG_FILE, 'r') as f:
                self.tickets_data = json.load(f)
                print(f"Log: Tickets config loaded: {self.tickets_data}")
        except FileNotFoundError:
            print(f"Log: {CONFIG_FILE} not found. Will create a new one.")
        except json.JSONDecodeError:
            print(f"Log: Error decoding {CONFIG_FILE}. Starting with empty config.")
        except Exception as e:
            print(f"Log: Unexpected error loading tickets config: {e}")

    def _save_config(self):
        """Saves the current ticket message IDs and hashes for all support channels to the config file."""
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True) # Ensure the directory exists
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.tickets_data, f, indent=4)
            print(f"Log: Tickets config saved.")
        except Exception as e:
            print(f"Log: ERROR saving tickets config: {e}")

    def _generate_ticket_embed_data(self, channel_id):
        """Generates the data for the ticket creation embed for a specific channel."""
        channel_name = SUPPORT_CHANNELS.get(channel_id, "Support") # Default to "Support" if ID not found

        description_text = (
            "Welcome to the **Homedocks Support System**!\n"
            "To get help, please click one of the buttons below that best describes your issue.\n"
            "This will create a private channel where our team can assist you.\n\n"
            "**Here are the available ticket types for __"
            f"{channel_name.upper()}"  # Enfatiza la categoría
            "__:**\n\n" 
            "**💻 App Problem:** For issues related to any application or software specific to this category.\n\n" 
            "**🌐 Web Problem:** For issues with websites, online services, or web platforms in this category.\n\n" 
            "**💬 Discord Problem:** For problems with Discord itself (permissions, server settings, bot issues, etc.) within this category.\n\n" 
            "Please be ready to provide as much detail as possible once your ticket is opened."
        )

        embed_dict = {
            "title": f"🎫 Homedocks | {channel_name} Ticket System 🎫",
            "description": description_text,
            "color": discord.Color.gold().value 
        }
        return embed_dict

    def _calculate_content_hash(self, embed_data):
        """Calculates a hash of the embed data to detect changes."""
        content_json_string = json.dumps(embed_data, sort_keys=True)
        return hashlib.sha256(content_json_string.encode('utf-8')).hexdigest()

    async def _manage_support_channel_message(self, channel: discord.TextChannel):
        """Manages the main ticket creation message in a given support channel."""
        channel_id_str = str(channel.id)
        embed_data = self._generate_ticket_embed_data(channel.id)
        current_hash = self._calculate_content_hash(embed_data)
        
        message_id = self.tickets_data.get(channel_id_str, {}).get('message_id')
        last_hash = self.tickets_data.get(channel_id_str, {}).get('last_content_hash')
        
        message_found = None

        if message_id:
            try:
                # Intenta buscar el mensaje existente
                message_found = await channel.fetch_message(message_id)
                print(f"Log: Found existing tickets message with ID: {message_id} in #{channel.name}")
            except discord.NotFound:
                # El mensaje no existe en Discord, pero el bot cree que sí.
                print(f"Log: Existing tickets message (ID: {message_id}) not found in #{channel.name}. It might have been deleted manually. Removing from config.")
                # Limpia la entrada para este canal, para que se envíe un nuevo mensaje.
                if channel_id_str in self.tickets_data:
                    del self.tickets_data[channel_id_str]
                self._save_config() # Guarda la configuración actualizada inmediatamente
                message_id = None # Reinicia message_id para que el siguiente bloque envíe un nuevo mensaje
            except discord.Forbidden:
                print(f"Log: WARNING: Bot does not have permissions to fetch message {message_id} in #{channel.name}. Skipping update for this channel.")
                return # Salir si no se puede acceder al mensaje

        if message_found and last_hash == current_hash:
            # Si el mensaje existe Y el contenido no ha cambiado
            print(f"Log: Tickets for #{channel.name} have not changed. No update needed for existing message.")
        else:
            # Si no hay mensaje, o el hash es diferente (contenido ha cambiado), o el mensaje fue borrado manualmente
            try:
                if message_found:
                    # El mensaje existe pero el contenido cambió, editarlo
                    updated_embed = discord.Embed.from_dict(embed_data)
                    await message_found.edit(embed=updated_embed, view=TicketCreationView(self))
                    print(f"Log: Existing tickets message in #{channel.name} updated successfully.")
                    new_message_id = message_found.id # Su ID no cambia al editar
                else:
                    # No hay mensaje, enviarlo de nuevo (o por primera vez)
                    new_message = await channel.send(embed=discord.Embed.from_dict(embed_data), view=TicketCreationView(self))
                    print(f"Log: New tickets message sent to #{channel.name}.")
                    new_message_id = new_message.id

                # Actualiza el config con el nuevo message_id y el nuevo hash
                self.tickets_data[channel_id_str] = {
                    'message_id': new_message_id,
                    'last_content_hash': current_hash
                }
                self._save_config()

            except discord.Forbidden:
                print(f"Log: ERROR: Bot lacks permissions to send/edit messages in #{channel.name}.")
            except Exception as e:
                print(f"Log: Unexpected error managing tickets message in #{channel.name}: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Cog "{self.qualified_name}" for Tickets loaded and ready.')
        
        for channel_id, display_name in SUPPORT_CHANNELS.items():
            support_channel = self.bot.get_channel(channel_id)
            if not support_channel:
                print(f"Log: ADVERTENCIA: Support channel '{display_name}' with ID {channel_id} not found or not accessible. Verify ID and permissions.")
                continue
            
            await self._manage_support_channel_message(support_channel)
            await asyncio.sleep(1) # Small delay to avoid hitting rate limits when managing multiple channels

    # --- Ticket Creation Logic ---
    async def create_ticket_channel(self, interaction: discord.Interaction, problem_type: str):
        # The interaction was already deferred in the button's callback.
        guild = interaction.guild
        user = interaction.user

        # Create channel name
        user_name_for_channel = user.global_name if user.global_name else user.name
        ticket_channel_name = f"ticket-{user_name_for_channel.lower().replace(' ', '-')}-{problem_type.lower().replace(' ', '-')}"
        ticket_channel_name = ticket_channel_name[:95] 
        ticket_channel_name = "".join(c for c in ticket_channel_name if c.isalnum() or c == '-')

        # Determine the source channel for the ticket (e.g., General Support)
        source_channel_name = SUPPORT_CHANNELS.get(interaction.channel_id, "Unknown Category")

        # Define category for ticket channels
        ticket_category = self.bot.get_channel(TICKET_CATEGORY_ID) # Fetch the category object
        if not ticket_category:
            print(f"Log: WARNING: Ticket category with ID {TICKET_CATEGORY_ID} not found. Tickets will be created without a category.")
            ticket_category = None # Fallback: if category not found, set to None so it creates it at top level

        # Define permissions for the new channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False), 
            user: discord.PermissionOverwrite(
                read_messages=True, 
                send_messages=True, 
                attach_files=True,
                embed_links=True
            ), 
            guild.me: discord.PermissionOverwrite( 
                read_messages=True, 
                send_messages=True, 
                manage_channels=True, 
                manage_messages=True  
            )
        }

        # Add permissions for each admin/moderator role in the list
        roles_to_mention = [] # New list to store role mentions for the welcome message
        roles_added_count = 0
        for role_id in ADMIN_OR_MOD_ROLE_IDS:
            admin_mod_role = guild.get_role(role_id)
            if admin_mod_role:
                overwrites[admin_mod_role] = discord.PermissionOverwrite(
                    read_messages=True, 
                    send_messages=True, 
                    manage_channels=True 
                ) 
                roles_to_mention.append(admin_mod_role.mention) # Add role mention to the list
                print(f"Log: Added {admin_mod_role.name} role (ID: {role_id}) to ticket channel overwrites.")
                roles_added_count += 1
            else:
                print(f"Log: WARNING: Admin/Mod role with ID {role_id} not found. Ensure the bot has access and the role exists.")
        
        if roles_added_count == 0:
            print("Log: WARNING: No ADMIN_OR_MOD_ROLE_IDS from the list were found or valid. Admins might not automatically see ticket channels.")


        try:
            # Create the actual text channel
            new_channel = await guild.create_text_channel(
                ticket_channel_name,
                overwrites=overwrites,
                category=ticket_category, 
                topic=f"Support ticket for {user.display_name} (ID: {user.id}) regarding a {problem_type}." 
            )
            print(f"Log: New ticket channel created: {new_channel.name} by {user.display_name}.")
            
            # Construct the mentions string for staff
            staff_mentions = ", ".join(roles_to_mention) if roles_to_mention else "Our support team"


            # Send initial welcome message in the new ticket channel
            welcome_embed = discord.Embed(
                title=f"👋 Welcome to your {problem_type} Ticket, {user.display_name}!",
                description=(
                    "Please describe your problem in detail below. Our team will review your issue and get back to you as soon as possible.\n"
                    "If your issue is resolved, or you no longer need assistance, you can close this ticket at any time by clicking the button below."
                ),
                color=discord.Color.green()
            )
            close_ticket_view = TicketCloseView(self) 
            
            # Send message with user mention AND staff mentions
            await new_channel.send(
                f"{user.mention} {staff_mentions}, a new ticket has been opened for you.", 
                embed=welcome_embed, 
                view=close_ticket_view
            )

            # Send the followup message after channel creation
            await interaction.followup.send(f"Your ticket channel has been created: {new_channel.mention}", ephemeral=True)

            # Envío de log al canal de logs
            log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                log_embed = discord.Embed(
                    title="🎟️ Nuevo Ticket Abierto",
                    color=discord.Color.blue()
                )
                log_embed.add_field(name="Abierto Por", value=user.mention, inline=True)
                log_embed.add_field(name="Tipo de Problema", value=problem_type, inline=True)
                log_embed.add_field(name="Canal de Origen", value=f"#{interaction.channel.name} ({source_channel_name})", inline=True)
                log_embed.add_field(name="Canal de Ticket", value=new_channel.mention, inline=True)
                log_embed.add_field(name="Hora de Apertura", value=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'), inline=True)
                log_embed.set_footer(text=f"ID del Ticket: {new_channel.id}")
                try:
                    await log_channel.send(embed=log_embed)
                    print(f"Log: Mensaje de nuevo ticket enviado al canal de logs para {new_channel.name}.")
                except discord.Forbidden:
                    print(f"Log: ERROR: No tengo permisos para enviar mensajes en el canal de logs ({LOG_CHANNEL_ID}).")
                except Exception as e:
                    print(f"Log: ERROR desconocido al enviar log de ticket abierto: {e}")
            else:
                print(f"Log: ADVERTENCIA: El canal de logs con ID {LOG_CHANNEL_ID} no fue encontrado o no está accesible en TicketsCog.")

        except discord.Forbidden:
            await interaction.followup.send("Error: I don't have permissions to create channels or set up their permissions. Please check my role permissions (Manage Channels, Manage Roles).", ephemeral=True)
            print("Log: ERROR: Bot lacks permissions to create or configure ticket channels.")
        except Exception as e:
            await interaction.followup.send(f"An unexpected error occurred while creating your ticket: {e}", ephemeral=True)
            print(f"Log: Unexpected error during ticket channel creation: {e}")

    # --- Ticket Closure Logic ---
    async def finalize_ticket_closure(self, channel: discord.TextChannel, closer: discord.Member, status: str, original_creator_id: int, closer_is_admin: bool):
        archive_channel = self.bot.get_channel(ARCHIVE_CHANNEL_ID)
        if not archive_channel:
            print(f"Log: ERROR: Archive channel with ID {ARCHIVE_CHANNEL_ID} not found. Cannot archive ticket.")
            # Intenta enviar un mensaje al canal del ticket antes de que se borre, si es posible.
            try:
                await channel.send("Error: The archive channel could not be found. Please contact an administrator.", delete_after=10)
            except: # Ignore any error if channel is already gone
                pass
            return

        closure_by_text = "by a staff member" if closer_is_admin else "by the ticket creator"
        
        # Send confirmation message to the ticket channel
        try:
            await channel.send(f"Ticket closure confirmed as **{status.upper()}** {closure_by_text} ({closer.display_name}). Compiling transcript...")
        except discord.Forbidden:
            print(f"Log: Bot lacks permissions to send confirmation message in ticket channel {channel.name}.")
        except Exception as e:
            print(f"Log: Error sending initial closure confirmation message: {e}")

        transcript_content_lines = [] # Collect all lines first
        transcript_content_lines.append(f"--- Ticket Transcript for Channel: #{channel.name} ---\n")
        
        ticket_creator_id_str = str(original_creator_id) if original_creator_id else "N/A"
        ticket_creator_name = "Unknown User"
        if channel.topic and "(ID: " in channel.topic:
            try:
                start_name_idx = channel.topic.find("for ")
                end_name_idx = channel.topic.find(" (ID:")
                if start_name_idx != -1 and end_name_idx != -1 and start_name_idx < end_name_idx:
                    ticket_creator_name = channel.topic[start_name_idx + len("for "):end_name_idx].strip()
            except Exception:
                pass 

        transcript_content_lines.append(f"Ticket opened by: {ticket_creator_name} (ID: {ticket_creator_id_str})\n")
        transcript_content_lines.append(f"Ticket opened at: {channel.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        transcript_content_lines.append(f"Ticket closed by: {closer.display_name} (ID: {closer.id})\n")
        transcript_content_lines.append(f"Ticket closed at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        transcript_content_lines.append(f"Final Status: {status.upper()}\n") 
        transcript_content_lines.append(f"Closed by Role: {'Admin/Mod' if closer_is_admin else 'User'}\n")
        transcript_content_lines.append("-" * 50 + "\n\n")

        # Fetch messages for transcript - LİMİTED TO MAX_TRANSCRIPT_MESSAGES
        try:
            messages_fetched = []
            async for message in channel.history(limit=MAX_TRANSCRIPT_MESSAGES, oldest_first=True):
                if message.author == self.bot.user and (
                    (message.embeds and "Welcome to your" in (message.embeds[0].title if message.embeds else "")) or
                    (message.content and "Ticket closure confirmed as" in message.content) or
                    (message.embeds and "Confirm Ticket Closure" in (message.embeds[0].title if message.embeds else False)) or
                    (message.components and any(c.custom_id in ["ticket_close_button", "ticket_solved_button", "ticket_unresolved_button"] for row in message.components for c in row.children))
                ):
                    continue

                msg_line = f"[{message.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {message.author.display_name} ({message.author.id}): {message.content}\n"
                messages_fetched.append(msg_line)
                if message.attachments:
                    for attachment in message.attachments:
                        messages_fetched.append(f"        Attachment: {attachment.url}\n")
            
            transcript_content_lines.extend(messages_fetched)
            transcript_full_content = "".join(transcript_content_lines) # Join all lines once

            # Determine color for archive embed based on status and closer
            embed_color = discord.Color.green() if status == "solved" else discord.Color.red()
            if status == "user-closed": # Specific color for user-closed
                embed_color = discord.Color.greyple()

            # --- SEND TRANSCRIPT TO ARCHIVE CHANNEL ---
            try:
                # Create a NEW StringIO object for the archive channel
                transcript_file_archive = io.StringIO(transcript_full_content)
                archive_filename = f"transcript-{channel.name}.txt"
                archive_file_obj = discord.File(transcript_file_archive, filename=archive_filename)

                archive_embed = discord.Embed(
                    title=f"Ticket Closed: {channel.name} ({status.upper()})", 
                    description=f"Ticket by <@{ticket_creator_id_str}> closed by {closer.mention}.",
                    color=embed_color
                )
                archive_embed.add_field(name="Channel", value=f"#{channel.name}", inline=True)
                archive_embed.add_field(name="Opened At", value=channel.created_at.strftime('%Y-%m-%d %H:%M:%S UTC'), inline=True)
                archive_embed.add_field(name="Closed At", value=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'), inline=True)
                archive_embed.add_field(name="Closer", value=closer.mention, inline=True)
                archive_embed.add_field(name="Final Status", value=status.upper(), inline=True) 
                archive_embed.add_field(name="Closed by Role", value="Admin/Mod" if closer_is_admin else "User", inline=True)
                archive_embed.set_footer(text=f"Ticket ID: {channel.id}")

                await archive_channel.send(embed=archive_embed, file=archive_file_obj)
                print(f"Log: Ticket {channel.name} archived successfully with status: {status} by {'admin' if closer_is_admin else 'user'}.")
            except discord.HTTPException as http_e:
                print(f"Log: ERROR sending transcript to archive channel ({ARCHIVE_CHANNEL_ID}): HTTP error {http_e.status} - {http_e.text}. Likely file size limit or rate limit. Transcript content length: {len(transcript_full_content)} bytes.")
                await channel.send(f"⚠️ Error archiving transcript: {http_e.text}. The channel will still be deleted.", delete_after=10)
            except Exception as e:
                print(f"Log: Unexpected ERROR archiving transcript for {channel.name}: {e}")
                await channel.send(f"⚠️ An unexpected error occurred while archiving the transcript: {e}. The channel will still be deleted.", delete_after=10)


            # --- SEND LOG OF TICKET CLOSURE TO LOG CHANNEL ---
            log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                log_embed_close = discord.Embed(
                    title="Ticket Cerrado",
                    description=f"El ticket {channel.name} ha sido cerrado.",
                    color=embed_color 
                )
                log_embed_close.add_field(name="Canal", value=f"#{channel.name}", inline=True)
                log_embed_close.add_field(name="Cerrado Por", value=closer.mention, inline=True)
                log_embed_close.add_field(name="Creador Original", value=f"<@{original_creator_id}>" if original_creator_id else "N/A", inline=True)
                log_embed_close.add_field(name="Estado Final", value=status.upper(), inline=True)
                log_embed_close.add_field(name="Rol de Cierre", value="Admin/Mod" if closer_is_admin else "Usuario", inline=True)
                log_embed_close.add_field(name="Hora de Cierre", value=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'), inline=True)
                log_embed_close.set_footer(text=f"ID del Ticket: {channel.id}")
                try:
                    # Create a NEW StringIO object for the log channel
                    transcript_file_log = io.StringIO(transcript_full_content)
                    log_filename = f"log_transcript_{channel.name}.txt"
                    log_file_obj = discord.File(transcript_file_log, filename=log_filename)
                    
                    await log_channel.send(embed=log_embed_close, file=log_file_obj)
                    print(f"Log: Mensaje de cierre de ticket enviado al canal de logs para {channel.name}.")
                except discord.Forbidden:
                    print(f"Log: ERROR: No tengo permisos para enviar mensajes en el canal de logs ({LOG_CHANNEL_ID}) al cerrar un ticket.")
                except discord.HTTPException as http_e:
                    print(f"Log: ERROR sending transcript to log channel ({LOG_CHANNEL_ID}): HTTP error {http_e.status} - {http_e.text}. Likely file size limit or rate limit. Transcript content length: {len(transcript_full_content)} bytes.")
                except Exception as e:
                    print(f"Log: ERROR desconocido al enviar log de cierre de ticket: {e}")

            # --- SEND DM TO USER (IF POSSIBLE) ---
            if original_creator_id and original_creator_id != "N/A":
                try:
                    ticket_creator = await self.bot.fetch_user(int(original_creator_id))
                    if ticket_creator:
                        dm_description = ""
                        if status == "solved":
                            dm_description = f"Your support ticket in **#{channel.name}** has been closed by {closer.display_name} with status: **Solved**.\nWe hope your issue was resolved!"
                        elif status == "unresolved":
                            dm_description = f"Your support ticket in **#{channel.name}** has been closed by {closer.display_name} with status: **Unresolved**.\nIf your issue persists, please open a new ticket."
                        elif status == "user-closed":
                            dm_description = f"Your support ticket in **#{channel.name}** has been closed by you.\nIf you need further assistance, please open a new ticket."

                        dm_embed = discord.Embed(
                            title="Your Homedocks Ticket Has Been Closed",
                            description=dm_description,
                            color=discord.Color.light_grey()
                        )
                        dm_embed.add_field(name="Ticket Channel", value=f"#{channel.name}", inline=True)
                        dm_embed.add_field(name="Closed By", value=closer.display_name, inline=True)
                        dm_embed.add_field(name="Final Status", value=status.upper(), inline=True) 
                        dm_embed.set_footer(text="Thank you for using Homedocks Support!")
                        
                        # Create a NEW StringIO object for the DM
                        transcript_file_dm = io.StringIO(transcript_full_content)
                        dm_filename = f"transcript-{channel.name}.txt"
                        dm_file_obj = discord.File(transcript_file_dm, filename=dm_filename)

                        await ticket_creator.send(embed=dm_embed, file=dm_file_obj)
                        print(f"Log: Transcript DM sent to {ticket_creator.display_name}.")
                except (discord.Forbidden, discord.HTTPException) as dm_e:
                    print(f"Log: Could not send DM to ticket creator {original_creator_id}: {dm_e}. Likely DMs disabled or file too large. Transcript content length: {len(transcript_full_content)} bytes.")
                except Exception as ex:
                    print(f"Log: Unexpected error sending DM for transcript: {ex}")

            # Delete the ticket channel
            await channel.delete(reason=f"Ticket closed by {closer.display_name} ({status})")
            print(f"Log: Ticket channel {channel.name} deleted.")

        except discord.Forbidden:
            # If bot can't send messages to the ticket channel (already deleted by someone else, or perms issue)
            print(f"Log: ERROR: Bot lacks permissions to send final messages/archive/delete ticket channel {channel.name}. Channel might be gone.")
        except Exception as e:
            print(f"Log: An unexpected error occurred during ticket closure for {channel.name}: {e}")


async def setup(bot):
    await bot.add_cog(TicketsCog(bot))