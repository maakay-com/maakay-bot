from discord.ext import commands
from discord_slash import cog_ext
from core.models.user import User
from discord import Color
import discord
from asgiref.sync import sync_to_async
from django.conf import settings
from discord_slash.utils.manage_commands import create_option
from maakay.models.profile import UserTip, UserProfile
from maakay.shortcuts import convert_to_decimal, get_or_create_guild
from django.db.models import Q


class tip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_subcommand(base="tip", name="tnbc", description="Tip another user!!",
                            options=[
                                create_option(
                                    name="user",
                                    description="Enter your escrow partner.",
                                    option_type=6,
                                    required=True
                                ),
                                create_option(
                                    name="amount",
                                    description="Enter TNBC amount you want to escrow.",
                                    option_type=10,
                                    required=True
                                ),
                                create_option(
                                    name="message",
                                    description="Message for the tip.",
                                    option_type=3,
                                    required=False
                                )
                            ]
                            )
    async def tip_new(self, ctx, user: discord.Member, amount: float, message: str = None):

        sender, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))
        recepient, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(user.id))

        if sender != recepient:

            if amount >= 1:

                total_amount = int(amount * settings.TNBC_MULTIPLICATION_FACTOR)
                total_amount_including_fees = total_amount + settings.TIP_FEE

                if sender.get_available_balance() < total_amount_including_fees:

                    await ctx.defer(hidden=True)

                    available_balace_including_fee = sender.get_available_balance() - settings.TIP_FEE
                    decimal_available_balace_including_fee = convert_to_decimal(available_balace_including_fee)
                    embed = discord.Embed(title="Inadequate Funds!!",
                                          description=f"You only have {decimal_available_balace_including_fee} tippable TNBC available. \n Use `/deposit tnbc` to deposit TNBC!!", color=Color.orange())
                    await ctx.send(embed=embed, hidden=True)

                else:

                    await ctx.defer()
                    guild = ctx.guild

                    if guild:
                        guild_db = get_or_create_guild(guild.id)
                        guild_reward = settings.TIP_FEE * settings.MAAKAY_BOT_GUILD_REWARD / 100
                        guild_db.guild_balance += guild_reward
                        guild_db.total_fee_collected += guild_reward
                        guild_db.save()

                    sender.balance -= total_amount_including_fees
                    sender.save()

                    recepient.balance += total_amount
                    recepient.save()

                    UserTip.objects.create(sender=sender, recepient=recepient, amount=total_amount, title=message)

                    sender_profile, created = UserProfile.objects.get_or_create(user=sender)
                    sender_profile.total_tip_sent += total_amount_including_fees
                    sender_profile.save()

                    recepient_profile, created = UserProfile.objects.get_or_create(user=recepient)
                    recepient_profile.total_tip_received += total_amount
                    recepient_profile.save()

                    if message:
                        await ctx.send(f"{ctx.author.mention} tipped {user.mention} {amount} TNBC.\nMessage: {message}.")
                    else:
                        await ctx.send(f"{ctx.author.mention} tipped {user.mention} {amount} TNBC.")
            else:
                embed = discord.Embed(title="Sorry!", description="You can not tip less than 1 TNBC.")
                await ctx.send(embed=embed, hidden=True)
        else:
            embed = discord.Embed(title="Sorry!", description="We can not let you tip yourself.")
            embed.set_image(url="https://i.ibb.co/YWdpD99/e33.jpg")
            await ctx.send(embed=embed, hidden=True)

    @cog_ext.cog_subcommand(base="tip", name="history", description="View tip history!!")
    async def tip_history(self, ctx):

        await ctx.defer(hidden=True)

        obj, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))

        if UserTip.objects.filter(Q(sender=obj) | Q(recepient=obj)).exists():

            tips = (await sync_to_async(UserTip.objects.filter)(Q(sender=obj) | Q(recepient=obj))).order_by('-created_at')[:5]

            embed = discord.Embed(color=Color.orange())

            for tip in tips:

                sender = await self.bot.fetch_user(int(tip.sender.discord_id))
                recepient = await self.bot.fetch_user(int(tip.recepient.discord_id))

                embed.add_field(name="\u200b", value=f"> Sender: {sender.mention}\n> Recepient: {recepient.mention}\n> Amount: {convert_to_decimal(tip.amount)} TNBC\n> Message: {tip.title}", inline=False)

        else:
            embed = discord.Embed(title="Error!!", description="404 Not Found.", color=Color.orange())

        await ctx.send(embed=embed, hidden=True)


def setup(bot):
    bot.add_cog(tip(bot))
