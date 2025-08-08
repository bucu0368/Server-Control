
import discord
from discord.ext import commands, tasks
from pydactyl import PterodactylClient
import datetime

# Bot setup
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Owner ID
OWNER_ID = 1142053791781355561

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

# Owner check
def is_owner(interaction: discord.Interaction) -> bool:
    return interaction.user.id == OWNER_ID

# Server group command
@bot.tree.command(name="server", description="Server control commands")
@discord.app_commands.describe(
    action="Action to perform",
    server_name="Server to control"
)
@discord.app_commands.choices(action=[
    discord.app_commands.Choice(name="control", value="control"),
    discord.app_commands.Choice(name="start", value="start"),
    discord.app_commands.Choice(name="stop", value="stop"),
    discord.app_commands.Choice(name="restart", value="restart"),
    discord.app_commands.Choice(name="status", value="status")
])
@discord.app_commands.choices(server_name=[
    discord.app_commands.Choice(name=name, value=name) for name in SERVERS.keys()
])
async def server_command(interaction: discord.Interaction, action: str, server_name: str = None):
    # Owner check
    if not is_owner(interaction):
        await interaction.response.send_message("❌ Only the bot owner can use this command.", ephemeral=True)
        return
    
    global selected_server, embed_message
    
    if action == "control":
        # Show control panel
        selected_server = server_name or selected_server
        
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
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
    elif action == "start":
        if not server_name:
            await interaction.response.send_message("❌ Please specify a server name.", ephemeral=True)
            return
        try:
            api.client.servers.send_power_action(SERVERS[server_name], 'start')
            await interaction.response.send_message(f"✅ {server_name} started successfully.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to start {server_name}. Error: {e}", ephemeral=True)
            
    elif action == "stop":
        if not server_name:
            await interaction.response.send_message("❌ Please specify a server name.", ephemeral=True)
            return
        try:
            api.client.servers.send_power_action(SERVERS[server_name], 'stop')
            await interaction.response.send_message(f"🛑 {server_name} stopped successfully.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to stop {server_name}. Error: {e}", ephemeral=True)
            
    elif action == "restart":
        if not server_name:
            await interaction.response.send_message("❌ Please specify a server name.", ephemeral=True)
            return
        try:
            api.client.servers.send_power_action(SERVERS[server_name], 'restart')
            await interaction.response.send_message(f"🔄 {server_name} restarted successfully.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to restart {server_name}. Error: {e}", ephemeral=True)
            
    elif action == "status":
        if not server_name:
            await interaction.response.send_message("❌ Please specify a server name.", ephemeral=True)
            return
        try:
            server = api.client.servers.get_server_utilization(SERVERS[server_name])
            state = server['current_state']
            status = "🟢 Online" if state == "running" else "🔴 Offline"
            await interaction.response.send_message(f"📡 {server_name} Status: {status}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to get status for {server_name}. Error: {e}", ephemeral=True)


# Server Control View (updated for slash commands)
class ServerControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ServerDropdown())

    @discord.ui.button(label="Start", style=discord.ButtonStyle.green, custom_id="start_button")
    async def start_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_owner(interaction):
            await interaction.response.send_message("❌ Only the bot owner can use this button.", ephemeral=True)
            return
            
        await interaction.response.defer()
        try:
            api.client.servers.send_power_action(SERVERS[selected_server], 'start')
            await interaction.followup.send(f"✅ {selected_server} started successfully.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to start {selected_server}. Error: {e}", ephemeral=True)

    @discord.ui.button(label="Restart", style=discord.ButtonStyle.gray, custom_id="restart_button")
    async def restart_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_owner(interaction):
            await interaction.response.send_message("❌ Only the bot owner can use this button.", ephemeral=True)
            return
            
        await interaction.response.defer()
        try:
            api.client.servers.send_power_action(SERVERS[selected_server], 'restart')
            await interaction.followup.send(f"🔄 {selected_server} restarted successfully.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to restart {selected_server}. Error: {e}", ephemeral=True)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.red, custom_id="stop_button")
    async def stop_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_owner(interaction):
            await interaction.response.send_message("❌ Only the bot owner can use this button.", ephemeral=True)
            return
            
        await interaction.response.defer()
        try:
            api.client.servers.send_power_action(SERVERS[selected_server], 'stop')
            await interaction.followup.send(f"🛑 {selected_server} stopped successfully.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to stop {selected_server}. Error: {e}", ephemeral=True)


# Server Selection Dropdown
class ServerDropdown(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=name, value=name) for name in SERVERS.keys()]
        super().__init__(placeholder="Choose a bot", options=options)

    async def callback(self, interaction: discord.Interaction):
        if not is_owner(interaction):
            await interaction.response.send_message("❌ Only the bot owner can use this dropdown.", ephemeral=True)
            return
            
        global selected_server
        selected_server = self.values[0]
        await interaction.response.defer()
        await update_embed()


async def update_embed(first_time=False):
    global embed_message
    
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

    if first_time and embed_message:
        await embed_message.edit(embed=embed, view=view)


@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user.name}')
    
    # Set presence
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="xSeif"))
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    # Start the status check loop
    check_server_status.start()


# Check Server Status Every 30 Seconds
@tasks.loop(seconds=30)
async def check_server_status():
    await update_embed()


bot.run("you bot here")
