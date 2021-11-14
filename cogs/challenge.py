from discord.ext import commands
from discord_slash import cog_ext
from core.models.user import User
from discord import Color
import discord
from asgiref.sync import sync_to_async
from discord_slash.utils.manage_components import create_button, create_actionrow
from django.conf import settings
from discord_slash.model import ButtonStyle
from discord_slash.utils.manage_commands import create_option
from maakay.models.profile import UserProfile
from maakay.shortcuts import convert_to_decimal
from django.db.models import Q, F
from maakay.models.challenge import Challenge


class challenge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_subcommand(base="challenge", name="new", description="Create a new challenge!!",
                            options=[
                                create_option(
                                    name="title",
                                    description="The title of the challenge.",
                                    option_type=3,
                                    required=True
                                ),
                                create_option(
                                    name="amount",
                                    description="Enter TNBC amount you want to escrow.",
                                    option_type=10,
                                    required=True
                                ),
                                create_option(
                                    name="contender",
                                    description="Enter your escrow partner.",
                                    option_type=6,
                                    required=True
                                ),
                                create_option(
                                    name="referee",
                                    description="Enter your escrow partner.",
                                    option_type=6,
                                    required=True
                                )
                            ]
                            )
    async def challenge_new(self, ctx, title: str, amount: float, contender: discord.Member, referee: discord.Member):

        challenger_user, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))
        contender_user, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(contender.id))
        referee_user, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(referee.id))

        embed = discord.Embed(color=Color.orange())

        if not (challenger_user == contender_user or contender_user == referee_user or referee_user == challenger_user):

            total_amount = int(amount * settings.TNBC_MULTIPLICATION_FACTOR)

            if total_amount >= settings.MINIMUL_CHALLENGE_AMOUNT:
                if contender_user.get_available_balance() >= total_amount:
                    if challenger_user.get_available_balance() >= total_amount:
                        challenger_user.locked += total_amount
                        challenger_user.save()
                        embed.add_field(name='Challenge Invitation', value=f"{contender.mention}, {ctx.author.mention} invited you on *{title}* for **{amount} TNBC**.", inline=False)
                        embed.add_field(name='Referee Invitation', value=f"{referee.mention}, {ctx.author.mention} invited you to be referee of *{title}*.")
                        challenge = await sync_to_async(Challenge.objects.create)(challenger=challenger_user, contender=contender_user, referee=referee_user, title=title, amount=total_amount)
                        embed.set_footer(text=f"Challenge id - {challenge.uuid_hex}")
                        await ctx.send(f"{contender.mention} {referee.mention}", embed=embed, components=[create_actionrow(create_button(custom_id=f"challenge_accept_{challenge.uuid}", style=ButtonStyle.green, label="Accept"), create_button(custom_id=f"challenge_reject_{challenge.uuid}", style=ButtonStyle.red, label="Reject"))], hidden=False)
                    else:
                        embed.add_field(name="Error", value=f"You only have {challenger_user.get_decimal_available_balance()} TNBC availabe out of {amount}.")
                        await ctx.send(embed=embed, hidden=True)
                else:
                    embed.add_field(name="Error!", value=f"{contender.mention} only has {contender_user.get_decimal_available_balance()} TNBC available out of {amount}")
                    await ctx.send(embed=embed, hidden=True)
            else:
                embed.add_field(name="Error!", value=f"You can not challenge less than {settings.MINIMUL_CHALLENGE_AMOUNT / settings.TNBC_MULTIPLICATION_FACTOR} TNBC.")
                await ctx.send(embed=embed, hidden=True)
        else:
            embed.add_field(name="Error!", value="Challenger, Contender and referee all must be different users.")
            await ctx.send(embed=embed, hidden=True)

    @cog_ext.cog_subcommand(base="challenge", name="reward", description="Reward the challenge winner!!",
                            options=[
                                create_option(
                                    name="challenge_id",
                                    description="ID of challenge.",
                                    option_type=3,
                                    required=True
                                ),
                                create_option(
                                    name="user",
                                    description="Challenge winnner.",
                                    option_type=6,
                                    required=True
                                )
                            ]
                            )
    async def challenge_reward(self, ctx, challenge_id: str, user: discord.Member):

        referee, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))
        winner, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(user.id))

        embed = discord.Embed(color=Color.orange())

        # Check if the discord user is referee of the challenge
        if Challenge.objects.filter(uuid_hex=challenge_id, referee=referee).exists():

            challenge = await sync_to_async(Challenge.objects.get)(uuid_hex=challenge_id)

            # Check if the winner is either the challenger or contender of the challenge
            if challenge.challenger == winner or challenge.contender == winner:

                # Check if challenger is winner
                if challenge.challenger == winner:
                    loser = await self.bot.fetch_user(int(challenge.contender.discord_id))
                    challenge.contender.balance -= challenge.amount
                    challenge.contender.locked -= challenge.amount
                    challenge.contender.save()
                else:
                    loser = await self.bot.fetch_user(int(challenge.challenger.discord_id))
                    challenge.challenger.balance -= challenge.amount
                    challenge.challenger.locked -= challenge.amount
                    challenge.challenger.save()

                challenge.winner = winner
                challenge.status = Challenge.COMPLETED
                challenge.save()

                CHALLENGE_FEE_MULTIPLICATION = (100 - settings.CHALLENGE_FEE) / 100
                winner.balance += challenge.amount * CHALLENGE_FEE_MULTIPLICATION
                winner.locked -= challenge.amount
                winner.save()
                UserProfile.objects.filter(user=winner).update(total_won_in_challenges=F('total_won_in_challenges') + challenge.amount - settings.CHALLENGE_FEE,
                                                               total_challenges_won=F('total_challenges_won') + 1)
                UserProfile.objects.filter(user=referee).update(total_referred=F('total_referred') + 1)

                embed.add_field(name="Yaayy", value=f"{user.mention} is rewarded **{convert_to_decimal(challenge.amount - settings.CHALLENGE_FEE)}** TNBC for *{challenge.title}*.")
                embed.set_image(url="https://i.ibb.co/y8QBmQc/download.png")
                await ctx.send(f"{user.mention} {loser.mention}", embed=embed)

            else:
                embed.add_field(name="Error!", value="The winner must be participant of the challenge.")
                await ctx.send(embed=embed, hidden=True)

        else:
            embed.add_field(name="Error!", value="You're not a referee of this challenge.")
            await ctx.send(embed=embed, hidden=True)

    @cog_ext.cog_subcommand(base="challenge", name="cancel", options=[create_option(name="challenge_id", description="Id of the Challenge", option_type=3, required=True)])
    async def challenge_cancel(self, ctx, challenge_id):

        obj, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))

        embed = discord.Embed(title="Cancel Challenge", color=Color.orange())

        if Challenge.objects.filter(Q(challenger=obj) | Q(contender=obj), Q(uuid_hex=challenge_id)).exists():

            challenge = await sync_to_async(Challenge.objects.get)(uuid_hex=challenge_id)

            if challenge.status == Challenge.NEW:
                challenge.status = Challenge.CANCELLED
                challenge.save()

                if challenge.contender_status == Challenge.ACCEPTED:
                    challenge.contender.locked -= challenge.amount
                    challenge.contender.save()

                challenge.challenger.locked -= challenge.amount
                challenge.challenger.save()

                embed.add_field(name=f"**{challenge.title}**.", value="Challenge has been cancelled")

                challenger = await self.bot.fetch_user(int(challenge.challenger.discord_id))
                contender = await self.bot.fetch_user(int(challenge.contender.discord_id))

                await ctx.send(f"{challenger.mention} {contender.mention}", embed=embed)
            else:
                embed.add_field(name="Error", value="Sorry Ongoing or Completed Challenges cannnot be cancelled.")
                await ctx.send(embed=embed)
        else:
            embed.add_field(name="Error!", value="You don't have the permission to cancel this challenge.")
            await ctx.send(embed=embed)

    @cog_ext.cog_subcommand(base="challenge", name="history", description="Show the history of challenges in which the user was included.")
    async def challenge_history(self, ctx):

        obj, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))

        if Challenge.objects.filter(Q(challenger=obj) | Q(contender=obj), Q(status=Challenge.COMPLETED)).exists():

            challenges = (await sync_to_async(Challenge.objects.filter)(Q(challenger=obj) | Q(contender=obj), Q(status=Challenge.COMPLETED))).order_by('-created_at')[:5]
            embed = discord.Embed(title="Challenge History", color=Color.orange())

            for challenge in challenges:

                winner = await self.bot.fetch_user(int(challenge.winner.discord_id))

                if challenge.challenger == obj:
                    role = "Challenger"
                elif challenge.contender == obj:
                    role = "Contender"
                embed.add_field(name=f"**{challenge.title}**", value=f'> Role: {role}\n> Amount: {convert_to_decimal(challenge.amount)} TNBC\n> Won By: {winner.mention}', inline=False)
        else:
            embed = discord.Embed(title="404!", description="You have not participated in any challenge.", color=Color.orange())

        await ctx.send(embed=embed, hidden=True)

    @cog_ext.cog_subcommand(base="challenge", name="all", description="list all the active challenges!!")
    async def challenge_all(self, ctx):

        await ctx.defer(hidden=True)

        discord_user, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))

        embed = discord.Embed(title="Active Challanges", color=Color.orange())

        if Challenge.objects.filter(Q(challenger=discord_user) | Q(contender=discord_user) | Q(referee=discord_user), Q(status=Challenge.ONGOING)).exists():

            challenges = (await sync_to_async(Challenge.objects.filter)(Q(challenger=discord_user) | Q(contender=discord_user) | Q(referee=discord_user), Q(status=Challenge.ONGOING))).order_by('-created_at')[:5]

            for challenge in challenges:

                if challenge.challenger == discord_user:
                    role = "Challenger"
                elif challenge.contender == discord_user:
                    role = "Contender"
                else:
                    role = "Referee"
                embed.add_field(name=f"{challenge.title}", value=f"> ID: {challenge.uuid_hex}\n> Amount: {convert_to_decimal(challenge.amount)} TNBC\n> Role: {role}", inline=False)
        else:
            embed.add_field(name="404!", value="You have no ongoing challenges available.")

        await ctx.send(embed=embed, hidden=True)


def setup(bot):
    bot.add_cog(challenge(bot))
