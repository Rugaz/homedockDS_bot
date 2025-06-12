import discord
from discord.ext import commands
import datetime
import json
import hashlib
import os

# --- CONFIGURATION IDs ---
RESOURCES_CHANNEL_ID = 1381296490923954230 # ID of the resources channel
CONFIG_FILE = 'config/resources_config.json' # File to save the message ID and hash

class ResourcesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.resources_message_id = None
        self.last_resources_hash = None
        self._load_config()

    def _load_config(self):
        """Loads the resources message ID and last resources hash from the config file."""
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                self.resources_message_id = config.get('resources_message_id')
                self.last_resources_hash = config.get('last_resources_hash')
                print(f"Log: Resources config loaded: message_id={self.resources_message_id}, last_hash={self.last_resources_hash}")
        except FileNotFoundError:
            print(f"Log: {CONFIG_FILE} not found. Will create a new one.")
        except json.JSONDecodeError:
            print(f"Log: Error decoding {CONFIG_FILE}. Starting with empty config.")
        except Exception as e:
            print(f"Log: Unexpected error loading resources config: {e}")

    def _save_config(self):
        """Saves the current resources message ID and resources hash to the config file."""
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True) # Ensure the directory exists
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({
                    'resources_message_id': self.resources_message_id,
                    'last_resources_hash': self.last_resources_hash
                }, f, indent=4)
            print(f"Log: Resources config saved: message_id={self.resources_message_id}, last_hash={self.last_resources_hash}")
        except Exception as e:
            print(f"Log: ERROR saving resources config: {e}")

    def _generate_resources_embed_data(self):
        """Generates the data for the resources embed and returns it as a dictionary."""
        # Any change here will result in a different hash.
        
        embed_dict = {
            "title": "📚 Homedocks Essential Resources 📚",
            "description": "**Explore these helpful links to get the most out of Homedocks:**",
            "color": 0x3498DB, # A nice blue color
            "fields": [
                 {
                    "name": "─" * 20, # Separator
                    "value": "\u200b",
                    "inline": False
                },
                {
                    "name": "🌐 Overview & Introduction",
                    "value": (
                        "Get started with a comprehensive look at Homedock.cloud.\n"
                        "[Click Here!](https://docs.homedock.cloud/introduction/overview/)\n"
                        "\u200b" # Zero Width Space for spacing
                    ),
                    "inline": False
                },
                {
                    "name": "─" * 20, # Separator
                    "value": "\u200b",
                    "inline": False
                },
                {
                    "name": "🚀 Setup & Installation Guide",
                    "value": (
                        "Follow our step-by-step instructions to install Homedock.\n"
                        "[Start Installation!](https://docs.homedock.cloud/setup/installation/)\n"
                        "\u200b" # Zero Width Space for spacing
                    ),
                    "inline": False
                },
                {
                    "name": "─" * 20, # Separator
                    "value": "\u200b",
                    "inline": False
                },
                {
                    "name": "📊 Homedock OS Dashboard",
                    "value": (
                        "Learn about the Homedock OS user interface and features.\n"
                        "[Explore Dashboard!](https://docs.homedock.cloud/homedock-os/dashboard/)\n"
                        "\u200b" # Zero Width Space for spacing
                    ),
                    "inline": False
                },
                {
                    "name": "─" * 20, # Separator
                    "value": "\u200b",
                    "inline": False
                },
                {
                    "name": "☁️ Administration Panel & Cloud Instances",
                    "value": (
                        "Manage your Homedock server and cloud instances.\n"
                        "[Access Admin Panel!](https://docs.homedock.cloud/administration-panel/cloud-instances/)\n"
                        "\u200b" # Zero Width Space for spacing
                    ),
                    "inline": False
                },
                {
                    "name": "─" * 20, # Separator
                    "value": "\u200b",
                    "inline": False
                },
                {
                    "name": "🛠️ Troubleshooting: Multicast DNS",
                    "value": (
                        "Find solutions for common issues, like Multicast DNS problems.\n"
                        "[Get Troubleshooting Help!](https://docs.homedock.cloud/troubleshooting/multicast-dns/)\n"
                        "\u200b" # Zero Width Space for spacing
                    ),
                    "inline": False
                },
                {
                    "name": "─" * 20, # Separator
                    "value": "\u200b",
                    "inline": False
                },
                {
                    "name": "❓ Frequently Asked Questions (FAQ)",
                    "value": (
                        "Your quick guide to common questions and answers about Homedocks.\n"
                        "[View FAQs!](https://docs.homedock.cloud/others/frequently-asked-questions/)\n"
                        "\u200b" # Zero Width Space for spacing
                    ),
                    "inline": False
                },
            ]
        }
        return embed_dict

    def _calculate_resources_hash(self, resources_data):
        """Calculates a hash of the resources data to detect changes."""
        resources_json_string = json.dumps(resources_data, sort_keys=True)
        return hashlib.sha256(resources_json_string.encode('utf-8')).hexdigest()

    async def _send_or_update_resources_message(self, resources_channel):
        """Handles sending a new resources message or updating an existing one."""
        current_resources_embed_data = self._generate_resources_embed_data()
        current_resources_hash = self._calculate_resources_hash(current_resources_embed_data)

        # Create the actual discord.Embed object
        embed = discord.Embed(
            title=current_resources_embed_data["title"],
            description=current_resources_embed_data["description"],
            color=current_resources_embed_data["color"]
        )
        for field in current_resources_embed_data["fields"]:
            embed.add_field(name=field["name"], value=field["value"], inline=field["inline"])
        
        # Add dynamic footer
        embed.set_footer(text=f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        message_to_send = None # This will be the Discord message object (new or existing)

        # Try to find an existing message
        if self.resources_message_id:
            try:
                message_to_send = await resources_channel.fetch_message(self.resources_message_id)
                print(f"Log: Found existing resources message with ID: {self.resources_message_id}")
            except discord.NotFound:
                print(f"Log: Existing resources message with ID {self.resources_message_id} not found. Will create new.")
                self.resources_message_id = None # Reset ID so a new one is created
            except discord.Forbidden:
                print(f"Log: ERROR: No permissions to fetch existing resources message {self.resources_message_id}.")
                return
            except Exception as e:
                print(f"Log: Unexpected error fetching resources message: {e}")
                return

        # Check if resources have changed or if no message was found
        if message_to_send and current_resources_hash == self.last_resources_hash:
            print("Log: Resources have not changed. No update needed for existing message.")
            return # No action needed if resources haven't changed and message exists

        # If resources changed OR no message found, create/update
        try:
            if message_to_send: # If message was found but resources changed, edit it
                await message_to_send.edit(embed=embed)
                print(f"Log: Resources message updated (ID: {self.resources_message_id}).")
                logging_cog = self.bot.get_cog("LoggingCog")
                if logging_cog and logging_cog.log_channel:
                    await logging_cog.log_channel.send(
                        f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                        f"Resources message updated in channel **{resources_channel.name}**."
                    )
            else: # No message found, create a new one
                message_to_send = await resources_channel.send(embed=embed)
                self.resources_message_id = message_to_send.id
                print(f"Log: New resources message sent (ID: {self.resources_message_id}).")
                logging_cog = self.bot.get_cog("LoggingCog")
                if logging_cog and logging_cog.log_channel:
                    await logging_cog.log_channel.send(
                        f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                        f"New resources message created in channel **{resources_channel.name}**."
                    )
            
            # Save the new message ID and hash only after successful send/update
            self.last_resources_hash = current_resources_hash
            self._save_config()

        except discord.Forbidden:
            print(f"Log: ERROR: No permissions to send/edit messages in channel {resources_channel.name}. Check 'Send Messages' and 'Embed Links' permissions.")
        except Exception as e:
            print(f"Log: ERROR sending/updating resources message: {e}")


    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Cog "{self.qualified_name}" for Resources loaded and ready.')
        
        resources_channel = self.bot.get_channel(RESOURCES_CHANNEL_ID)
        if not resources_channel:
            print(f"Log: ADVERTENCIA: Resources channel with ID {RESOURCES_CHANNEL_ID} not found or not accessible. Verify ID and permissions.")
            return

        # Call the helper function to handle sending/updating the resources message
        await self._send_or_update_resources_message(resources_channel)


async def setup(bot):
    await bot.add_cog(ResourcesCog(bot))