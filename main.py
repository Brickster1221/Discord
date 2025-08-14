import discord
from discord.ext import commands
from datetime import datetime, timezone, timedelta
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

with open('secret.json') as f:
    secret = json.load(f)

bot.data = {}
def load_data():
    if os.path.exists('data.json'):
        try:
            with open('data.json', "r") as file:
                bot.data = json.load(file)
        except json.JSONDecodeError:
            bot.data = {}

def save_data():
    with open('data.json', "w") as file:
        json.dump(bot.data, file, indent=4)
bot.save = save_data
load_data()

async def log_message(message, guild=1034558177510961182):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{timestamp} {message}")
    channel = bot.get_channel(int(bot.data["guild_specific"][str(guild)]["log_channel"]))
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
    text = message.content.lower()
    if "job" in text:
        await message.channel.send("DONT SAY THAT WORD", reference=message)
        await message.author.timeout(timedelta(seconds=3), reason="said the j slur")
        await log_message(f"{message.author} said the j slur :sob:")

async def constant_loop():
    while True:
        load_data()
        IDS = []
        for ID in bot.data["user_channels"]:
            channel_id = int(bot.data["user_channels"][ID]['ChannelID'])
            channel = bot.get_channel(channel_id)
            user = await bot.fetch_user(ID)
            if channel and len(channel.members) == 0 and channel.guild and time.time() > int(bot.data["user_channels"][ID]['TimeDel']):
                IDS.append(ID)
                await channel.delete()
                await log_message(f"personal vc belonging `{user}` has been deleted to due timer running out")
            if not channel:
                IDS.append(ID)
                await log_message(f"personal vc belonging to `{user}` has been deleted to due it no longer existing")
        if len(IDS) > 0:
            for ID in IDS:
                del bot.data["user_channels"][ID]
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
    if str(member.guild.id) not in bot.data["guild_specific"]:
        return log_message("please put your guild id in guild_specific.json")
    if "welcome_channel" not in bot.data["guild_specific"][str(member.guild.id)]:
        return log_message("please put a `welcome_channel` id in your guild settings")
    channel = member.guild.get_channel(int(bot.data["guild_specific"][str(member.guild.id)]["welcome_channel"]))
    if not channel:
        return

    messages = [f"{member.mention} has joined the server!!", f"Welcome {member.mention} to the server!!",
                f"{member.mention} arrived!!", f"{member.mention} just showed up!!", f"Yay you made it {member.mention}!!",
                f"{member.mention} joined the party!!"]
    message = random.choice(messages)
    await channel.send(f"-> ({str(member.guild.member_count)}) {message}\n-# ({member.name})")

    role = discord.utils.get(member.guild.roles, name="hi")
    await member.add_roles(role)

@bot.event
async def on_member_remove(member):
    if str(member.guild.id) not in bot.data["guild_specific"]:
        return await log_message("please put your guild id in guild_specific.json")
    if "welcome_channel" not in bot.data["guild_specific"][str(member.guild.id)]:
        return await log_message("please put a `welcome_channel` id in your guild settings")
    channel = member.guild.get_channel(int(bot.data["guild_specific"][str(member.guild.id)]["welcome_channel"]))
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
    if  duration:
        message = f"{message}, they were here for {duration}"

    await channel.send(f"<- ({str(member.guild.member_count)}) {message}\n-# ({member.name})")

#sends a message in vc when someone joins/leaves
@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel == after.channel:
        return
    if before.channel:
        await before.channel.send(f"<t:{round(time.time())}:T> {member} left")
    if after.channel:
        await after.channel.send(f"<t:{round(time.time())}:T> {member} joined")

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

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await help(ctx)
    else:
        raise error

@bot.command(name='help', aliases=[''])
async def help(ctx, args=""):
    if args == "moderation":
        embed = discord.Embed(title="List of moderation commands", color=0x0c8eeb)
        embed.add_field(name=f"{ctx.prefix}ban", value="bans a member from the server, using something like 1d/1h/1m will set them to be unbanned in that time", inline=True)
        embed.add_field(name=f"{ctx.prefix}unban", value="unbans a member", inline=True)
        embed.add_field(name=f"{ctx.prefix}mute", value="mutes a member by making them only be able to access one channel", inline=True)
        embed.add_field(name=f"{ctx.prefix}kick", value="kicks a member from the server", inline=True)
        embed.add_field(name=f"{ctx.prefix}warn", value="warns a member, useful for seeing what they have done in the past", inline=True)
        await ctx.send(embed=embed)
    elif args == "infinivc":
        embed = discord.Embed(title="List of infinivc commands", description="These can only be used in infinivc channels", color=0x0c8eeb)
        embed.add_field(name=f"{ctx.prefix}infinivc timer", value="typing the argument, 1d/1h/1m will set the vc to delete at the time you choose", inline=True)
        embed.add_field(name=f"{ctx.prefix}infinivc info", value="This will display info about the current vc you are tpying the command in", inline=True)
        embed.add_field(name=f"{ctx.prefix}infinivc delete", value="This will delete the channel if you are the owner of it", inline=True)
        await ctx.send(embed=embed)
    else:
        embed=discord.Embed(title="List of commands", color=0x0c8eeb)
        embed.add_field(name=f"{ctx.prefix}help", value="displays a list of helpful commands", inline=True)
        embed.add_field(name=f"{ctx.prefix}repeat", value="makes the bot repeat what you type, use `-del` to automatically delete your message after", inline=True)
        embed.add_field(name="infinivc commands", value=f"use `{ctx.prefix}help infinivc` for more information", inline=True)
        embed.add_field(name="moderation commands", value=f"use `{ctx.prefix}help moderation` for more information", inline=True)
        await ctx.send(embed=embed)

@bot.command()
async def test(ctx):
    await ctx.channel.send(f"<- ({str(ctx.guild.member_count)}) {ctx}\n-# ({ctx.author})")

token = secret["token"]
bot.run(token)
