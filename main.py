#import spam
import discord
from discord.ext import commands
from datetime import datetime, timezone, timedelta
import asyncio
import time
import json
import os
import random

#default bot setup
intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="?", intents=intents, help_command=None)

with open('secret.json') as f:
    secret = json.load(f)

#save and load data
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

#logging
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
    await check_members()
    bot.loop.create_task(constant_loop()) #loop for unbans and vc timers

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    text = message.content.lower()
    if bot.data["guild_specific"][str(message.guild.id)]['censor_job'] == True and "job" in text:
        await message.channel.send("DONT SAY THAT WORD", reference=message)
        try:
           await message.author.timeout(timedelta(seconds=3), reason="said the j slur") 
        except:
            pass
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
        for guildid in bot.data['mod_actions']:
            for case in bot.data['mod_actions'][guildid]:
                if case["action"] == "ban" and "duration" in case:
                    if round(time.time()) > (int(case['duration']) + round(time.time())):
                        try:
                            guild = bot.get_guild(int(guildid))
                            await guild.unban(discord.Object(id=int(case["user_id"])))
                            await log_message(f"Succesfully unbanned <@{case['user_id']}>, Case `{case}`")
                        except Exception as e:
                            await log_message(f"Couldnt unban `{case['user_id']}`: `{e}`")
        """
        
        await asyncio.sleep(300)
"""
Ultra cool comment to show that everything till the next comment is to do with the 
join_leave_messages variable in guild_specific omg wow
"""
async def packData(numb):
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    if numb == 0:
        return 0
    s = []
    while numb > 0:
        s.append(chars[numb % 64])
        n //= 64
    return ''.join(reversed(s))

@bot.command()
async def test(ctx):
    await ctx.send(packData(21938128939534))

async def joinmessage(member, guild, join, duration=None):
    if bot.data["guild_specific"][str(guild.id)]["join_leave_messages"] == False:
        return
    if "welcome_channel" not in bot.data["guild_specific"][str(guild.id)]:
        return log_message("please put a `welcome_channel` id in your guild settings")
    channel = bot.get_channel(int(bot.data["guild_specific"][str(guild.id)]["welcome_channel"]))
    if not channel:
        return
    

    messages = [f"{member.mention} has joined the server!!",
                f"Welcome {member.mention} to the server!!",
                f"{member.mention} arrived!!", f"{member.mention} just showed up!!",
                f"Yay you made it {member.mention}!!",
                f"{member.mention} joined the party!!"
            ] if join else [
                f"{member.mention} has left the server >:C",
                f"{member.mention} has left us behind :C",
                f"{member.mention} moved on :("
            ]
    if join:
        message = f"-> ({guild.member_count}) {random.choice(messages)}\n-# ({member.name})"
    elif duration:
        message = f"<- ({guild.member_count}) {random.choice(messages)}, they were here for {duration}\n-# ({member.name})"
    else:
        message = f"<- ({guild.member_count}) {random.choice(messages)}\n-# ({member.name})"

    await channel.send(f"{message}")

async def check_members():
    if not "members" in bot.data:
        bot.data["members"] = {}
        save_data()

    for guildid in bot.data["members"]:
        if bot.data["guild_specific"][guildid]["join_leave_messages"] == False:
            return

        data = bot.data["members"][guildid]
        newlist = data.copy()
        guild = bot.get_guild(int(guildid))

        for member in guild.members:
            if str(member.id) in newlist:
                newlist.remove(str(member.id))
            else:
                await joinmessage(member, guild, True)
                data.append(str(member.id))
        
        if len(newlist) >= 0:
            for memberid in newlist:
                member = await bot.fetch_user(int(memberid))
                await joinmessage(member, guild, False)
                data.remove(memberid)
    save_data()

@bot.event
async def on_member_join(member):
    await joinmessage(member, member.guild, True)
    bot.data["members"][str(member.guild.id)].append(str(member.id))
    save_data()
    role = discord.utils.get(member.guild.roles, name="hi")
    await member.add_roles(role)

@bot.event
async def on_member_remove(member):
    duration = None
    if member.joined_at:
        now = datetime.now(timezone.utc)
        time_in_server = now - member.joined_at
        days = time_in_server.days
        seconds = time_in_server.seconds
        hours, remainder = divmod(seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        duration = f"{days} days, {hours} hours, and {minutes} minutes"
    
    await joinmessage(member, member.guild, False, duration)
    bot.data["members"][str(member.guild.id)].remove(str(member.id))
    save_data()

"""
omg ultra cool comment to end the join/leave channel message things wowie
"""

@bot.event
async def on_voice_state_update(member, before, after):
    if bot.data["guild_specific"][str(member.guild.id)]["vc_log"] == False:
        return
    if before.channel == after.channel:
        return
    if before.channel:
        await before.channel.send(f"<t:{round(time.time())}:T> {member} left")
    if after.channel:
        await after.channel.send(f"<t:{round(time.time())}:T> {member} joined")

#cool repeat command
@bot.command(name='repeat', aliases=['rep'])
async def repeat(ctx, *, text: str):
    if bot.data["guild_specific"][str(ctx.guild.id)]["repeat_command"] == False:
        return
    if "@everyone" in text or "@here" in text or "@&" in text:
        await log_message(f"yeah, `{ctx.author}` really tried that")
        await ctx.send(f"You really tried that didnt you, {ctx.author}")
        return
    if '-del' in text:
        await ctx.message.delete()
        text = text.replace('-del', '').strip()
    
    if ctx.message.reference and ctx.message.reference.resolved:
        replied_message = ctx.message.reference.resolved
        await ctx.send(text, reference=replied_message)
    else:
        await ctx.send(text)
    
    await log_message(f"`{ctx.author}` made the bot say: `{text}`")

#bet you cant guess what this is
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
        embed.add_field(name=f"{ctx.prefix}infinivc timeout", value="This will set the default deletion time for when somebody joins/leaves this vc", inline=True)
        embed.add_field(name=f"{ctx.prefix}infinivc info", value="This will display info about the current vc you are tpying the command in", inline=True)
        embed.add_field(name=f"{ctx.prefix}infinivc delete", value="This will delete the channel if you are the owner of it", inline=True)
        await ctx.send(embed=embed)
    else:
        embed=discord.Embed(title="List of commands", color=0x0c8eeb)
        embed.add_field(name=f"{ctx.prefix}help", value="displays a list of helpful commands", inline=True)
        embed.add_field(name=f"{ctx.prefix}repeat", value="makes the bot repeat what you type, use `-del` to automatically delete your message after", inline=True)
        embed.add_field(name=f"{ctx.prefix}theforbiddencommand", value="gives/removes your perms for <#1382937610774777966>")
        embed.add_field(name="infinivc commands", value=f"use `{ctx.prefix}help infinivc` for more information", inline=True)
        embed.add_field(name="moderation commands", value=f"use `{ctx.prefix}help moderation` for more information", inline=True)
        await ctx.send(embed=embed)

@bot.command()
async def theforbiddencommand(ctx):
    channel = ctx.guild.get_channel(1382937610774777966)
    if channel:
        if channel.permissions_for(ctx.author).view_channel:
            try:
                await channel.set_permissions(ctx.author, view_channel=False)
                await ctx.send("ok you dont have perms anymore")
            except:
                await ctx.send("Error")
        else:
            try:
                await channel.set_permissions(ctx.author, view_channel=True)
                await ctx.send("you have perms ig")
            except:
                await ctx.send("Error")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await help(ctx)
    else:
        raise error
    

token = secret["token"]
bot.run(token)
