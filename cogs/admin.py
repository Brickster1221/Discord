import discord
from discord.ext import commands
import time
import re
from datetime import timedelta

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ultra cool admin only commands

    def log_modcommand(self, user_id: int, action: str, reason: str, mod: str, guild: str, timeout: str=None):
        entry = {
            "user_id": str(user_id),
            "action": action,
            "timestamp": str(round(time.time())),
            "reason": reason,
            "moderator_id": str(mod),
        }
        if timeout:
            entry["duration"] = str(timeout)

        guild = str(guild)
        if guild not in self.bot.data["mod_actions"]:
            self.bot.data["mod_actions"][guild] = {}

        numb = max(int(k) for k in self.bot.data["mod_actions"][guild].keys()) + 1
        self.bot.data["mod_actions"][guild][str(numb)] = entry
        self.bot.save()

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
                return await self.bot.fetch_user(int(member))
            except (ValueError, discord.NotFound):
                pass
        await ctx.send(embed=discord.Embed(description="❌ Could not find a user with that ID or mention.", color=0xcc182a))
        return None

    async def check_perms(self, ctx, member):
        if ctx.author == ctx.guild.owner:
            return True
        has_role = discord.utils.get(ctx.author.roles, id=int(self.bot.data["guild_specific"][str(ctx.guild.id)]["moderator_role_id"]))
        if member and has_role:
            if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
                await ctx.send(embed=discord.Embed(description="❌ You cant do that to someone with a higher or equal role to you", color=0xcc182a))
                return False
        if has_role:
            return True
        
        await ctx.send(embed=discord.Embed(description="❌ You don't have permission to use this command.", color=0xcc182a))
        return False
    
    @commands.command()
    async def modlog(self, ctx, member: str="None"):
        member = await self.get_member(ctx, member)
        if not member:
            return
        
        casefound = 0
        embed=discord.Embed(title=f"Mod actions against {member}", color=0x0c8eeb)
        for id, case in self.bot.data["mod_actions"][str(ctx.guild.id)].items():
            if int(case['user_id']) == member.id:
                casefound += 1
                moderator = await ctx.guild.fetch_member(int(case['moderator_id']))
                embed.add_field(name=f"Case #{id}",
                    value=(
                        f"**Action:** {case['action'].capitalize()}\n"
                        f"**Reason:** {case['reason']}\n"
                        f"**User:** {member.mention} ({member})\n"
                        f"**Moderator:** {moderator.mention} ({moderator})\n"
                        f"Issued: <t:{case['timestamp']}:R>"
                    ), inline=False)
        if  casefound > 0:
            return await ctx.send(embed=embed)
        else:
            return await ctx.send(embed=discord.Embed(description=f"❌ There are no entries for this user", color=0xcc182a))

    async def moderate(self, ctx, action: str, member: str, args):
        try:
            member = await self.get_member(ctx, member)
            if not member:
                return
            if not await self.check_perms(ctx, member):
                return

            split = args.split(" ", 1)  # Split into time and reason
            time = split[0]
            duration = self.parse_time(time) if time else None

            reason = split[1] if duration and len(split) > 1 else args
            if not duration:
                time = None

            timeout = round(time.time()) + duration if duration else None

            self.log_modcommand(
                user_id=member.id,
                action=action,
                reason=reason,
                mod=ctx.author.id,
                guild=ctx.guild.id,
                timeout=timeout
            )

            dm_msg = {
                "ban": f"**You have been banned in stuffs for {time}** | {reason}" if time else f"**You have been banned in stuffs** | {reason}",
                "unban": f"**You have been unbanned from stuffs** | {reason}",
                "kick": f"**You have been kicked from stuffs** | {reason}",
                "warn": f"**You have been warned in stuffs** | {reason}"
            }[action]

            try:
                embed=discord.Embed(description=dm_msg, color=0x0c8eeb)
                if action == "ban":
                    embed.set_footer(text="If you felt that this ban was unfair, please us our unban form, https://forms.gle/efkNy4J9rBsufURVA")
                if action == "unban":
                    embed.add_field(value="Heres an invite to join back, https://discord.gg/9qBNfF5hHP")
                if action != "timeout":
                    await member.send(embed=embed)
            except discord.Forbidden:
                await self.bot.log(f"could not dm `{member}` during {action}")

            funny = {
                "ban": f"BANNED for {time}" if time else f"BANNED",
                "unban": f"UNBANNED",
                "kick": f"KICKED",
                "warn": f"WARNED",
                "timeout": f"MUTED"
            }[action]

            embed=discord.Embed(description=(
                f"✅ **{member.mention} has been {funny}** | {reason}"), color=0x06700b)
            await ctx.send(embed=embed)

            if action == "ban":
                await member.ban(reason=reason)
                await self.bot.log(f"`{member}` has been banned for `{time}` because `{reason}` by `{ctx.author}`")
            elif action == "unban":
                await ctx.guild.unban(member)
                await self.bot.log(f"`{member}` has been unbanned for `{reason}` by `{ctx.author}`")
            elif action == "kick":
                await member.kick(reason=reason)
                await self.bot.log(f"`{member}` has been kicked for `{reason}` by `{ctx.author}`")
            elif action == "warn":
                await self.bot.log(f"`{member}` has been warned for `{reason}` by `{ctx.author}`")
            elif action == "timeout":
                await member.timeout(timedelta(seconds=duration), reason=reason)
                await self.bot.log(f"`{member}` has been timed out for `{time}` because `{reason}` by `{ctx.author}`")
        except Exception as e:
            await self.bot.log(f"Unknown error occured while taking action on a member: `{e}`")
            return await ctx.send(embed=discord.Embed(description=f"❌ An unexpected error has occured.", color=0xcc182a))
    
    @commands.command()
    async def ban(self, ctx, member: str="None", *, args="No reason provided"):
        await self.moderate(ctx, "ban", member, args)

    @commands.command()
    async def unban(self, ctx, member: str="None", *, reason="No reason provided"):
        await self.moderate(ctx, "unban", member, reason)

    @commands.command()
    async def kick(self, ctx, member: str="None", *, reason="No reason provided"):
        await self.moderate(ctx, "kick", member, reason)

    @commands.command()
    async def warn(self, ctx, member: str="None", *, reason="No reason provided"):
        await self.moderate(ctx, "warn", member, reason)

    @commands.command()
    async def timeout(self, ctx, member: str="None", *, reason="No reason provided"):
        await self.moderate(ctx, "timeout", member, reason)

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))