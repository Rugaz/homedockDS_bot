# information_ticket_usage.py

import discord
from discord.ext import commands
import datetime
import json
import hashlib
import os

# --- CONFIGURATION IDs ---
# IMPORTANT: Replace 1382766275717234828 with your actual Discord channel ID for tickets.
TICKET_INFO_CHANNEL_ID = 1382766275717234828
CONFIG_FILE = 'config/ticket_info_config.json' # File to save the message ID and hash

class InformationTicketUsage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ticket_info_message_id = None
        self.last_ticket_info_hash = None
        self._load_config()

    def _load_config(self):
        """Loads the ticket info message ID and last hash from the config file."""
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                self.ticket_info_message_id = config.get('ticket_info_message_id')
                self.last_ticket_info_hash = config.get('last_ticket_info_hash')
                print(f"Log: Ticket info config loaded: message_id={self.ticket_info_message_id}, last_hash={self.last_ticket_info_hash}")
        except FileNotFoundError:
            print(f"Log: {CONFIG_FILE} not found. Will create a new one.")
        except json.JSONDecodeError:
            print(f"Log: Error decoding {CONFIG_FILE}. Starting with empty config.")
        except Exception as e:
            print(f"Log: Unexpected error loading ticket info config: {e}")

    def _save_config(self):
        """Saves the current ticket info message ID and hash to the config file."""
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True) # Ensure the directory exists
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({
                    'ticket_info_message_id': self.ticket_info_message_id,
                    'last_ticket_info_hash': self.last_ticket_info_hash
                }, f, indent=4)
            print(f"Log: Ticket info config saved: message_id={self.ticket_info_message_id}, last_hash={self.last_ticket_info_hash}")
        except Exception as e:
            print(f"Log: ERROR saving ticket info config: {e}")

    def _generate_ticket_info_embed_data(self):
        """Generates the data for the ticket information embed and returns it as a dictionary."""
        # Any change to this dictionary will result in a different hash, triggering an update.
        
        embed_dict = {
            "title": "🎟️ Our Ticket System: How it Works 🚀",
            "description": "Welcome! This guide explains how to get the most out of our ticket system for efficient support.",
            "color": 0x2ECC71, # A nice green color for support
            "fields": [
                {
                    "name": "─" * 20, # Separator
                    "value": "\u200b", # Zero Width Space for spacing
                    "inline": False
                },
                {
                    "name": "Categories & Specific Apps",
                    "value": (
                        "Our system is organized by categories, where **each category corresponds to specific applications or functionalities**. "
                        "When you open a ticket, select the category that best matches your query (e.g., 'Orders App' for order-related issues). "
                        "This ensures your request reaches the specialized team for that area."
                    ),
                    "inline": False
                },
                {
                    "name": "─" * 20, # Separator
                    "value": "\u200b",
                    "inline": False
                },
                {
                    "name": "Ticket Creation Process",
                    "value": (
                        "1. **Select Category:** Begin by choosing the relevant category for your issue.\n"
                        "2. **Provide Details:** The system will then prompt you for specific details about your problem within that app/category. "
                        "The more information you provide, the faster we can assist you!"
                    ),
                    "inline": False
                },
                {
                    "name": "─" * 20, # Separator
                    "value": "\u200b",
                    "inline": False
                },
                {
                    "name": "Ticket Generation & Tracking 📝",
                    "value": (
                        "Once submitted, a unique ticket will be generated for your request. "
                        "You'll receive a confirmation with your ticket reference number, allowing us to track its progress. "
                        "Our team will review it and get back to you here or via your preferred contact method."
                    ),
                    "inline": False
                },
                {
                    "name": "─" * 20, # Separator
                    "value": "\u200b",
                    "inline": False
                },
                {
                    "name": "Your Ticket Copy ✉️",
                    "value": (
                        "After your ticket is resolved and closed, the system will **automatically send you a copy of the resolution**. "
                        "This ensures you have a complete record of your inquiry and the solution provided for future reference."
                    ),
                    "inline": False
                },
                {
                    "name": "─" * 20, # Separator
                    "value": "\u200b",
                    "inline": False
                },
                {
                    "name": "Need help? Don't hesitate to open a ticket!",
                    "value": "\u200b", # Zero Width Space for spacing
                    "inline": False
                }
            ]
        }
        return embed_dict

    def _calculate_ticket_info_hash(self, embed_data):
        """Calculates a hash of the embed data to detect changes."""
        # Convert the dictionary to a sorted JSON string to ensure consistent hashing
        json_string = json.dumps(embed_data, sort_keys=True)
        return hashlib.sha256(json_string.encode('utf-8')).hexdigest()

    async def _send_or_update_ticket_info_message(self, ticket_info_channel):
        """Handles sending a new ticket info message or updating an existing one."""
        current_embed_data = self._generate_ticket_info_embed_data()
        current_hash = self._calculate_ticket_info_hash(current_embed_data)

        # Create the actual discord.Embed object from the data
        embed = discord.Embed(
            title=current_embed_data["title"],
            description=current_embed_data["description"],
            color=current_embed_data["color"]
        )
        for field in current_embed_data["fields"]:
            embed.add_field(name=field["name"], value=field["value"], inline=field["inline"])
        
        # Add dynamic footer with last update time
        embed.set_footer(text=f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        message_to_send = None # This will store the Discord message object (new or existing)

        # Try to find an existing message by its stored ID first
        if self.ticket_info_message_id:
            try:
                message_to_send = await ticket_info_channel.fetch_message(self.ticket_info_message_id)
                print(f"Log: Found existing ticket info message with ID: {self.ticket_info_message_id}")
            except discord.NotFound:
                print(f"Log: Existing ticket info message with ID {self.ticket_info_message_id} not found. Will attempt to find in history or create new.")
                self.ticket_info_message_id = None # Reset ID as it's no longer valid
            except discord.Forbidden:
                print(f"Log: ERROR: No permissions to fetch existing ticket info message {self.ticket_info_message_id}. Check 'Read Message History'.")
                return
            except Exception as e:
                print(f"Log: Unexpected error fetching ticket info message: {e}")
                self.ticket_info_message_id = None # Reset to try finding another way

        # If message not found by ID, search recent channel history (less reliable but fallback)
        if not message_to_send:
            try:
                # Search for messages sent by the bot that look like the ticket info message
                async for message in ticket_info_channel.history(limit=50): # Limit history search
                    if message.author == self.bot.user and message.embeds and \
                       message.embeds[0].title and "Ticket System" in message.embeds[0].title:
                        message_to_send = message
                        self.ticket_info_message_id = message.id # Store the ID of the found message
                        print(f"Log: Found existing ticket info message in history (ID: {self.ticket_info_message_id}).")
                        break
            except discord.Forbidden:
                print("Bot lacks permissions to read message history in this channel.")
                return
            except Exception as e:
                print(f"An error occurred while searching channel history: {e}")

        # Check if the content has changed or if no message was found
        if message_to_send and current_hash == self.last_ticket_info_hash:
            print("Log: Ticket information has not changed. No update needed for existing message.")
            return # No action needed if content hasn't changed and message exists

        # If content changed OR no message found, proceed to create/update
        try:
            if message_to_send: # If message was found but content changed, edit it
                await message_to_send.edit(embed=embed)
                print(f"Log: Ticket information message updated (ID: {self.ticket_info_message_id}).")
            else: # No message found, create a new one
                message_to_send = await ticket_info_channel.send(embed=embed)
                self.ticket_info_message_id = message_to_send.id
                print(f"Log: New ticket information message sent (ID: {self.ticket_info_message_id}).")
            
            # Save the new message ID and hash only after successful send/update
            self.last_ticket_info_hash = current_hash
            self._save_config()

        except discord.Forbidden:
            print(f"Log: ERROR: No permissions to send/edit messages in channel {ticket_info_channel.name}. Check 'Send Messages' and 'Embed Links' permissions.")
        except Exception as e:
            print(f"Log: ERROR sending/updating ticket information message: {e}")


    @commands.Cog.listener()
    async def on_ready(self):
        """
        Event listener that runs when the bot is ready.
        It calls the helper function to handle sending/updating the ticket information message.
        """
        print(f'Cog "{self.qualified_name}" for Ticket Information loaded and ready.')
        
        ticket_info_channel = self.bot.get_channel(TICKET_INFO_CHANNEL_ID)
        if not ticket_info_channel:
            print(f"Log: WARNING: Ticket Info channel with ID {TICKET_INFO_CHANNEL_ID} not found or not accessible. Verify ID and permissions.")
            return

        # Call the helper function to handle sending/updating the ticket information message
        await self._send_or_update_ticket_info_message(ticket_info_channel)


async def setup(bot):
    """
    Function to add the cog to the bot. This is called when the cog is loaded.
    """
    await bot.add_cog(InformationTicketUsage(bot))