import discord
from discord.ext import commands
import datetime
import json
import hashlib

# --- CONFIGURATION IDs ---
RULES_CHANNEL_ID = 1381296490923954228 # ID of the rules channel
CONFIG_FILE = 'config/rules_config.json' # File to save the message ID and hash

class RulesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rules_message_id = None
        self.last_rules_hash = None
        self.rules_embed_data = {} # To store the structure of the rules embed
        self._load_config()

    def _load_config(self):
        """Loads the rules message ID and last rules hash from the config file."""
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                self.rules_message_id = config.get('rules_message_id')
                self.last_rules_hash = config.get('last_rules_hash')
                print(f"Log: Rules config loaded: message_id={self.rules_message_id}, last_hash={self.last_rules_hash}")
        except FileNotFoundError:
            print(f"Log: {CONFIG_FILE} not found. Will create a new one.")
        except json.JSONDecodeError:
            print(f"Log: Error decoding {CONFIG_FILE}. Starting with empty config.")
        except Exception as e:
            print(f"Log: Unexpected error loading config: {e}")

    def _save_config(self):
        """Saves the current rules message ID and rules hash to the config file."""
        import os
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({
                    'rules_message_id': self.rules_message_id,
                    'last_rules_hash': self.last_rules_hash
                }, f, indent=4)
            print(f"Log: Rules config saved: message_id={self.rules_message_id}, last_hash={self.last_rules_hash}")
        except Exception as e:
            print(f"Log: ERROR saving rules config: {e}")

    def _generate_rules_embed_data(self):
        """Generates the data for the rules embed and returns it as a dictionary."""
        # Any change here will result in a different hash.
        
        embed_dict = {
            "title": "📜 Homedocks Community Rules 📜",
            "description": "**To maintain a positive and productive environment for everyone, please read and respect these guidelines:**",
            "color": 0x00FF00, # A nice green color (hexadecimal)
            "fields": [
                 {
                    # Separator field
                    "name": "─" * 20,
                    "value": "\u200b",
                    "inline": False
                },
                {
                    "name": "🤝 1. Be Excellent to Each Other",
                    "value": (
                        "Our community thrives on **mutual respect**. **Toxic behavior in any form is strictly prohibited**, including, but not limited to:\n"
                        "\n" # Added blank line for spacing
                        "•  Discrimination (based on race, gender, sexual orientation, nationality, etc.)\n"
                        "•  Harassment, flaming, provoking/baiting other users.\n"
                        "•  Doxxing (revealing personal information of others).\n"
                        "•  Excessive vulgarity.\n"
                        "\u200b" # Zero Width Space for extra vertical spacing after the rule
                    ),
                    "inline": False
                },
                {
                    # Separator field
                    "name": "─" * 20, # A decorative line
                    "value": "\u200b", # Zero Width Space
                    "inline": False
                },
                {
                    "name": "🔗 2. Welcome Sharing, No Advertising or Spamming",
                    "value": (
                        "We love it when you share cool things! However, please **refrain from any form of unsolicited advertising or spam**.\n"
                        "\n" # Added blank line for spacing
                        "If you have something specific to discuss, the `Create Thread` feature is a great way to have a focused conversation.\n"
                        "\u200b" # Zero Width Space for extra vertical spacing
                    ),
                    "inline": False
                },
                {
                    # Separator field
                    "name": "─" * 20,
                    "value": "\u200b",
                    "inline": False
                },
                {
                    "name": "🇬🇧 3. We Primarily Communicate in English",
                    "value": (
                        "The primary language spoken on this server is **English**.\n"
                        "\n" # Added blank line for spacing
                        "We may add new channels in specific languages based on the languages our community mods can speak. Feel free to join the mod team!\n"
                        "If you choose to speak in another language, please be aware you may not receive an immediate response or any response at all.\n"
                        "\u200b" # Zero Width Space for extra vertical spacing
                    ),
                    "inline": False
                },
                {
                    # Separator field
                    "name": "─" * 20,
                    "value": "\u200b",
                    "inline": False
                },
                {
                    "name": "🚨 4. Also Refer to Discord Community Guidelines",
                    "value": (
                        "In addition to our server rules, it is essential that you follow the **Discord Community Guidelines**.\n"
                        "\n" # Added blank line for spacing
                        "You can review them here: [Discord Community Guidelines](https://discord.com/guidelines)\n"
                        "\u200b" # Zero Width Space for extra vertical spacing
                    ),
                    "inline": False
                },
                {
                    # Separator field
                    "name": "─" * 20,
                    "value": "\u200b",
                    "inline": False
                },
                {
                    "name": "🌍 5. Timezones Exist!",
                    "value": (
                        "Keep in mind that most of the Homedocks team is located in **Spain (UTC/GMT +2 hours)**.\n"
                        "\n" # Added blank line for spacing
                        "Therefore, responses to your questions or comments may not be immediate. We appreciate your patience!\n"
                        "\u200b" # Zero Width Space for extra vertical spacing
                    ),
                    "inline": False
                },
                {
                    # Separator field
                    "name": "─" * 20,
                    "value": "\u200b",
                    "inline": False
                },
                {
                    "name": "🚫 6. No Illegal Software",
                    "value": (
                        "Sharing, discussing, or promoting **illegal software** (including cracks, pirated licenses, etc.) is **strictly prohibited**.\n"
                        "\n" # Added blank line for spacing
                        "Violation of this rule will result in an **immediate ban** from the server.\n"
                        "\u200b" # Zero Width Space for extra vertical spacing
                    ),
                    "inline": False
                },
                {
                    # Separator field
                    "name": "─" * 20,
                    "value": "\u200b",
                    "inline": False
                },
                {
                    "name": "👮‍♀️ 7. Follow Moderator Instructions",
                    "value": (
                        "Our moderators are here to ensure a safe and orderly environment. Please **always follow their instructions** and decisions.\n"
                        "\n" # Added blank line for spacing
                        "If you have questions or a problem, contact a moderator directly.\n"
                        "\u200b" # Zero Width Space for extra vertical spacing
                    ),
                    "inline": False
                },
                {
                    # Separator field
                    "name": "─" * 20,
                    "value": "\u200b",
                    "inline": False
                },
                {
                    "name": "💬 8. Keep Discussions Relevant",
                    "value": (
                        "Please keep discussions relevant to Homedocks products and technology in the main channels.\n"
                        "\n" # Added blank line for spacing
                        "For unrelated topics, kindly move them to the designated **`off-topic` channel**.\n"
                        "\u200b" # Zero Width Space for extra vertical spacing
                    ),
                    "inline": False
                },
                {
                    # Separator field
                    "name": "─" * 20,
                    "value": "\u200b",
                    "inline": False
                },
                {
                    "name": "🎉 9. Have Fun!",
                    "value": "**Most importantly, enjoy your time at Homedocks and learn from our amazing community. Welcome!**\n\u200b", # Increased emphasis and spacing
                    "inline": False
                },
            ]
        }
        return embed_dict

    def _calculate_rules_hash(self, rules_data):
        """Calculates a hash of the rules data to detect changes."""
        rules_json_string = json.dumps(rules_data, sort_keys=True)
        return hashlib.sha256(rules_json_string.encode('utf-8')).hexdigest()

    async def _send_or_update_rules_message(self, rules_channel):
        """Handles sending a new rules message or updating an existing one."""
        current_rules_embed_data = self._generate_rules_embed_data()
        current_rules_hash = self._calculate_rules_hash(current_rules_embed_data)

        embed = discord.Embed(
            title=current_rules_embed_data["title"],
            description=current_rules_embed_data["description"],
            color=current_rules_embed_data["color"]
        )
        for field in current_rules_embed_data["fields"]:
            embed.add_field(name=field["name"], value=field["value"], inline=field["inline"])
        
        embed.set_footer(text=f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        message_to_send = None

        if self.rules_message_id:
            try:
                message_to_send = await rules_channel.fetch_message(self.rules_message_id)
                print(f"Log: Found existing rules message with ID: {self.rules_message_id}")
            except discord.NotFound:
                print(f"Log: Existing rules message with ID {self.rules_message_id} not found. Will create new.")
                self.rules_message_id = None
            except discord.Forbidden:
                print(f"Log: ERROR: No permissions to fetch existing rules message {self.rules_message_id}.")
                return
            except Exception as e:
                print(f"Log: Unexpected error fetching rules message: {e}")
                return

        if message_to_send and current_rules_hash == self.last_rules_hash:
            print("Log: Rules have not changed. No update needed for existing message.")
            return

        try:
            if message_to_send: 
                await message_to_send.edit(embed=embed)
                print(f"Log: Rules message updated (ID: {self.rules_message_id}).")
                logging_cog = self.bot.get_cog("LoggingCog")
                if logging_cog and logging_cog.log_channel:
                    await logging_cog.log_channel.send(
                        f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                        f"Rules message updated in channel **{rules_channel.name}**."
                    )
            else: 
                message_to_send = await rules_channel.send(embed=embed)
                self.rules_message_id = message_to_send.id
                print(f"Log: New rules message sent (ID: {self.rules_message_id}).")
                logging_cog = self.bot.get_cog("LoggingCog")
                if logging_cog and logging_cog.log_channel:
                    await logging_cog.log_channel.send(
                        f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                        f"New rules message created in channel **{rules_channel.name}**."
                    )
            
            self.last_rules_hash = current_rules_hash
            self._save_config()

        except discord.Forbidden:
            print(f"Log: ERROR: No permissions to send/edit messages in channel {rules_channel.name}. Check 'Send Messages' and 'Embed Links' permissions.")
        except Exception as e:
            print(f"Log: ERROR sending/updating rules message: {e}")


    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Cog "{self.qualified_name}" for Rules loaded and ready.')
        
        rules_channel = self.bot.get_channel(RULES_CHANNEL_ID)
        if not rules_channel:
            print(f"Log: ADVERTENCIA: Rules channel with ID {RULES_CHANNEL_ID} not found or not accessible. Verify ID and permissions.")
            return

        await self._send_or_update_rules_message(rules_channel)


async def setup(bot):
    await bot.add_cog(RulesCog(bot))