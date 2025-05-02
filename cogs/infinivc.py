import discord
from discord.ext import commands
import time
import json
import os
import re

class infinivc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_channels = self.load_json("user_channels.json")
        self.guild_specific = self.load_json("guild_specific.json")

    # INFINITE VC CHANNELS
    def load_json(self, filename):
        if os.path.exists(filename):
            try:
                with open(filename, "r") as file:
                    return json.load(file)
            except json.JSONDecodeError:
                return {}
        return {}

    def save_data(self):
        with open('user_channels.json', "w") as file:
            json.dump(self.user_channels, file, indent=4)

    def get_data(self, value, key='ChannelID'):
        value = str(value)
        return next((user for user, details in self.user_channels.items() if details.get(key) == value), None)

    async def update_data(self, user_id, value, type='ChannelID'):
        user_id = str(user_id)
        value = str(value)

        if user_id not in self.user_channels:
            self.user_channels[user_id] = {}
        self.user_channels[user_id][type] = value

        if type == "TimeDel" and self.user_channels[user_id]['MessageID']:
            channel = self.bot.get_channel(int(self.user_channels[user_id]['ChannelID']))
            try:
                message = await channel.fetch_message(self.user_channels[user_id]['MessageID'])
                user = await self.bot.fetch_user(user_id)
                await message.edit(content=f"Voice channel created by: `{user}`\nChannel will be deleted in <t:{value}:R>")
            except:
                pass

        self.save_data()


    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        guild = str(member.guild.id)
        # Check if a member joined the specific VC
        if after.channel and guild in self.guild_specific:
            if after.channel.id == int(self.guild_specific[guild]["infinivc_channel"]):
                category = member.guild.get_channel(int(self.guild_specific[guild]["infinivc_category"]))
                existing = self.user_channels.get(str(member.id))
                if existing:
                    await member.move_to(existing)
                    return
                #else:
                    #self.user_channels[str(member.id)]['ChannelID'] = ""

                # Create a temporary voice channel
                overwrites = {
                    member.guild.default_role:
                    discord.PermissionOverwrite(connect=True),
                    member:
                    discord.PermissionOverwrite(view_channel=True,connect=True,manage_channels=True,mute_members=True,deafen_members=True,move_members=True,manage_permissions=True)
                }
                temp_channel = await member.guild.create_voice_channel(
                    name=f"{member.name}'s Channel",
                    category=category,
                    overwrites=overwrites
                )

                await self.bot.log(f"`{member}` has created a voice channel")
                message = await temp_channel.send(f"Voice Channel created by: `{member}`")
                await self.update_data(member.id, temp_channel.id, 'ChannelID')
                await self.update_data(member.id, message.id, 'MessageID')
                await self.update_data(member.id,round(time.time()) + 36 * 60 * 60, 'TimeDel')
                await member.move_to(temp_channel)

        for state_channel in [after.channel, before.channel]:
            if state_channel:
                user_id = self.get_data(state_channel.id)
                if user_id in self.user_channels:
                    if self.user_channels[user_id]['TimeDel'] < round(time.time()) + 36 * 60 * 60:
                        await self.update_data(user_id, round(time.time()) + 36 * 60 * 60, 'TimeDel')

    def parse_time(self, time_str):
        match = re.match(r"(\d+)([dhm])", time_str.lower())
        if not match:
            return None

        amount, unit = match.groups()
        amount = int(amount)

        if unit == "d":
            return amount * 86400
        elif unit == "h":
            return amount * 3600
        elif unit == "m":
            return amount * 60
        else:
            return None

    @commands.command()
    async def infinivc(self, ctx, *, args):
        user_id = self.get_data(ctx.channel.id, "ChannelID")
        if not user_id:
            await ctx.send(embed=discord.Embed(description="❌ You are not in a valid VC", color=0xcc182a))
            return

        split = args.split(" ", 1)  # Split into time and reason
        arg = split[0]
        if arg == "timer":
            timmy = split[1]
            duration = self.parse_time(timmy) if timmy else None
            if duration > 30 * 24 * 60 * 60:
                duration = 30 * 24 * 60 * 60 #sets max time to 30 days
            if not duration:
                timmy = None

            if duration:
                await self.update_data(user_id, round(time.time()) + duration, 'TimeDel')
            else:
                ctx.send(embed=discord.Embed(description="❌ Please input a vaild time value", color=0xcc182a))

    @infinivc.error
    async def error(self, ctx, error):
        await self.bot.log(f"Unexpected errer during infinivc command, `{error}`")
        await ctx.send(embed=discord.Embed(description="❌ an unexpected error occured", color=0xcc182a))
        


async def setup(bot):
    await bot.add_cog(infinivc(bot))