from discord.ext import commands
import sys
sys.path.append("..")
from discord_slash import SlashContext, cog_ext
from core.models.users import User
from discord import Color
import discord
from asgiref.sync import sync_to_async
from django.conf import settings
from discord_slash.utils.manage_commands import create_option
from maakay.models.users import  MaakayUser
from maakay.shortcuts import convert_to_decimal
from django.db.models import Q, F
from maakay.models.tournaments import Tournament

TOURNAMENT_FEE_MULTIPLICATION = (100 - settings.TOURNAMENT_FEE) / 100

class hosted_challenge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_subcommand(base="host", name="challenge", description="Host challenge between users!!",
                  options=[
                      create_option(
                          name="title",
                          description="The title of the hosted challenge.",
                          option_type=3,
                          required=True
                      ),
                      create_option(
                          name="description",
                          description="More info about the hosted challenge.",
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
                          name="player1",
                          description="User that'll be participant.",
                          option_type=6,
                          required=True
                      ),
                      create_option(
                          name="player2",
                          description="User that'll be participant.",
                          option_type=6,
                          required=True
                      ),
                      create_option(
                          name="player3",
                          description="User that'll be participant.",
                          option_type=6,
                          required=False
                      ),
                      create_option(
                          name="player4",
                          description="User that'll be participant.",
                          option_type=6,
                          required=False
                      )
                  ]
                  )
    async def tournament_new(self, ctx, title: str, description: str, amount: float, player1: discord.Member, player2: discord.Member, player3: discord.Member = None, player4: discord.Member = None):

        await ctx.defer(hidden=True)

        total_amount = int(amount * settings.TNBC_MULTIPLICATION_FACTOR)

        discord_user, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))

        if total_amount < settings.MINIMUM_TOURNAMENT_AMOUNT:
            embed = discord.Embed(title="Sorry",
                                description=f"You cannot host challenges less than {convert_to_decimal(settings.MINIMUM_TOURNAMENT_AMOUNT)} TNBC.", color=Color.orange())
            await ctx.send(embed=embed, hidden=True)
        else:
            if discord_user.get_available_balance() < total_amount:
                embed = discord.Embed(title="Sorry",
                                    description="You do not have enough maakay balance avalable.\nUse `/deposit tnbc` command to deposit TNBC.", color=Color.orange())
                await ctx.send(embed=embed, hidden=True)
            else:

                tournament_channel = self.bot.get_channel(int(settings.TOURNAMENT_CHANNEL_ID))

                tournament_embed = discord.Embed(title="Challenge Hosted Alert!!", description=f"{ctx.author.mention} has hosted a challenge.")
                tournament_embed.add_field(name="Title", value=title)
                tournament_embed.add_field(name="Description", value=description)
                tournament_embed.add_field(name="Reward (TNBC)", value=f"**{amount}**", inline=False)
                tournament_embed.set_thumbnail(url=ctx.author.avatar_url)

                if player3:
                    if player4:
                        message = f"{player1.mention} {player2.mention} {player3.mention} {player4.mention}"
                    else:
                        message = f"{player1.mention} {player2.mention} {player3.mention}"
                else:
                    message = f"{player1.mention} {player2.mention}"

                await tournament_channel.send(message, embed=tournament_embed)

                Tournament.objects.create(title=title, description=description, amount=total_amount, hosted_by=discord_user)
                MaakayUser.objects.filter(user=discord_user).update(total_amount_hosted=F('total_amount_hosted') + total_amount,
                                                                    total_challenges_hosted=F('total_challenges_hosted') + 1)

                discord_user.locked += total_amount
                discord_user.save()

                await ctx.send("Challenge Hosted successfully.", hidden=True)


    @cog_ext.cog_subcommand(base="host", name="reward", description="Reward the challenge winner!!",
                  options=[
                      create_option(
                          name="tournament_id",
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
    async def tournament_reward(self, ctx, tournament_id: str, user: discord.Member):

        discord_user, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))
        winner, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(user.id))

        embed = discord.Embed(color=Color.orange())

        # Check if the discord user is referee of the reward
        if Tournament.objects.filter(uuid_hex=tournament_id, hosted_by=discord_user).exists():
            if Tournament.objects.filter(uuid_hex=tournament_id, status=Tournament.ONGOING).exists():
                tournament = await sync_to_async(Tournament.objects.get)(uuid_hex=tournament_id)
                tournament.status = Tournament.COMPLETED
                tournament.winner = winner
                tournament.save()

                discord_user.balance -= tournament.amount
                discord_user.locked -= tournament.amount
                discord_user.save()

                winner.balance += tournament.amount * TOURNAMENT_FEE_MULTIPLICATION
                winner.save()

                MaakayUser.objects.filter(user=winner).update(total_won_in_tournaments=F('total_won_in_tournaments') + tournament.amount - settings.TOURNAMENT_FEE,
                                                            total_tournaments_won=F('total_tournaments_won') + 1)

                winner = await self.bot.fetch_user(user.id)
                hosted_by = await self.bot.fetch_user(ctx.author.id)
                tournament_channel = self.bot.get_channel(int(settings.TOURNAMENT_CHANNEL_ID))
                tournament_embed = discord.Embed(title=f"Congratulations {winner.mention} !!", description="")
                tournament_embed.add_field(name="Title", value=tournament.title)
                tournament_embed.add_field(name="Description", value=tournament.description)
                tournament_embed.add_field(name="Reward (TNBC)", value=f"**{convert_to_decimal(tournament.amount - settings.TOURNAMENT_FEE)}**", inline=False)
                tournament_embed.add_field(name="Winner", value=winner.mention)
                tournament_embed.add_field(name="Hosted By", value=hosted_by.mention)
                tournament_embed.set_thumbnail(url=ctx.author.avatar_url)
                await tournament_channel.send(f"{winner.mention}", embed=tournament_embed)

                embed.add_field(name="Success!", value="The hosted challenge is rewarded successfully.")
                await ctx.send(embed=embed, hidden=True)
            else:
                embed.add_field(name="Sorry!", value="The hosted challenge is either cancelled or completed.")
                await ctx.send(embed=embed, hidden=True)
        else:
            embed.add_field(name="Sorry!", value="You donot have correct permission to reward this challenge.")
            await ctx.send(embed=embed, hidden=True)

    @cog_ext.cog_subcommand(base="hosted", name="all", description="list all the active hosted challenges!!")
    async def tournament_all(self, ctx):

        await ctx.defer(hidden=True)
        discord_user, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))

        embed = discord.Embed(title="Active Hosted Challenges", color=Color.orange())

        if Tournament.objects.filter(Q(hosted_by=discord_user), Q(status=Tournament.ONGOING)).exists():

            tournaments = (await sync_to_async(Tournament.objects.filter)(Q(hosted_by=discord_user), Q(status=Tournament.ONGOING))).order_by('-created_at')[:5]
            for tournament in tournaments:
                embed.add_field(name=f"**{tournament.title}**\n *{tournament.description}*", value=f"> ID: {tournament.uuid_hex}\n> Role: Host\n> Amount: {convert_to_decimal(tournament.amount)}", inline=False)
        else:
            embed.add_field(name="404!", value="You have no ongoing hosted challenges available.")

        await ctx.send(embed=embed, hidden=True)

    @cog_ext.cog_subcommand(base="hosted", name="history", description="list all the challenges user has participated in!!")
    async def tournament_history(self, ctx):

        await ctx.defer(hidden=True)

        discord_user, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))

        embed = discord.Embed(color=Color.orange())

        if Tournament.objects.filter(Q(hosted_by=discord_user) | Q(winner=discord_user), Q(status=Tournament.COMPLETED)).exists():

            tournaments = (await sync_to_async(Tournament.objects.filter)(Q(hosted_by=discord_user) | Q(winner=discord_user), Q(status=Tournament.COMPLETED))).order_by('-created_at')[:5]
            for tournament in tournaments:

                if tournament.hosted_by == discord_user:
                    role = "Host"
                else:
                    role = "Winner"

                embed.add_field(name=f"**{tournament.title}**\n *{tournament.description}*", value=f"> Role: {role}\n > Amount: {convert_to_decimal(tournament.amount)} TNBC", inline=False)

        else:
            embed.add_field(name='404!', value="You have not hosted/ participated in hosted challenges.")

        await ctx.send(embed=embed, hidden=True)



def setup(bot):
    bot.add_cog(hosted_challenge(bot))