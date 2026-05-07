import discord
from discord.ext import commands
import random
import string
import json
import os
from datetime import datetime, timedelta

TOKEN = "YOUR_BOT_TOKEN"
ADMIN_IDS = [123456789]  # Your Discord User IDs

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

KEYS_FILE = "keys.json"

def load_keys():
    if not os.path.exists(KEYS_FILE):
        return {}
    with open(KEYS_FILE, "r") as f:
        return json.load(f)

def save_keys(keys):
    with open(KEYS_FILE, "w") as f:
        json.dump(keys, f, indent=2)

def gen_key():
    parts = [''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) for _ in range(4)]
    return "RAMIN-" + "-".join(parts)

def is_admin():
    async def predicate(ctx):
        return ctx.author.id in ADMIN_IDS
    return commands.check(predicate)

@bot.command()
@is_admin()
async def genkey(ctx, days: int = 30, username: str = "User", tier: str = "Premium"):
    keys = load_keys()
    key = gen_key()
    expires = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    keys[key] = {"username": username, "expires": expires, "tier": tier, "banned": False}
    save_keys(keys)
    await ctx.send(f"✅ Key generated:\n```{key}```\nUser: `{username}` | Tier: `{tier}` | Expires: `{expires}`")

@bot.command()
@is_admin()
async def bankey(ctx, key: str):
    keys = load_keys()
    if key not in keys:
        await ctx.send("❌ Key not found.")
        return
    keys[key]["banned"] = True
    save_keys(keys)
    await ctx.send(f"🔨 Key `{key}` has been banned.")

@bot.command()
@is_admin()
async def unbankey(ctx, key: str):
    keys = load_keys()
    if key not in keys:
        await ctx.send("❌ Key not found.")
        return
    keys[key]["banned"] = False
    save_keys(keys)
    await ctx.send(f"✅ Key `{key}` has been unbanned.")

@bot.command()
@is_admin()
async def addtime(ctx, key: str, days: int):
    keys = load_keys()
    if key not in keys:
        await ctx.send("❌ Key not found.")
        return
    current = datetime.strptime(keys[key]["expires"], "%Y-%m-%d")
    keys[key]["expires"] = (current + timedelta(days=days)).strftime("%Y-%m-%d")
    save_keys(keys)
    await ctx.send(f"✅ Added `{days}` days to `{key}`. New expiry: `{keys[key]['expires']}`")

@bot.command()
@is_admin()
async def removetime(ctx, key: str, days: int):
    keys = load_keys()
    if key not in keys:
        await ctx.send("❌ Key not found.")
        return
    current = datetime.strptime(keys[key]["expires"], "%Y-%m-%d")
    keys[key]["expires"] = (current - timedelta(days=days)).strftime("%Y-%m-%d")
    save_keys(keys)
    await ctx.send(f"✅ Removed `{days}` days from `{key}`. New expiry: `{keys[key]['expires']}`")

@bot.command()
@is_admin()
async def sendkey(ctx, member: discord.Member, days: int = 30, tier: str = "Premium"):
    keys = load_keys()
    key = gen_key()
    expires = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    keys[key] = {"username": member.name, "expires": expires, "tier": tier, "banned": False}
    save_keys(keys)
    try:
        await member.send(f"🔑 **Your Ramin Tweaks License Key:**\n```{key}```\nTier: `{tier}` | Expires: `{expires}`")
        await ctx.send(f"✅ Key sent to {member.mention} via DM.")
    except:
        await ctx.send(f"❌ Could not DM {member.mention}. Key: `{key}`")

@bot.command()
@is_admin()
async def checkkey(ctx, key: str):
    keys = load_keys()
    if key not in keys:
        await ctx.send("❌ Key not found.")
        return
    d = keys[key]
    status = "🔨 BANNED" if d["banned"] else "✅ Active"
    await ctx.send(f"**Key:** `{key}`\n**User:** `{d['username']}`\n**Tier:** `{d['tier']}`\n**Expires:** `{d['expires']}`\n**Status:** {status}")

@bot.command()
@is_admin()
async def listkeys(ctx):
    keys = load_keys()
    if not keys:
        await ctx.send("No keys found.")
        return
    msg = "**All Keys:**\n"
    for k, v in keys.items():
        status = "🔨" if v["banned"] else "✅"
        msg += f"{status} `{k}` — `{v['username']}` | `{v['tier']}` | `{v['expires']}`\n"
    await ctx.send(msg[:2000])

bot.run(TOKEN)
