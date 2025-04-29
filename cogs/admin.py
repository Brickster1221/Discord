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
                mod_actions = json.load(file)
        except json.JSONDecodeError:
            mod_actions = {}
    else:
        mod_actions = {}

    def save_data(self):
        with open('mod_actions.json', "w") as file:
            json.dump(mod_actions, file, indent=4)

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
    
    async def get_member(self, ctx, member):
        try:
            return await commands.MemberConverter().convert(ctx, member)
        except commands.BadArgument:
            try:
                user_id = int(member)
                return ctx.guild.get_member(user_id) or await ctx.guild.fetch_member(user_id)
            except (ValueError, discord.NotFound):
                pass
        await ctx.send(embed=discord.Embed(description="❌ Could not find a user with that ID or mention.", color=0xcc182a))
        return None

    async def check_perms(self, ctx, member):
        if ctx.author.id != 277243145081716736:
            await ctx.send(embed=discord.Embed(description="❌ You don't have permission to use this command.", color=0xcc182a))
            return False
        elif member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send(embed=discord.Embed(description="❌ You cant ban someone with a higher or equal role to you", color=0xcc182a))
            return False
        else:
            return True
        
    async def check_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            return await ctx.send(embed=discord.Embed(description=f"❌ Please mention a valid member", color=0xcc182a))
        else:
            await self.bot.log(f"Unknown error occured while banning member: `{error}`")
            return await ctx.send(embed=discord.Embed(description=f"❌ an unknown error has occured", color=0xcc182a))
        
    @commands.command()
    async def ban(self, ctx, member: str, *, args="No reason provided"):
        member = await self.get_member(ctx, member)
        if not member:
            return
        if not await self.check_perms(ctx, member):
            return
        
        split = args.split(" ", 1)  # Split into time and reason
        bantime = split[0]
        duration = self.parse_time(bantime) if bantime else None

        reason = split[1] if duration and len(split) > 1 else args
        if not duration:
            bantime = None

        await member.ban(reason=reason)
        await self.bot.log(f"`{member}` has been banned for `{bantime}` because `{reason}` by `{ctx.author}`")

        unbanTime = round(time.time()) + duration if duration else None
        
        self.log_modcommand(
            user_id=member.id,
            action="ban",
            reason=reason,
            mod=ctx.author.id,
            unban_time=unbanTime
        )

        try:
            embed=discord.Embed(description=(
                                f"**You have been banned in stuffs for {bantime}** | {reason}"
                                if bantime else
                                f"**You have been banned in stuffs** | {reason}"
                                ), color=0x0c8eeb)
            embed.set_footer(text="If you felt that this ban was unfair, please us our unban form, linklinklinklinklinklink")
            await member.send(embed=embed)
        except discord.Forbidden:
            await self.bot.log(f"could not dm `{member}` during ban")

        embed=discord.Embed(description=(
            f"✅ **{member.mention} has been BANNED for {bantime}** | {reason}"
            if bantime else
            f"✅ **{member.mention} has been BANNED** | {reason}"
            ), color=0x06700b)
        await ctx.send(embed=embed)

    @ban.error
    async def ban_error(self, ctx, error):
        await self.check_error(ctx,error)

    @commands.command()
    async def kick(self, ctx, member: str, *, reason="No reason provided"):
        member = await self.get_member(ctx, member)
        if not member:
            return
        if not await self.check_perms(ctx, member):
            return
        
        await member.kick(reason=reason)
        await self.bot.log(f"`{member}` has been kicked because `{reason}` by `{ctx.author}`")

        self.log_modcommand(
            user_id=member.id,
            action="kick",
            reason=reason,
            mod=ctx.author.id,
        )

        await ctx.send(embed=discord.Embed(description=f"✅ **{member.mention} has been KICKED** | {reason}", color=0x06700b))

        try:
            await member.send(embed=discord.Embed(description=f"**You have been kicked from stuffs** | {reason}", color=0x0c8eeb))
        except discord.Forbidden:
            await self.bot.log(f"could not dm `{member}` during kick")

    @kick.error
    async def kick_error(self, ctx, error):
        await self.check_error(ctx,error)

    @commands.command()
    async def warn(self, ctx, member: str, *, reason="No reason provided"):
        member = await self.get_member(ctx, member)
        if not member:
            return
        if not await self.check_perms(ctx, member):
            return
             
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
            await member.send(embed=discord.Embed(description=f"**You have been warned in stuffs** | {reason}", color=0x0c8eeb))
        except discord.Forbidden:
            await self.bot.log(f"could not dm `{member}` during warn")

    @warn.error
    async def warn_error(self, ctx, error):
        await self.check_error(ctx,error)

    @commands.command()
    async def mute(self, ctx):
        await ctx.send("yeah your getting MUTED (imma code ts later)")

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))