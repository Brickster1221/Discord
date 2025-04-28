import discord
from discord.ext import commands
import time
import json
import os
import re

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    global mod_actions
    if os.path.exists('mod_actions.json'):
        try:
            with open('mod_actions.json', "r") as file:
                data = json.load(file)
                mod_actions = data.get("actions", {})
        except json.JSONDecodeError:
            #await log_message(f"Error: `{DATA_FILE}` is not a valid JSON file or is empty. Starting fresh.")
            mod_actions = {}
    else:
        #await log_message(f"Error: `{DATA_FILE}` is not a valid JSON file or is empty. Starting fresh.")
        mod_actions = {}

    def save_data(self):
        data = {
            "actions": mod_actions
        }
        with open('mod_actions.json', "w") as file:
            json.dump(data, file, indent=4)

        # Update data on the Github
        """
        if lastUpdate - 1800 > round(time.time()):
            return False
        else:
            lastUpdate = round(time.time())
        
        try:
            subprocess.run(["git", "add", "data.json"], check=True)
            subprocess.run(["git", "commit", "-m", "Update data.json"], check=True)
            subprocess.run(["git", "push"], check=True)
        except subprocess.CalledProcessError as e:
            log_message(f"Error pushing changes to GitHub for data.json, '{e}'")
        """

    # ultra cool admin only commands
    def CheckPerms(self, user):
        if user.id == 277243145081716736:
            return True
        else:
            return False

    def log_modcommand(self, user_id: int, action: str, reason: str, mod: str, unban_time: str=None):
        entry = {
            "user_id": str(user_id),
            "action": action,
            "timestamp": str(round(time.time())),
            "reason": reason,
            "moderator_id": str(mod)
        }
        if unban_time:
            entry["unban_time"] = str(unban_time)



        cases = len(mod_actions)
        if not cases:
            cases = 0

        mod_actions[str(cases+1)] = entry
        self.save_data()

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
    async def ban(self, ctx, member: discord.Member, *, args="No reason provided"):
        if not self.CheckPerms(ctx.author):
            embed = discord.Embed(description="❌ You don't have permission to use this command.", color=0xcc182a)
            return await ctx.send(embed=embed)
        elif member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = discord.Embed(description="❌ You cant ban someone with a higher or equal role to you", color=0xcc182a)
            return await ctx.send(embed=embed)
        else:
            split = args.split(" ", 1)  # Split into time and reason
            bantime = split[0]
            duration = self.parse_time(bantime) if bantime else None

            if duration:
                reason = split[1] if len(split) > 1 else "No reason provided"
            else:
                bantime = None
                reason = args

            await member.ban(reason=reason)

            await self.bot.log(f"`{member}` has been banned for `{bantime}` because `{reason}` by `{ctx.author}`")

            unbanTime = None
            if duration:
                unbanTime = round(time.time()) + duration
            
            self.log_modcommand(
                user_id=member.id,
                action="ban",
                reason=reason,
                mod=ctx.author.id,
                unban_time=unbanTime
            )

            try:
                if bantime:
                    embed=discord.Embed(description=f"**You have been banned in stuffs for {bantime}** | {reason}", color=0x0c8eeb)
                else:
                    embed=discord.Embed(description=f"**You have been banned in stuffs** | {reason}", color=0x0c8eeb)
                await member.send(embed=embed)
            except discord.Forbidden:
                await self.bot.log(f"could not dm `{member}` during kick")

            if bantime:
                embed=discord.Embed(description=f"✅ **{member.mention} has been BANNED for {bantime}** | {reason}", color=0x06700b)
            else:
                embed=discord.Embed(description=f"✅ **{member.mention} has been BANNED** | {reason}", color=0x06700b)
            await ctx.send(embed=embed)

    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            embed=discord.Embed(description=f"❌ Please mention a valid member", color=0xcc182a)
            await ctx.send(embed=embed)
        else:
            await self.bot.log(f"Unknown error occured while banning member: {error}")
            embed=discord.Embed(description=f"❌ an unknown error has occured", color=0xcc182a)
            await ctx.send(embed=embed)

    @commands.command()
    async def kick(self, ctx, member: discord.Member, *, reason="No reason provided"):
        if not self.CheckPerms(ctx.author):
            embed = discord.Embed(description="❌ You don't have permission to use this command.", color=0xcc182a)
            return await ctx.send(embed=embed)
        elif member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = discord.Embed(description="❌ You cant kick someone with a higher or equal role to you", color=0xcc182a)
            return await ctx.send(embed=embed)
        else:
            await member.kick(reason=reason)
            
            await self.bot.log(f"`{member}` has been kicked because `{reason}` by `{ctx.author}`")

            self.log_modcommand(
                user_id=member.id,
                action="kick",
                reason=reason,
                mod=ctx.author.id,
            )

            embed=discord.Embed(description=f"✅ **{member.mention} has been KICKED** | {reason}", color=0x06700b)
            await ctx.send(embed=embed)

            try:
                embed=discord.Embed(description=f"**You have been kicked from stuffs** | {reason}", color=0x0c8eeb)
                await member.send(embed=embed)
            except discord.Forbidden:
                await self.bot.log(f"could not dm `{member}` during kick")

    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            embed=discord.Embed(description=f"❌ Please mention a valid member", color=0xcc182a)
            await ctx.send(embed=embed)
        else:
            await self.bot.log(f"Unknown error occured while kicking member: {error}")
            embed=discord.Embed(description=f"❌ an unknown error has occured", color=0xcc182a)
            await ctx.send(embed=embed)



    @commands.command()
    async def warn(self, ctx, member: discord.Member, *, reason="No reason provided"):
        if not self.CheckPerms(ctx.author):
            embed = discord.Embed(description="❌ You don't have permission to use this command.", color=0xcc182a)
            return await ctx.send(embed=embed)
        elif member.top_role > ctx.author.top_role and ctx.author != ctx.guild.owner:
            embed = discord.Embed(description="❌ You cant warn someone with a higher role than you", color=0xcc182a)
            return await ctx.send(embed=embed)
        else:        
            await self.bot.log(f"`{member}` has been warned for `{reason}` by `{ctx.author}`")

            self.log_modcommand(
                user_id=member.id,
                action="warn",
                reason=reason,
                mod=ctx.author.id,
            )

            embed=discord.Embed(description=f"✅ **{member.mention} has been WARNED** | {reason}", color=0x06700b)
            await ctx.send(embed=embed)

            try:
                embed=discord.Embed(description=f"**You have been warned in stuffs** | {reason}", color=0x0c8eeb)
                await member.send(embed=embed)
            except discord.Forbidden:
                await self.bot.log(f"could not dm `{member}` during warn")

    @warn.error
    async def warn_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            embed=discord.Embed(description=f"❌ Please mention a valid member", color=0xcc182a)
            await ctx.send(embed=embed)
        else:
            await self.bot.log(f"Unknown error occured while warning member: {error}")
            embed=discord.Embed(description=f"❌ an unknown error has occured", color=0xcc182a)
            await ctx.send(embed=embed)

    @commands.command()
    async def mute(self, ctx):
        await ctx.send("yeah your getting MUTED (imma code ts later)")



async def setup(bot):
    await bot.add_cog(AdminCommands(bot))