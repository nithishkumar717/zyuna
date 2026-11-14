

import sys
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
# os.system("")
import asyncio
import traceback
from threading import Thread
from datetime import datetime
import random
import time

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

# Ensure the repository root is in sys.path regardless of the launch directory.
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir and os.path.exists(_script_dir):
    try:
        os.chdir(_script_dir)
    except Exception:
        pass
_parent_dir = os.path.dirname(_script_dir)
for _p in [
    _script_dir,
    _parent_dir,
    os.getcwd(),
]:
    if _p and os.path.exists(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

_GIT_REPOSITORY_URL = "https://github.com/nithishkumar717/zyuna.git"
_GIT_BRANCH = "main"
_PROJECT_MODULE_ROOTS = {"core", "cogs", "utils", "git_update"}


def _bootstrap_git(*args, cwd):
    """Run a quiet, non-interactive Git command for missing-module recovery."""
    env = os.environ.copy()
    env.update({"GIT_TERMINAL_PROMPT": "0", "GIT_PAGER": "cat"})
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        timeout=120,
        env=env,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or f"git {' '.join(args)} failed"
        raise RuntimeError(detail)
    return result.stdout.strip()


def _find_checkout_root():
    script_dir = Path(_script_dir).resolve()
    for candidate in (script_dir, *script_dir.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def _is_runtime_data_path(relative_path):
    path = Path(relative_path)
    protected_directories = {".git", ".venv", "venv", "db", "data", "logs", "__pycache__"}
    if any(part in protected_directories for part in path.parts):
        return True
    if path.as_posix() == ".env":
        return True
    return path.suffix.lower() in {".db", ".sqlite", ".sqlite3", ".log"}


def _recover_missing_project_module(module_name):
    """Restore missing internal Python files from this checkout or public GitHub."""
    top_level = (module_name or "").split(".", 1)[0]
    if top_level not in _PROJECT_MODULE_ROOTS:
        return []

    project_root = Path(_script_dir).resolve()
    checkout_root = _find_checkout_root()
    restored = []

    if checkout_root is not None:
        try:
            tracked_paths = _bootstrap_git("ls-tree", "-r", "--name-only", "HEAD", cwd=checkout_root).splitlines()
            if top_level == "git_update":
                candidate_paths = [path for path in tracked_paths if path == "git_update.py"]
            else:
                prefix = f"{top_level}/"
                candidate_paths = [
                    path for path in tracked_paths
                    if path.startswith(prefix) and path.endswith(".py")
                ]

            missing_paths = [
                path for path in candidate_paths
                if not (checkout_root / Path(path)).is_file()
            ]
            if not missing_paths:
                return []

            _bootstrap_git(
                "restore", "--source=HEAD", "--staged", "--worktree", "--", *missing_paths,
                cwd=checkout_root,
            )
            return [str(checkout_root / Path(path)) for path in missing_paths]
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
            print(f"\033[33m◈ Git recovery could not restore '{module_name}': {error}\033[0m")
            return []

    try:
        with tempfile.TemporaryDirectory(prefix="zyuna-git-recovery-") as temporary_dir:
            clone_root = Path(temporary_dir) / "checkout"
            _bootstrap_git(
                "clone", "--quiet", "--depth", "1", "--branch", _GIT_BRANCH,
                _GIT_REPOSITORY_URL, str(clone_root),
                cwd=temporary_dir,
            )
            candidate_paths = _bootstrap_git(
                "ls-tree", "-r", "--name-only", "HEAD", cwd=clone_root
            ).splitlines()
            for relative_path in candidate_paths:
                if _is_runtime_data_path(relative_path):
                    continue
                source = clone_root / Path(relative_path)
                destination = project_root / Path(relative_path)
                if not source.is_file():
                    continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                restored.append(str(destination))
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"\033[33m◈ Git recovery could not restore '{module_name}': {error}\033[0m")
    return restored


def _restart_after_module_recovery(module_name):
    attempts = int(os.environ.get("ZYUNA_IMPORT_RECOVERY_ATTEMPTS", "0"))
    if attempts >= 3:
        print(f"✖ [Startup] Recovery limit reached; '{module_name}' is still missing.")
        return

    restored = _recover_missing_project_module(module_name)
    if not restored:
        return

    print(f"\033[32m◈ [Startup] Restored {len(restored)} missing project file(s) from Git.\033[0m")
    print("\033[33m◈ [Startup] Restarting Zyuna to load the recovered code...\033[0m")
    os.environ["ZYUNA_IMPORT_RECOVERY_ATTEMPTS"] = str(attempts + 1)
    os.execv(sys.executable, [sys.executable, os.path.abspath(sys.argv[0]), *sys.argv[1:]])

def _auto_git_pull():
    """Safely fast-forward this checkout at startup, then restart if code changed."""
    try:
        from git_update import sync_repository

        result = sync_repository()
        if not result.success:
            print(f"\033[33m◈ Auto-Update skipped: {result.message}\033[0m")
        elif result.updated:
            print(f"\033[32m◈ Auto-Update: {result.message}\033[0m")
            print("\033[33m◈ Restarting to load the updated code...\033[0m")
            os.execv(sys.executable, [sys.executable, os.path.abspath(sys.argv[0]), *sys.argv[1:]])
        else:
            print(f"\033[36m◈ Auto-Update: {result.message}\033[0m")
    except ModuleNotFoundError as e:
        if e.name:
            _restart_after_module_recovery(e.name)
        print(f"\033[33m◈ Auto-Update note: {e}\033[0m")
    except Exception as e:
        print(f"\033[33m◈ Auto-Update note: {e}\033[0m")

_auto_git_pull()

# Initialize global IST timezone logging for console prints & standard library logging.
try:
    from utils.time_utils import setup_ist_logging, now_ist, format_ist_full, format_ist_datetime
    setup_ist_logging()
except ModuleNotFoundError as error:
    if error.name:
        _restart_after_module_recovery(error.name)
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
    _dep_qr = os.path.join(_base, "cogs", "commands", "qr.py")
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

# (Auto-update moved to top of file)

try:
    from core import Context, zyuna
    from core.Cog import Cog
    from utils.Tools import *
    from utils.config import *
    from utils.emoji import SUCCESS, ERROR, TICK, CROSS, REACTION_TEST_EMOJIS
    from utils.sync_emojis import run_sync

    import jishaku
    import cogs
except ModuleNotFoundError as error:
    if error.name:
        _restart_after_module_recovery(error.name)
    raise

os.environ.pop("ZYUNA_IMPORT_RECOVERY_ATTEMPTS", None)


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


# --- Main Bot Execution ---
async def main():
    async with client:
        os.system("cls" if os.name == "nt" else "clear")
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
