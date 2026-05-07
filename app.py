import os
import json
import random
import string
import threading
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import discord
from discord.ext import commands

app = Flask(__name__)
KEYS_FILE = 'keys.json'
ADMIN_IDS = [int(x) for x in os.environ.get('ADMIN_IDS', '').split(',') if x]
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')

# ── Keys Helpers ─────────────────────────────────────────────
def load_keys():
    if not os.path.exists(KEYS_FILE):
        return {}
    with open(KEYS_FILE, 'r') as f:
        return json.load(f)

def save_keys(keys):
    with open(KEYS_FILE, 'w') as f:
        json.dump(keys, f, indent=2)

def gen_key():
    chars = string.ascii_uppercase + string.digits
    parts = [''.join(random.choices(chars, k=4)) for _ in range(3)]
    return 'RAMIN-' + '-'.join(parts)

def add_days(date_str, days):
    d = datetime.strptime(date_str, '%Y-%m-%d') + timedelta(days=days)
    return d.strftime('%Y-%m-%d')

# ── Flask API ─────────────────────────────────────────────────
@app.route('/verify')
def verify():
    key = request.args.get('key', '')
    keys = load_keys()
    data = keys.get(key)
    if not data:
        return jsonify({'valid': False, 'reason': 'Invalid key.'})
    if data['banned']:
        return jsonify({'valid': False, 'reason': 'Key is banned.'})
    if datetime.strptime(data['expires'], '%Y-%m-%d') <= datetime.now():
        return jsonify({'valid': False, 'reason': 'Key expired.'})
    return jsonify({'valid': True, 'username': data['username'], 'expires': data['expires'], 'tier': data['tier']})

# ── Discord Bot ───────────────────────────────────────────────
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

def is_admin():
    async def predicate(ctx):
        return ctx.author.id in ADMIN_IDS
    return commands.check(predicate)

@bot.event
async def on_ready():
    print(f'Bot logged in as {bot.user}')

@bot.command()
@is_admin()
async def genkey(ctx, days: int = 30, username: str = 'User', tier: str = 'Premium'):
    keys = load_keys()
    key = gen_key()
    expires = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
    keys[key] = {'username': username, 'expires': expires, 'tier': tier, 'banned': False}
    save_keys(keys)
    await ctx.reply(f'✅ Key generated:\n```{key}```User: `{username}` | Tier: `{tier}` | Expires: `{expires}`')

@bot.command()
@is_admin()
async def sendkey(ctx, member: discord.Member, days: int = 30, tier: str = 'Premium'):
    keys = load_keys()
    key = gen_key()
    expires = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
    keys[key] = {'username': member.name, 'expires': expires, 'tier': tier, 'banned': False}
    save_keys(keys)
    try:
        await member.send(f'🔑 **Your Ramin Tweaks License Key:**\n```{key}```Tier: `{tier}` | Expires: `{expires}`')
        await ctx.reply(f'✅ Key sent to {member.mention} via DM.')
    except Exception:
        await ctx.reply(f'❌ Could not DM {member.mention}. Key: `{key}`')

@bot.command()
@is_admin()
async def bankey(ctx, key: str):
    keys = load_keys()
    if key not in keys:
        return await ctx.reply('❌ Key not found.')
    keys[key]['banned'] = True
    save_keys(keys)
    await ctx.reply(f'🔨 Key `{key}` banned.')

@bot.command()
@is_admin()
async def unbankey(ctx, key: str):
    keys = load_keys()
    if key not in keys:
        return await ctx.reply('❌ Key not found.')
    keys[key]['banned'] = False
    save_keys(keys)
    await ctx.reply(f'✅ Key `{key}` unbanned.')

@bot.command()
@is_admin()
async def addtime(ctx, key: str, days: int):
    keys = load_keys()
    if key not in keys:
        return await ctx.reply('❌ Key not found.')
    keys[key]['expires'] = add_days(keys[key]['expires'], days)
    save_keys(keys)
    await ctx.reply(f'✅ Added `{days}` days. New expiry: `{keys[key]["expires"]}`')

@bot.command()
@is_admin()
async def removetime(ctx, key: str, days: int):
    keys = load_keys()
    if key not in keys:
        return await ctx.reply('❌ Key not found.')
    keys[key]['expires'] = add_days(keys[key]['expires'], -days)
    save_keys(keys)
    await ctx.reply(f'✅ Removed `{days}` days. New expiry: `{keys[key]["expires"]}`')

@bot.command()
@is_admin()
async def checkkey(ctx, key: str):
    keys = load_keys()
    if key not in keys:
        return await ctx.reply('❌ Key not found.')
    d = keys[key]
    status = '🔨 BANNED' if d['banned'] else '✅ Active'
    expired = ' ⚠️ EXPIRED' if datetime.strptime(d['expires'], '%Y-%m-%d') <= datetime.now() else ''
    await ctx.reply(f'**Key:** `{key}`\n**User:** `{d["username"]}`\n**Tier:** `{d["tier"]}`\n**Expires:** `{d["expires"]}`{expired}\n**Status:** {status}')

@bot.command()
@is_admin()
async def listkeys(ctx):
    keys = load_keys()
    if not keys:
        return await ctx.reply('No keys found.')
    out = '**All Keys:**\n'
    for k, v in keys.items():
        expired = '⌛' if datetime.strptime(v['expires'], '%Y-%m-%d') <= datetime.now() else ''
        out += f'{"🔨" if v["banned"] else "✅"}{expired} `{k}` — `{v["username"]}` | `{v["tier"]}` | `{v["expires"]}`\n'
    await ctx.reply(out[:2000])

@bot.command()
@is_admin()
async def deletekey(ctx, key: str):
    keys = load_keys()
    if key not in keys:
        return await ctx.reply('❌ Key not found.')
    del keys[key]
    save_keys(keys)
    await ctx.reply(f'🗑️ Key `{key}` deleted.')

@bot.command()
@is_admin()
async def help_cmd(ctx):
    await ctx.reply('\n'.join([
        '**Ramin Tweaks Bot Commands:**',
        '`!genkey [days] [username] [tier]` — Generate key',
        '`!sendkey @user [days] [tier]` — Generate & DM key',
        '`!bankey <key>` — Ban key',
        '`!unbankey <key>` — Unban key',
        '`!addtime <key> <days>` — Add days',
        '`!removetime <key> <days>` — Remove days',
        '`!checkkey <key>` — Check key info',
        '`!listkeys` — List all keys',
        '`!deletekey <key>` — Delete key',
    ]))

# ── Start both ────────────────────────────────────────────────
def run_flask():
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)

def run_bot():
    bot.run(BOT_TOKEN)

if __name__ == '__main__':
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    run_bot()
