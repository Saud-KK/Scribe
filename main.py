import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import os
import asyncio
import pymongo
from discord import app_commands

# --- 1. WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Scribe is Online!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- 2. MONGODB SETUP ---
MONGO_URI = os.environ.get('MONGO_URI')
client = pymongo.MongoClient(MONGO_URI)
db = client["ScribeBot"]
styles_col = db["role_styles"]

# --- 3. FONT TRANSFORMERS ---
FONT_MAP = {
    "asian": lambda t: t.translate(str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz", "卂乃匚ᗪ乇千Ꮆ卄丨ﾌҜㄥ爪几ㄖ卩Ɋ尺丂ㄒㄩᐯ山乂ㄚ乙卂乃匚ᗪ乇千Ꮆ卄丨ﾌҜㄥ爪几ㄖ卩Ɋ尺丂ㄒㄩᐯ山乂ㄚ乙")),
    "mixed": lambda t: t.translate(str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz", "ΔβĆĐ€₣ǤĦƗĴҜŁΜŇØƤΩŘŞŦỮVŴЖ¥ŽΔβĆĐ€₣ǤĦƗĴҜŁΜŇØƤΩŘŞŦỮVŴЖ¥Ž")),
    "medieval": lambda t: t.translate(str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz", "𝕬𝕭𝕮𝕯𝕰𝕱𝕲𝕳𝕴𝕵𝕶𝕷𝕸𝕹𝕺𝕻𝕼𝕽𝕾𝕿𝖀𝖁𝖂𝖃𝖄𝖅𝖆𝖇𝖈𝖉𝖊𝖋𝖌𝖍𝖎𝖏𝖐𝖑𝖒𝖓𝖔𝖕𝖖𝖗𝖘𝖙𝖚𝖛𝖜𝖝𝖞𝖟")),
    "antique": lambda t: t.translate(str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz", "𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓦𝓧𝓨𝓩𝓪𝓫𝓬𝓭𝓮𝓯𝓰𝓱𝓲𝓳𝓴𝓵𝓶𝓷𝓸𝓹𝓺𝓻𝓼𝓽𝓾𝓿𝔀𝔁𝔂𝔃")),
    "monospace": lambda t: t.translate(str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789", "𝙰𝙱𝙲𝙳𝙴𝙵𝙶𝙷𝙸𝙹𝙺𝙻𝙼𝙽𝙾𝙿𝚀𝚁𝚂𝚃𝚄𝚅𝚆𝚇𝚈𝚉𝚊𝚋𝚌𝚍𝚎𝚏𝚐𝚑𝚒𝚓𝚔𝚕𝚖𝚗𝚘𝚙𝚚𝚛𝚜𝚝𝚞𝚟𝚠𝚡𝚢𝚣𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿")),
    "circled": lambda t: t.translate(str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789", "ⒶⒷⒸⒹⒺⒻⒼⒽⒾⒿⓀⓁⓂⓃⓄⓅⓆⓇⓈⓉⓊⓋⓌⓍⓎⓏⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩ⓪①②③④⑤⑥⑦⑧⑨")),
    "none": lambda t: t
}

# --- 4. BOT SETUP ---
intents = discord.Intents.default()
intents.members = True 
bot = commands.Bot(command_prefix="!", intents=intents)

async def sync_member_nick(member):
    base_name = member.global_name or member.name
    
    # Optimization: Cache DB results to avoid over-querying MongoDB
    cursor = styles_col.find()
    saved_roles = {doc["role_name"]: doc for doc in cursor}
    
    # Check roles from highest position to lowest
    for role in reversed(member.roles):
        if role.name in saved_roles:
            data = saved_roles[role.name]
            font_key = data.get("font", "none")
            font_func = FONT_MAP.get(font_key, FONT_MAP["none"])
            prefix = data.get("prefix", "")
            
            final_nick = f"{prefix}{font_func(base_name)}"[:32]
            
            if member.nick != final_nick:
                try:
                    await member.edit(nick=final_nick)
                except discord.Forbidden:
                    print(f"Permission denied for {member.name}")
                except Exception as e:
                    print(f"Error: {e}")
            return 

    # No styled roles found, remove nickname if one exists
    if member.nick:
        try:
            await member.edit(nick=None)
        except:
            pass

def make_progress_bar(current, total):
    size = 10
    filled = int((current / total) * size)
    bar = "🟩" * filled + "⬜" * (size - filled)
    return f"[{bar}] {int((current/total)*100)}% ({current}/{total})"

# --- 5. COMMANDS ---

@bot.tree.command(name="createrole", description="Create a role with perms and color")
@app_commands.describe(level="member, moderator, admin")
async def createrole(interaction: discord.Interaction, name: str, level: str, hex_color: str = "#99aab5"):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Admin only!", ephemeral=True)
    
    perms = discord.Permissions.none()
    if level.lower() == "member": perms.update(view_channel=True, send_messages=True, read_message_history=True)
    elif level.lower() == "moderator": perms.update(manage_messages=True, kick_members=True, ban_members=True)
    elif level.lower() == "admin": perms.administrator = True
    
    try:
        color = discord.Color(int(hex_color.replace("#", ""), 16))
        role = await interaction.guild.create_role(name=name, permissions=perms, color=color)
        await interaction.response.send_message(f"✅ Created role {role.mention} with **{level}** perms.")
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

@bot.tree.command(name="setrole", description="Assign font/prefix to a role (Saves to MongoDB)")
async def setrole(interaction: discord.Interaction, role_name: str, font: str, prefix: str = ""):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Admin only!", ephemeral=True)
    
    if font.lower() not in FONT_MAP:
        return await interaction.response.send_message(f"❌ Invalid font! Choices: {', '.join(FONT_MAP.keys())}", ephemeral=True)

    # Upsert (Update if exists, Insert if not)
    styles_col.replace_one(
        {"role_name": role_name}, 
        {"role_name": role_name, "font": font.lower(), "prefix": prefix}, 
        upsert=True
    )
    await interaction.response.send_message(f"✅ Style for **{role_name}** saved to Cloud Database!")

@bot.tree.command(name="syncall", description="Sync all nicknames publicly")
async def syncall(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator: return
    await interaction.response.defer()
    
    members = [m for m in interaction.guild.members if not m.bot]
    total = len(members)
    msg = await interaction.followup.send(f"🔄 **Syncing...**\n{make_progress_bar(0, total)}")
    
    for i, m in enumerate(members, 1):
        await sync_member_nick(m)
        if i %
