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

if not MONGO_URI:
    print("❌ ERROR: MONGO_URI missing!")
    client = styles_col = None
else:
    try:
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client["ScribeBot"]
        styles_col = db["role_styles"]
        client.admin.command('ping') 
        print("✅ Successfully connected to MongoDB Atlas")
    except Exception as e:
        print(f"❌ MongoDB Connection Error: {e}")
        client = None

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
bot = commands.Bot(command_prefix="!", intents=intents, activity=discord.Game(name="Made by GhostMode"))

async def sync_member_nick(member):
    base_name = member.global_name or member.name
    cursor = styles_col.find()
    saved_roles = {doc["role_name"]: doc for doc in cursor}
    
    for role in reversed(member.roles):
        if role.name in saved_roles:
            data = saved_roles[role.name]
            font_func = FONT_MAP.get(data.get("font", "none"), FONT_MAP["none"])
            prefix = data.get("prefix", "")
            suffix = data.get("suffix", "") # NEW: Suffix support
            
            final_nick = f"{prefix}{font_func(base_name)}{suffix}"[:32]
            
            if member.nick != final_nick:
                try:
                    await member.edit(nick=final_nick)
                except discord.Forbidden: pass
            return 

    if member.nick:
        try: await member.edit(nick=None)
        except: pass

def make_progress_bar(current, total):
    size = 10
    filled = int((current / total) * size)
    bar = "🟩" * filled + "⬜" * (size - filled)
    return f"[{bar}] {int((current/total)*100)}% ({current}/{total})"

# --- 5. COMMANDS ---

@bot.tree.command(name="preview", description="Show a visual gallery of all available fonts")
async def preview(interaction: discord.Interaction):
    embed = discord.Embed(title="🖋️ Scribe Font Preview", color=discord.Color.blue())
    example_text = "Scribe Bot"
    
    description = ""
    for name, func in FONT_MAP.items():
        description += f"**{name}**: {func(example_text)}\n"
    
    embed.description = description
    embed.set_footer(text="Use /setrole to apply these to roles!")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="setrole", description="Assign font, prefix, and suffix to a role")
async def setrole(interaction: discord.Interaction, role_name: str, font: str, prefix: str = "", suffix: str = ""):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Admin only!", ephemeral=True)
    
    if font.lower() not in FONT_MAP:
        return await interaction.response.send_message(f"❌ Invalid font! Use /preview to see list.", ephemeral=True)

    styles_col.replace_one(
        {"role_name": role_name}, 
        {"role_name": role_name, "font": font.lower(), "prefix": prefix, "suffix": suffix}, 
        upsert=True
    )
    await interaction.response.send_message(f"✅ Saved **{role_name}** style: `{prefix}` + `{font}` + `{suffix}`")

@bot.tree.command(name="createrole", description="Create a role with perms and color")
async def createrole(interaction: discord.Interaction, name: str, level: str, hex_color: str = "#99aab5"):
    if not interaction.user.guild_permissions.administrator: return
    perms = discord.Permissions.none()
    if level.lower() == "member": perms.update(view_channel=True, send_messages=True, read_message_history=True)
    elif level.lower() == "moderator": perms.update(manage_messages=True, kick_members=True, ban_members=True)
    elif level.lower() == "admin": perms.administrator = True
    
    color = discord.Color(int(hex_color.replace("#", ""), 16))
    role = await interaction.guild.create_role(name=name, permissions=perms, color=color)
    await interaction.response.send_message(f"✅ Created {role.mention}")

@bot.tree.command(name="listroles", description="See all cloud configurations in a clean embed")
async def listroles(interaction: discord.Interaction):
    # Fetch all styles from MongoDB
    all_styles = list(styles_col.find())
    
    if not all_styles: 
        return await interaction.response.send_message("❌ No roles are currently configured in the database.")
    
    embed = discord.Embed(
        title="📜 Current Cloud Role Configurations",
        description="All roles currently managed by Scribe and stored in MongoDB Atlas.",
        color=discord.Color.blue() # You can change this to any color (e.g., Color.gold())
    )

    for d in all_styles:
        role_name = d.get('role_name', 'Unknown')
        font = d.get('font', 'none')
        prefix = d.get('prefix', 'None')
        suffix = d.get('suffix', 'None')

        # Formatting values for the embed field
        value_text = f"**Font:** {font}\n**Prefix:** {prefix}\n**Suffix:** {suffix}"
        
        # We use inline=True so they sit side-by-side if the screen is wide enough
        embed.add_field(name=f"✨ {role_name}", value=value_text, inline=True)

    embed.set_footer(text=f"Total Configured Roles: {len(all_styles)}")
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
    
    await interaction.response.send_message(embed=embed)
@bot.tree.command(name="syncall", description="Sync everyone")
async def syncall(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator: return
    await interaction.response.defer()
    members = [m for m in interaction.guild.members if not m.bot]
    msg = await interaction.followup.send(f"🔄 **Syncing...**")
    for i, m in enumerate(members, 1):
        await sync_member_nick(m)
        if i % 5 == 0 or i == len(members): 
            await msg.edit(content=f"🔄 **Syncing...**\n{make_progress_bar(i, len(members))}")
        await asyncio.sleep(1.2)
    await msg.edit(content="✅ **Sync Complete!**")

# --- 6. EVENTS ---

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Scribe is ready.")

@bot.event
async def on_member_join(member):
    # FEATURE (2): Auto-Sync when a new person joins
    print(f"New member joined: {member.name}. Waiting for roles...")
    # We wait a few seconds because some bots/systems add roles immediately after join
    await asyncio.sleep(5)
    await sync_member_nick(member)

@bot.event
async def on_member_update(before, after):
    if before.roles != after.roles: 
        await sync_member_nick(after)

# --- 7. RUN ---
if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get('DISCORD_TOKEN'))
