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
bot = commands.Bot(command_prefix="?", intents=intents)


#log_file = "log.txt"
async def log_message(message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{timestamp} {message}")
    #with open(log_file, "a") as file:
    #file.write(f"{timestamp} {message}\n")
    channel = bot.get_channel(1036159229440032768)
    if channel:
        await channel.send(
            f"<t:{round(time.time())}> (<t:{round(time.time())}:R>) {message}")


#def log_shutdown():
#with open(log_file, "a") as file:
#timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
#file.write(f"{timestamp} Bot is shutting down.\n")

# Register shutdown hook
#atexit.register(log_shutdown)


@bot.event
async def on_ready():
    await log_message(f"Logged in as `{bot.user}`")
    print(f"Logged in as {bot.user}")
    bot.loop.create_task(delete_if_empty())


@bot.event
async def on_message(message):
    #log_message(f"Received message: {message.content}")
    await bot.process_commands(message)


# INFINITE VC CHANNELS
TEMP_CHANNEL_ID = 1195402268305014795
CATEGORY_ID = 1034558178886701138

# Path to the JSON file
DATA_FILE = "data.json"


# Load data from the file
def load_data():
    """Load data from the JSON file."""
    global user_channels
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as file:
                data = json.load(file)
                user_channels = data.get("user_channels", {})
                #await log_message(f"Data has been loaded")
        except json.JSONDecodeError:
            #await log_message(f"Error: `{DATA_FILE}` is not a valid JSON file or is empty. Starting fresh.")
            user_channels = {}
    else:
        # File doesn't exist, start fresh
        #await log_message(f"Error: `{DATA_FILE}` is not a valid JSON file or is empty. Starting fresh.")
        user_channels = {}


def save_data():
    """Save data to the JSON file."""
    with open(DATA_FILE, "w") as file:
        json.dump({"user_channels": user_channels}, file, indent=4)


load_data()


def get_data(value, whatfind='ChannelID'):
    value = str(value)

    # Find the UserID with the given ChannelID
    user_id = next((user for user, details in user_channels.items()
                    if details[whatfind] == value), None)

    if user_id:
        return user_id


async def update_data(UserID, value, type='ChannelID'):
    UserID = str(UserID)
    if UserID in user_channels:
        user_channels[UserID][type] = str(value)
    else:
        user_channels[UserID] = {}
        user_channels[UserID][type] = str(value)

    if type == "TimeDel" and user_channels[UserID]['MessageID']:

        channel = bot.get_channel(int(user_channels[UserID]['ChannelID']))
        message = await channel.fetch_message(
            user_channels[UserID]['MessageID'])

        user = await bot.fetch_user(UserID)
        await message.edit(
            content=
            f"Voice channel created by: `{user}` \nChannel will be deleted in <t:{user_channels[UserID]['TimeDel']}:R> "
        )

    save_data()


@bot.event
async def on_voice_state_update(member, before, after):
    # Check if a member joined the specific VC
    if after.channel and after.channel.id == TEMP_CHANNEL_ID:
        guild = member.guild
        category = guild.get_channel(CATEGORY_ID)

        if str(member.id) in user_channels:
            existing_channel_id = int(user_channels[str(
                member.id)]['ChannelID'])
            existing_channel = guild.get_channel(existing_channel_id)
            if existing_channel:
                await member.move_to(existing_channel)
                return

        # Create a temporary voice channel
        overwrites = {
            guild.default_role:
            discord.PermissionOverwrite(connect=True),
            member:
            discord.PermissionOverwrite(view_channel=True,connect=True,manage_channels=True,mute_members=True,deafen_members=True,move_members=True,manage_permissions=True)
        }
        temp_channel = await guild.create_voice_channel(
            name=f"{member.name}'s Channel",
            category=category,
            overwrites=overwrites)

        message = await temp_channel.send(
            f"Voice Channel created by: `{member}`")
        await update_data(member.id, message.id, 'MessageID')
        # Move the member to the newly created channel
        await member.move_to(temp_channel)
        await update_data(member.id, temp_channel.id, 'ChannelID')
        await log_message(f"`{member}` has created a voice channel")
        await update_data(member.id,round(time.time()) + 36 * 60 * 60, 'TimeDel')

    if after.channel:
        if get_data(after.channel.id, 'ChannelID') in user_channels:
            user_id = get_data(after.channel.id)
            await update_data(user_id,round(time.time()) + 36 * 60 * 60, 'TimeDel')
            #await log_message(f"personal vc: `{after.channel}`'s timer has been reset")

    if before.channel:
        if get_data(before.channel.id, 'ChannelID') in user_channels:
            user_id = get_data(before.channel.id)
            await update_data(user_id,round(time.time()) + 36 * 60 * 60, 'TimeDel')
            #await log_message(f"personal vc: `{before.channel}`'s timer has been reset")


async def delete_if_empty():
    while True:
        IDS = []
        for ID in user_channels:
            channel_id = int(user_channels[ID]['ChannelID'])
            channel = bot.get_channel(channel_id)
            user = await bot.fetch_user(ID)
            if channel and len(channel.members
                               ) == 0 and channel.guild and time.time() > int(
                                   user_channels[ID]['TimeDel']):
                IDS.append(ID)
                await channel.delete()
                #del user_channels[ID]
                #save_data()
                await log_message(
                    f"personal vc belonging `{user}` has been deleted to due timer running out"
                )
            if not channel:
                IDS.append(ID)
                await log_message(
                    f"personal vc belonging to `{user}` has been deleted to due it no longer existing"
                )
        if len(IDS) > 0:
            for ID in IDS:
                del user_channels[ID]
                save_data()
        await asyncio.sleep(120)


WelcomeID = 1265540793456787546  #Channel where welcome/leave messages are sent

@bot.event
async def on_member_join(member):
    channel = member.guild.get_channel(WelcomeID)
    messages = [f"{member.mention} has joined the server!!", f"Welcome {member.mention} to the server!!"]
    message = random.choice(messages)
    await channel.send(f"-> {message}")

    role = discord.utils.get(member.guild.roles, name="hi")
    await member.add_roles(role)


@bot.event
async def on_member_remove(member):
    channel = member.guild.get_channel(WelcomeID)
    if channel:
        if member.joined_at:
            now = datetime.now(timezone.utc)
            time_in_server = now - member.joined_at
            days = time_in_server.days
            seconds = time_in_server.seconds
            hours, remainder = divmod(seconds, 3600)
            minutes, _ = divmod(remainder, 60)

            duration = f"{days} days, {hours} hours, and {minutes} minutes"
            await channel.send(    f"<- {member.mention} has left the server >:C, they were here for {duration}.")
        else:
            await channel.send(f"<- {member.mention} has left the server. >:C")


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

# ultra cool admin only commands
@bot.command()
async def kick(ctx):
    await ctx.send("yeah your getting kicked (imma code ts later)")

@bot.command()
async def ban(ctx):
    await ctx.send("yeah your getting banned (imma code ts later)")

@bot.command()
async def mute(ctx):
    await ctx.send("yeah your getting muted (imma code ts later)")

@bot.command()
async def warn(ctx):
    await ctx.send("yeah your getting warned (imma code ts later)")

with open('secret.json') as f:
    secret = json.load(f)

token = secret["token"]
bot.run(token)
