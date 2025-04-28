import discord
from discord.ext import commands
import time
import json
import os

class infinivc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # INFINITE VC CHANNELS
    global user_channels
    if os.path.exists('user_channels.json'):
        try:
            with open('user_channels.json', "r") as file:
                data = json.load(file)
                user_channels = data.get("actions", {})
        except json.JSONDecodeError:
            #await log_message(f"Error: `{DATA_FILE}` is not a valid JSON file or is empty. Starting fresh.")
            user_channels = {}
    else:
        #await log_message(f"Error: `{DATA_FILE}` is not a valid JSON file or is empty. Starting fresh.")
        user_channels = {}

    def save_data(self):
        data = {
            "channels": user_channels
        }
        with open('user_channels.json', "w") as file:
            json.dump(data, file, indent=4)

    def get_data(self, value, whatfind='ChannelID'):
        if not value:
            return
        
        value = str(value)

        # Find the UserID with the given ChannelID
        try:
            user_id = next((user for user, details in user_channels.items() if details[whatfind] == value), None)
        except:
            print("error")

        if user_id:
            return user_id


    async def update_data(self, UserID, value, type='ChannelID'):
        UserID = str(UserID)
        if UserID in user_channels:
            user_channels[UserID][type] = str(value)
        else:
            user_channels[UserID] = {}
            user_channels[UserID][type] = str(value)

        if type == "TimeDel" and user_channels[UserID]['MessageID']:

            channel = self.bot.get_channel(int(user_channels[UserID]['ChannelID']))
            message = await channel.fetch_message(user_channels[UserID]['MessageID'])

            user = await self.bot.fetch_user(UserID)
            await message.edit(content=f"Voice channel created by: `{user}` \nChannel will be deleted in <t:{user_channels[UserID]['TimeDel']}:R> ")

        self.save_data()


    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # Check if a member joined the specific VC
        if after.channel and after.channel.id == 1195402268305014795:
            guild = member.guild
            category = guild.get_channel(1034558178886701138)

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
                overwrites=overwrites
            )

            message = await temp_channel.send(f"Voice Channel created by: `{member}`")
            await self.update_data(member.id, message.id, 'MessageID')
            # Move the member to the newly created channel
            await member.move_to(temp_channel)
            await self.update_data(member.id, temp_channel.id, 'ChannelID')
            await self.bot.log(f"`{member}` has created a voice channel")
            await self.update_data(member.id,round(time.time()) + 48 * 60 * 60, 'TimeDel')

        if after.channel:
            if self.get_data(after.channel.id, 'ChannelID') in user_channels:
                user_id = self.get_data(after.channel.id)
                await self.update_data(user_id,round(time.time()) + 48 * 60 * 60, 'TimeDel')
                #await log_message(f"personal vc: `{after.channel}`'s timer has been reset")

        if before.channel:
            if self.get_data(before.channel.id, 'ChannelID') in user_channels:
                user_id = self.get_data(before.channel.id)
                await self.update_data(user_id,round(time.time()) + 48 * 60 * 60, 'TimeDel')
                #await log_message(f"personal vc: `{before.channel}`'s timer has been reset")


async def setup(bot):
    await bot.add_cog(infinivc(bot))