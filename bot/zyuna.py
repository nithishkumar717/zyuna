

import sys
import os
import subprocess
# os.system("")
import asyncio
import traceback
from threading import Thread
from datetime import datetime
import random
import time

# Ensure current working dir, script dir, parent dir, and subfolders are in sys.path
_script_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_script_dir)
for _p in [
    _script_dir,
    _parent_dir,
    os.getcwd(),
    os.path.join(_script_dir, "bot"),
    os.path.join(os.getcwd(), "bot"),
    os.path.join(_parent_dir, "bot"),
]:
    if _p and os.path.exists(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

# Initialize global IST timezone logging for console prints & standard library logging
try:
    from bot.utils.time_utils import setup_ist_logging, now_ist, format_ist_full, format_ist_datetime
    setup_ist_logging()
except (ImportError, ModuleNotFoundError):
    try:
        from utils.time_utils import setup_ist_logging, now_ist, format_ist_full, format_ist_datetime
        setup_ist_logging()
    except Exception:
        pass

# If core is not yet found, check for zip archives to auto-extract or search subdirectories
if not any(os.path.isdir(os.path.join(p, "core")) for p in sys.path if isinstance(p, str) and os.path.isdir(p)):
    import zipfile
    for _f in os.listdir(os.getcwd()):
        if _f.endswith(".zip") and not _f.startswith("."):
            try:
                print(f"◈ [Startup] Found archive '{_f}', auto-extracting...")
                with zipfile.ZipFile(_f, "r") as _z:
                    _z.extractall(os.getcwd())
                print(f"✔ [Startup] Successfully extracted '{_f}'!")
                break
            except Exception as _e:
                print(f"✖ [Startup] Could not extract '{_f}': {_e}")

    # Re-scan paths
    for _root, _dirs, _ in os.walk(os.getcwd()):
        if "core" in _dirs and os.path.isfile(os.path.join(_root, "core", "__init__.py")):
            if _root not in sys.path:
                sys.path.insert(0, _root)
            break

if not any(os.path.isdir(os.path.join(p, "core")) for p in sys.path if isinstance(p, str) and os.path.isdir(p)):
    print(f"✖ [Error] Could not locate 'core' directory!")
    print(f"   Working Directory: {os.getcwd()}")
    print(f"   Files in directory: {os.listdir(os.getcwd())[:20]}")

# Cleanup any deprecated or leftover command files (e.g. legacy qr.py)
for _base in [_script_dir, _parent_dir, os.getcwd()]:
    for _sub in ["cogs/commands", "bot/cogs/commands"]:
        _dep_qr = os.path.join(_base, _sub, "qr.py")
        if os.path.isfile(_dep_qr):
            try:
                os.remove(_dep_qr)
                print(f"\033[33m◈ Cleanup: Removed deprecated file {_dep_qr}\033[0m")
            except Exception:
                pass

import aiohttp
import discord
from discord import Spotify
from discord.ext import commands, tasks

def _find_git_dir():
    check_paths = [
        os.getcwd(),
        os.path.dirname(os.path.abspath(__file__)),
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ]
    for path in check_paths:
        if os.path.exists(os.path.join(path, ".git")):
            return path
    return None

def _auto_git_pull():
    """Automatically pulls the latest code from GitHub on startup."""
    try:
        git_dir = _find_git_dir()
        if git_dir:
            result = subprocess.run(
                ["git", "pull", "origin", "main"],
                cwd=git_dir,
                capture_output=True,
                text=True,
                timeout=20
            )
            out = result.stdout.strip()
            if result.returncode == 0:
                if "Already up to date" in out or "Already up-to-date" in out:
                    print("\033[36m◈ Auto-Update: Code is up to date.\033[0m")
                else:
                    print(f"\033[32m◈ Auto-Update: Pulled latest changes from GitHub:\n{out}\033[0m")
            else:
                err = result.stderr.strip()
                print(f"\033[33m◈ Auto-Update note: Git pull exited with code {result.returncode}: {err or out}\033[0m")
        else:
            print("\033[33m◈ Auto-Update note: No .git directory found, skipping startup pull.\033[0m")
    except Exception as e:
        print(f"\033[33m◈ Auto-Update note: {e}\033[0m")

_auto_git_pull()

try:
    from bot.core import Context, zyuna
    from bot.core.Cog import Cog
    from bot.utils.Tools import *
    from bot.utils.config import *
    from bot.utils.emoji import SUCCESS, ERROR, TICK, CROSS, REACTION_TEST_EMOJIS
    from bot.utils.sync_emojis import run_sync
except (ImportError, ModuleNotFoundError):
    try:
        from core import Context, zyuna
    except ImportError:
        from core import Context, zyrox
        zyuna = zyrox
    from core.Cog import Cog
    from utils.Tools import *
    from utils.config import *
    from utils.emoji import SUCCESS, ERROR, TICK, CROSS, REACTION_TEST_EMOJIS
    from utils.sync_emojis import run_sync

import jishaku
try:
    import bot.cogs as cogs
except (ImportError, ModuleNotFoundError):
    import cogs

# Alias modules in sys.modules so all imports like 'from core import ...' or 'from bot.core import ...'
# resolve to the exact same module instances without NumPy namespace collisions or circular dependency issues.
for _mod_name in list(sys.modules.keys()):
    if _mod_name.startswith("bot.core"):
        _alias = _mod_name.replace("bot.core", "core", 1)
        if _alias not in sys.modules:
            sys.modules[_alias] = sys.modules[_mod_name]
    elif _mod_name.startswith("bot.utils"):
        _alias = _mod_name.replace("bot.utils", "utils", 1)
        if _alias not in sys.modules:
            sys.modules[_alias] = sys.modules[_mod_name]
    elif _mod_name.startswith("core.") or _mod_name == "core":
        _alias = f"bot.{_mod_name}"
        if _alias not in sys.modules:
            sys.modules[_alias] = sys.modules[_mod_name]
    elif _mod_name.startswith("utils.") or _mod_name == "utils":
        _alias = f"bot.{_mod_name}"
        if _alias not in sys.modules:
            sys.modules[_alias] = sys.modules[_mod_name]


os.environ["JISHAKU_NO_DM_TRACEBACK"] = "False"
os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_FORCE_PAGINATOR"] = "True"

from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("TOKEN")

# --- Configuration ---
# IMPORTANT: Replace these with your actual channel IDs.
SERVER_COUNT_CHANNEL_ID = 1419729255977189467  # Replace with your server count channel ID
USER_COUNT_CHANNEL_ID = 1419729283861184632    # Replace with your user count channel ID
LOG_CHANNEL_ID = 1396794297386532978 # Replace with the channel ID for join/leave logs


client = zyuna()
tree = client.tree

# --- Background Task for Stats ---
async def update_stats():
    """A background task to update server and user stats in channel names."""
    await client.wait_until_ready()
    while not client.is_closed():
        try:
            servers = len(client.guilds)
            users = sum(guild.member_count for guild in client.guilds if guild.member_count is not None)
            
            server_channel = client.get_channel(SERVER_COUNT_CHANNEL_ID)
            user_channel = client.get_channel(USER_COUNT_CHANNEL_ID)
            
            if server_channel:
                await server_channel.edit(name=f"Servers: {servers}")
            
            if user_channel:
                await user_channel.edit(name=f"Users: {users}")
                
        except Exception as e:
            print(f"Error updating stats: {e}")
        
        await asyncio.sleep(600) # Update every 10 minutes

async def auto_git_update_task():
    """A background task to periodically check and pull git updates every 10 minutes."""
    await client.wait_until_ready()
    # Wait 5 minutes after boot before first check
    await asyncio.sleep(300)
    while not client.is_closed():
        try:
            git_dir = _find_git_dir()
            if git_dir:
                proc = await asyncio.create_subprocess_exec(
                    "git", "pull", "origin", "main",
                    cwd=git_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                out = stdout.decode().strip()
                err = stderr.decode().strip()

                if proc.returncode == 0:
                    if "Already up to date" not in out and "Already up-to-date" not in out and len(out) > 0:
                        print(f"\033[32m◈ Auto-Update: Pulled new updates from GitHub:\n{out}\033[0m")
                        print(f"\033[33m◈ Auto-Update: Restarting {BRAND_NAME} to apply updates...\033[0m")
                        log_channel = client.get_channel(LOG_CHANNEL_ID)
                        if log_channel:
                            try:
                                embed = discord.Embed(
                                    title="◈ Auto Git Update",
                                    description=f"Pulled new updates from GitHub repository:\n```\n{out[:1500]}\n```\nRestarting {BRAND_NAME} to apply changes...",
                                    color=0x2ecc71
                                )
                                embed.timestamp = discord.utils.utcnow()
                                await log_channel.send(embed=embed)
                            except Exception:
                                pass
                        await asyncio.sleep(2)
                        restart_program()
                else:
                    if err:
                        print(f"\033[33m◈ Auto-Update background check notice: {err}\033[0m")
        except Exception as e:
            print(f"◈ Auto-Update background check error: {e}")

        await asyncio.sleep(600) # Check every 10 minutes

# --- Event Handlers ---
@client.event
async def on_ready():
    await client.wait_until_ready()
    
    print("""
        \033[1;31m
███████╗██╗   ██╗██╗   ██╗███╗   ██╗ █████╗ 
╚══███╔╝╚██╗ ██╔╝██║   ██║████╗  ██║██╔══██╗
  ███╔╝  ╚████╔╝ ██║   ██║██╔██╗ ██║███████║
 ███╔╝    ╚██╔╝  ██║   ██║██║╚██╗██║██╔══██║
███████╗   ██║   ╚██████╔╝██║ ╚████║██║  ██║
╚══════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝
        \033[0m
       """)
    print("Loaded & Online!")
    print(f"Logged in as: {client.user}")
    print(f"Connected to: {len(client.guilds)} guilds")
    print(f"Connected to: {len(client.users)} users")

    # Sync application emojis on startup
    await run_sync(TOKEN)

    async def sync_commands():
        try:
            synced = await client.tree.sync()
            all_commands = list(client.commands)
            print(f"Synced Total {len(all_commands)} Client Commands and {len(synced)} Slash Commands")
        except Exception as e:
            print(f"Error syncing command tree: {e}")

    client.loop.create_task(sync_commands())
    client.loop.create_task(update_stats())
    client.loop.create_task(auto_git_update_task())


@client.event
async def on_guild_join(guild: discord.Guild):
    # Log when the bot joins a server
    log_channel = client.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        ist_now = format_ist_full() if "format_ist_full" in globals() else datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        await log_channel.send(f"[{ist_now}] **{BRAND_NAME}** has been added to the server: **{guild.name}** (ID: `{guild.id}`)")

@client.event
async def on_command_completion(context: commands.Context) -> None:
    if context.author.id in OWNER_IDS:
        return

    full_command_name = context.command.qualified_name
    split = full_command_name.split("\n")
    executed_command = str(split[0])
    webhook_url = CMD_WEBHOOK_URL
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(webhook_url, session=session)

        embed_color = 0xFF0000
        embed = discord.Embed(color=embed_color)
        avatar_url = context.author.display_avatar.url

        embed.set_author(name=f"Cmd Executed: {executed_command}", icon_url=avatar_url)
        embed.set_thumbnail(url=avatar_url)

        if context.guild is not None:
            embed.add_field(name="User", value=f"{context.author.mention} (`{context.author.id}`)", inline=False)
            embed.add_field(name="Server", value=f"{context.guild.name} (`{context.guild.id}`)", inline=False)
            embed.add_field(name="Channel", value=f"{context.channel.mention} (`{context.channel.id}`)", inline=False)
        else:
            embed.add_field(name="User (DM)", value=f"{context.author.mention} (`{context.author.id}`)", inline=False)
        
        if "format_ist_full" in globals():
            embed.add_field(name="Date & Time (IST)", value=f"`{format_ist_full()}`", inline=False)
        embed.timestamp = discord.utils.utcnow()
        embed.set_footer(text=f"{BRAND_NAME} Development™ ❤️", icon_url=client.user.display_avatar.url)
        
        try:
            await webhook.send(embed=embed)
        except Exception as e:
            print(f'Command log webhook failed: {e}')


# --- Utility Commands ---
@client.command(name='spotify')
async def spotify(ctx: Context, user: discord.Member = None):
    """Shows what a user is listening to on Spotify."""
    user = user or ctx.author
    spotify_activity = next((activity for activity in user.activities if isinstance(activity, Spotify)), None)

    if not spotify_activity:
        return await ctx.send(f"{user.name} is not listening to Spotify.")
    
    embed = discord.Embed(
        title=f"{user.name}'s Spotify",
        description=f"**Listening to:** {spotify_activity.title}",
        color=0x1DB954 # Spotify Green
    )
    embed.set_thumbnail(url=spotify_activity.album_cover_url)
    embed.add_field(name="Artist", value=spotify_activity.artist)
    embed.add_field(name="Album", value=spotify_activity.album)
    embed.set_footer(text=f"Song started at {spotify_activity.created_at.strftime('%H:%M')}")
    await ctx.send(embed=embed)


@client.command(name='makeinvite', aliases=['createinvite', 'makeinv'])
@commands.is_owner()
async def make_invite(ctx: Context, guild_id: int = None):
    """Creates an invite for a specified server (owner only)."""
    if guild_id is None:
        return await ctx.send("Please provide a Guild ID.")
        
    guild = client.get_guild(guild_id)
    if not guild:
        return await ctx.send("Invalid Guild ID. I am not in that server.")

    if guild.system_channel and guild.system_channel.permissions_for(guild.me).create_instant_invite:
        try:
            invite = await guild.system_channel.create_invite(max_age=0, max_uses=0, unique=True, reason="Owner requested invite.")
            return await ctx.send(f"Invite for **{guild.name}**:\n{invite.url}")
        except Exception:
            pass

    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).create_instant_invite:
            try:
                invite = await channel.create_invite(max_age=0, max_uses=0, unique=True, reason="Owner requested invite.")
                return await ctx.send(f"Invite for **{guild.name}** (from #{channel.name}):\n{invite.url}")
            except Exception:
                continue
                
    await ctx.send(f"I don't have 'Create Instant Invite' permission in any channel in **{guild.name}**.")


# --- Webhook Management Commands ---
@client.command(name='create_hook', aliases=['makehook'])
@commands.has_permissions(administrator=True)
async def create_hook(ctx: Context, *, name: str = None):
    """Creates a webhook in the current channel."""
    if name is None:
        return await ctx.send("Please provide a name for the webhook.")
    
    try:
        webhook = await ctx.channel.create_webhook(name=name, reason=f"Created by {ctx.author}")
        embed = discord.Embed(
            title=f"{SUCCESS} Webhook Created",
            description=f"A webhook named **{webhook.name}** was created.",
            color=0xFF0000
        )
        await ctx.author.send(f"Webhook URL for **{webhook.name}** in **{ctx.channel.name}**:\n||{webhook.url}||", embed=embed)
        await ctx.send("Webhook created. I've sent the URL to your DMs.")
    except discord.Forbidden:
        await ctx.send("I don't have permission to create webhooks here.")
    except Exception:
        await ctx.send(f"Webhook created: **{webhook.name}**\n||{webhook.url}||\n(I could not DM you the URL.)")


@client.command(name='delete_hook', aliases=['delhook'])
@commands.has_permissions(administrator=True)
async def delete_hook(ctx: Context, webhook_url: str = None):
    """Deletes a webhook using its URL."""
    if webhook_url is None:
        return await ctx.send("Please provide the webhook URL to delete.")

    try:
        async with aiohttp.ClientSession() as session:
            webhook = await discord.Webhook.from_url(webhook_url, session=session)
            await webhook.delete(reason=f"Deleted by {ctx.author}")
        await ctx.send(f"{SUCCESS} Webhook deleted successfully.")
    except (discord.NotFound, ValueError):
        await ctx.send(f"{ERROR} Webhook not found or URL is invalid.")


@client.command(name='list_hooks', aliases=['hooks'])
@commands.has_permissions(administrator=True)
async def list_hooks(ctx: Context):
    """Lists all webhooks in the current channel."""
    try:
        webhooks = await ctx.channel.webhooks()
        if not webhooks:
            return await ctx.send("No webhooks found in this channel.")

        embed = discord.Embed(title=f"Webhooks in #{ctx.channel.name}", color=0xFF0000)
        description = "\n".join([f"**Name:** {wh.name} | **ID:** `{wh.id}`" for wh in webhooks])
        embed.description = description
        await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send("I don't have permission to view webhooks in this channel.")


# --- Game Command ---
@client.command()
async def reaction(ctx: Context):
    """See how fast you can react to the correct emoji."""
    emojis = ["🍪", "🎉", "🧋", "🍒", "🍑", "💸", "🌙", "💕"]
    correct_emoji = random.choice(emojis)
    random.shuffle(emojis)
    
    embed = discord.Embed(
        title="Reaction Test",
        description="I will show an emoji in a few seconds. Get ready to click it!",
        color=0xFF0000
    )
    message = await ctx.send(embed=embed)
    
    for emoji in emojis:
        await message.add_reaction(emoji)
        
    await asyncio.sleep(random.uniform(2.0, 7.0))
    
    embed.description = f"**GET THE {correct_emoji} EMOJI!**"
    await message.edit(embed=embed)
    start_time = time.time()

    def check(reaction, user):
        return (
            reaction.message.id == message.id
            and str(reaction.emoji) == correct_emoji
            and user == ctx.author
        )

    try:
        reaction, user = await client.wait_for("reaction_add", timeout=15.0, check=check)
        end_time = time.time()
        reaction_time = end_time - start_time
        
        embed.description = f"{user.mention} got the {correct_emoji} in **{reaction_time:.2f} seconds**!"
        await message.edit(embed=embed)
    except asyncio.TimeoutError:
        embed.description = "Timeout! You were too slow."
        await message.edit(embed=embed)


# ---API Server for Dashboard Backend ---
import uvicorn
from threading import Thread
try:
    from bot.api.server import create_app
    from bot.api.dependencies import set_bot
except (ImportError, ModuleNotFoundError):
    from api.server import create_app
    from api.dependencies import set_bot

fastapi_app = create_app()
fastapi_app.state.bot = client
set_bot(client)

API_ENABLED = os.getenv("API_ENABLED", "true").strip().lower() == "true"
API_PORT = int(os.getenv("API_PORT", "8000"))

def run_api():
    uvicorn.run(fastapi_app, host='0.0.0.0', port=API_PORT, log_level="warning")

def keep_alive():
    if not API_ENABLED:
        print(f"\033[33m◈ API Server: Disabled via API_ENABLED=false\033[0m")
        return
    print(f"\033[32m◈ API Server: Starting on port {API_PORT}\033[0m")
    server = Thread(target=run_api, daemon=True)
    server.start()

keep_alive()

# --- Cloudflare Tunnel (HTTPS for API) ---
try:
    from bot.utils.tunnel import start_tunnel
except (ImportError, ModuleNotFoundError):
    from utils.tunnel import start_tunnel
start_tunnel()

# --- Main Bot Execution ---
async def main():
    async with client:
        os.system("clear")
        await client.load_extension("jishaku")
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                await client.start(TOKEN)
                break
            except discord.HTTPException as e:
                if e.status == 429: # Rate limited
                    wait_time = min((2 ** attempt) + random.random(), 60)
                    print(f"Rate limited. Retrying in {wait_time:.2f} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    raise
        else:
            raise Exception("Bot failed to start after multiple retries due to rate limiting.")

if __name__ == "__main__":
    asyncio.run(main())
