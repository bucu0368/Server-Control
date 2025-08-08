import discord
from discord.ext import commands, tasks
from pydactyl import PterodactylClient
import datetime

# Bot setup
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Pterodactyl API Setup
PANEL_URL = 'https://panel.sillydev.co.uk/'
API_KEY = 'your-api-key'  # Replace with your real API key

# You can change the names to whatever you want
SERVERS = {
    "Main Bot": "249f245f",
    "Mirror Bot": "abcd1234",
    "Backup Bot": "efgh5678",
    "Test Bot": "ijkl9012",
    "Gaming Bot": "mnop3456",
    "Music Bot": "qrst7890"
}

NODE = 'Phoenix' # You can change this too
api = PterodactylClient(url=PANEL_URL, api_key=API_KEY)

# Store selected bot & message ID
selected_server = list(SERVERS.keys())[0]  # Default bot
embed_message = None  # Store embed message reference


# ️ Server Control View
class ServerControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ServerDropdown())

    @discord.ui.button(label="Start", style=discord.ButtonStyle.green, custom_id="start_button")
    async def start_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        try:
            api.client.servers.send_power_action(SERVERS[selected_server], 'start')
            await interaction.followup.send(f"✅ {selected_server} started successfully.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to start {selected_server}. Error: {e}", ephemeral=True)

    @discord.ui.button(label="Restart", style=discord.ButtonStyle.gray, custom_id="restart_button")
    async def restart_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        try:
            api.client.servers.send_power_action(SERVERS[selected_server], 'restart')
            await interaction.followup.send(f"🔄 {selected_server} restarted successfully.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to restart {selected_server}. Error: {e}", ephemeral=True)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.red, custom_id="stop_button")
    async def stop_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        try:
            api.client.servers.send_power_action(SERVERS[selected_server], 'stop')
            await interaction.followup.send(f"🛑 {selected_server} stopped successfully.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to stop {selected_server}. Error: {e}", ephemeral=True)


#  Server Selection Dropdown
class ServerDropdown(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=name, value=name) for name in SERVERS.keys()]
        super().__init__(placeholder="Choose a bot", options=options)

    async def callback(self, interaction: discord.Interaction):
        global selected_server
        selected_server = self.values[0]
        await interaction.response.defer()
        await update_embed()


#  Send Initial Embed
@bot.event
async def on_ready():
    global embed_message
    print(f'✅ Logged in as {bot.user.name}')
    
    # Set presence
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="xSeif"))
    
    channel_id = 1342204108110827530  # Replace with your channel ID
    channel = bot.get_channel(channel_id)

    if not channel:
        print(f"❌ Channel with ID {channel_id} not found.")
        return

    # Check if the embed already exists
    async for message in channel.history(limit=10):
        if message.author == bot.user and message.embeds:
            embed_message = message
            print("🔄 Found existing embed, will update instead of sending a new one.")
            break

    await update_embed(first_time=(embed_message is None))
    check_server_status.start()


# ️ Update Embed (Fixes Multiple Messages)
async def update_embed(first_time=False):
    global selected_server, embed_message
    channel_id = 1342204108110827530  # Replace with your channel ID
    channel = bot.get_channel(channel_id)

    if not channel:
        return

    try:
        server = api.client.servers.get_server_utilization(SERVERS[selected_server])
        state = server['current_state']
        status = "🟢 Online" if state == "running" else "🔴 Offline"
    except Exception as e:
        status = f"⚠️ {e}"

    embed = discord.Embed(title="🔧 Bot Control System", color=discord.Color.blue())
    embed.add_field(name="🔹 Selected Bot:", value=selected_server, inline=False)
    embed.add_field(name="🆔 Server ID:", value=SERVERS[selected_server], inline=False)
    embed.add_field(name="🖥️ Node:", value=NODE, inline=False)
    embed.add_field(name="📡 Server Status:", value=status, inline=False)

    now = discord.utils.utcnow()
    next_ping_time = now + datetime.timedelta(seconds=30 - (now.second % 30))
    remaining_seconds = (next_ping_time - now).seconds
    embed.set_footer(text=f"Next ping in {remaining_seconds} s")

    view = ServerControlView()

    if first_time:
        message = await channel.send(embed=embed, view=view)
        embed_message = message
    else:
        await embed_message.edit(embed=embed, view=view)


# Check Server Status Every 30 Seconds
@tasks.loop(seconds=30)
async def check_server_status():
    await update_embed()


bot.run("your-bot-token")
