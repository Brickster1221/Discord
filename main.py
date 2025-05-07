import discord
from discord.ext import commands
from datetime import datetime, timezone
import asyncio
import time
import json
import os
import random

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="?", intents=intents, help_command=None)

async def log_message(message, guild=1034558177510961182):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{timestamp} {message}")
    channel = bot.get_channel(int(guild_specific[str(guild)]["log_channel"]))
    if channel:
        await channel.send(
            f"<t:{round(time.time())}> (<t:{round(time.time())}:R>) {message}")
        
bot.log = log_message

@bot.event
async def on_ready():
    await log_message(f"Logged in as `{bot.user}`")
    await bot.load_extension('cogs.admin')
    await bot.load_extension('cogs.infinivc')
    bot.loop.create_task(constant_loop())

@bot.event
async def on_message(message):
    await bot.process_commands(message)


def load_data():
    global user_channels
    global mod_actions
    global guild_specific
    if os.path.exists('user_channels.json'):
        try:
            with open('user_channels.json', "r") as file:
                user_channels = json.load(file)
        except json.JSONDecodeError:
            user_channels = {}
    else:
        user_channels = {}

    if os.path.exists('mod_actions.json'):
        try:
            with open('mod_actions.json', "r") as file:
                mod_actions = json.load(file)
        except json.JSONDecodeError:
            mod_actions = {}
    else:
        mod_actions = {}

    if os.path.exists('guild_specific.json'):
        try:
            with open('guild_specific.json', "r") as file:
                guild_specific = json.load(file)
        except json.JSONDecodeError:
            guild_specific = {}
    else:
        guild_specific = {}

def save_data():
    with open('user_channels.json', "w") as file:
        json.dump(user_channels, file, indent=4)
load_data()

async def constant_loop():
    while True:
        load_data()
        IDS = []
        for ID in user_channels:
            channel_id = int(user_channels[ID]['ChannelID'])
            channel = bot.get_channel(channel_id)
            user = await bot.fetch_user(ID)
            if channel and len(channel.members) == 0 and channel.guild and time.time() > int(user_channels[ID]['TimeDel']):
                IDS.append(ID)
                await channel.delete()
                #del user_channels[ID]
                #save_data()
                await log_message(f"personal vc belonging `{user}` has been deleted to due timer running out")
            if not channel:
                IDS.append(ID)
                await log_message(f"personal vc belonging to `{user}` has been deleted to due it no longer existing")
        if len(IDS) > 0:
            for ID in IDS:
                del user_channels[ID]
            save_data()
        
        """
        for Case in mod_actions.values():
            if Case['action'] == "ban" and "unban_time" in Case:
                if round(time.time()) > int(Case["unban_time"]) and int(Case["unban_time"]) > 0:
                    try:
                        guild = bot.get_guild(1034558177510961182)
                        await guild.unban(discord.Object(id=int(Case["user_id"])))
                        await log_message(f"Succesfully unbanned `{Case['user_id']}`, Case `{Case}`")
                        Case['unban_time'] = "0"
                    except Exception as e:
                        await log_message(f"Couldn't unban `{Case['user_id']}`: `{e}`")
                        Case['unban_time'] = "0"
        """

        await asyncio.sleep(300)

@bot.event
async def on_member_join(member):
    if member.guild.id not in guild_specific:
        return log_message("please put your guild id in guild_specific.json")
    if "welcome_channel" not in guild_specific[str(member.guild.id)]:
        return log_message("please put a `welcome_channel` id in your guild settings")
    channel = member.guild.get_channel(int(guild_specific[str(member.guild.id)]["welcome_channel"]))
    if not channel:
        return

    messages = [f"{member.mention} has joined the server!!", f"Welcome {member.mention} to the server!!"]
    message = random.choice(messages)
    await channel.send(f"-> ({str(member.guild.member_count)}) {message}")

    role = discord.utils.get(member.guild.roles, name="hi")
    await member.add_roles(role)

@bot.event
async def on_member_remove(member):
    if member.guild.id not in guild_specific:
        return await log_message("please put your guild id in guild_specific.json")
    if "welcome_channel" not in guild_specific[str(member.guild.id)]:
        return await log_message("please put a `welcome_channel` id in your guild settings")
    channel = member.guild.get_channel(int(guild_specific[str(member.guild.id)]["welcome_channel"]))
    if not channel:
        return

    duration = None
    if member.joined_at:
        now = datetime.now(timezone.utc)
        time_in_server = now - member.joined_at
        days = time_in_server.days
        seconds = time_in_server.seconds
        hours, remainder = divmod(seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        duration = f"{days} days, {hours} hours, and {minutes} minutes"
    
    messages = [f"{member.mention} has left the server >:C"]
    message = random.choice(messages)
    if duration:
        message = f"{message}, they were here for {duration}"
    await channel.send(f"<- ({str(member.guild.member_count)}) {message}")


@bot.command()
async def repeat(ctx, *, text: str):
    if "@everyone" in text or "@here" in text or "@&" in text:
        await log_message(f"yeah, `{ctx.author}` really tried that")
        await ctx.send(f"You really tried that didnt you, {ctx.author}")
        return
    if '-del' in text:
        await ctx.message.delete()
        text = text.replace('-del', '').strip()
    
    await log_message(f"`{ctx.author}` made the bot say: `{text}`")
    
    if ctx.message.reference and ctx.message.reference.resolved:
        replied_message = ctx.message.reference.resolved
        await ctx.send(text, reference=replied_message)
    else:
        await ctx.send(text)

@bot.command(name='help', aliases=[''])
async def help(ctx, args=""):
    if args == "moderation":
        embed = discord.Embed(title="List of moderation commands", color=0xcc182a)

        await ctx.send(embed=embed)
    else:
        embed=discord.Embed(title="List of commands", color=0xcc182a)
        embed.add_field(name="?help", value="displays a list of helpful commands", inline=True)
        embed.add_field(name="?repeat", value="makes the bot repeat what you type, use `-del` to automatically delete your message after", inline=True)
        embed.add_field(name="?infinivc", value="use ?help infinivc for more information", inline=True)
        embed.add_field(name="moderation commands", value="use ?help moderation for more information", inline=True)
        await ctx.send(embed=embed)
    await ctx.send("Currently in development")

with open('secret.json') as f:
    secret = json.load(f)

token = secret["token"]
bot.run(token)
