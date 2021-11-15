from asgiref.sync import sync_to_async
import discord
from discord import Color
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_option
from core.models.guild import Guild, GuildTransaction
from core.models.user import User
from core.models.transaction import Transaction
from core.models.statistic import Statistic
from maakay.shortcuts import convert_to_decimal, convert_to_int
from core.utils.send_tnbc import estimate_fee, withdraw_tnbc
from django.conf import settings


class admin(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_subcommand(base="admin",
                            name="set_withdrawl_address",
                            description="Set withdrawl adress for the server",
                            options=[
                                create_option(
                                    name="address",
                                    description="Withdrawl address",
                                    required=True,
                                    option_type=3)
                            ])
    async def admin_set_withdrawl_address(self, ctx, address):

        guild, created = await sync_to_async(Guild.objects.get_or_create)(guild_id=str(ctx.guild.id))

        if guild.has_permissions:

            has_role = False
            for role in ctx.author.roles:

                if role.id == int(guild.manager_role_id):
                    has_role = True
                    break

            if has_role:
                if len(address) == 64:

                    guild.withdrawal_address = address
                    guild.save()

                    await ctx.send(f"Withdrawl address for **{ctx.guild.name}** set to `{address}` successfully!", hidden=True)
                else:
                    await ctx.send("Invalid Withdrawl Address!", hidden=True)

            else:
                role = ctx.guild.get_role(int(guild.manager_role_id))
                await ctx.send(f"You don't have the required `{role.name}` Role!!", hidden=True)

        else:
            await ctx.send("Oh no, seems like Maakay-bot was not invited with correct permissions!!, \nHere are some steps to resolve the issue! \n ```1. Kick Maakay-bot. \n2. Invite Maakay-bot with 'Manage Roles' and 'Send Message' permissions.```", hidden=True)

    @cog_ext.cog_subcommand(base="admin",
                            name="info",
                            description="Check the maakay profile of your discord server.")
    async def admin_info(self, ctx):

        guild, created = await sync_to_async(Guild.objects.get_or_create)(guild_id=str(ctx.guild.id))

        if guild.has_permissions:

            has_role = False
            for role in ctx.author.roles:

                if role.id == int(guild.manager_role_id):
                    has_role = True
                    break

            if has_role:

                embed = discord.Embed()
                embed.add_field(name="Withdrawal Address", value=guild.withdrawal_address, inline=False)
                embed.add_field(name="Total Fees Collected (TNBC)", value=convert_to_decimal(guild.total_fee_collected))
                embed.add_field(name="Guild Balance (TNBC)", value=convert_to_decimal(guild.guild_balance))
                await ctx.send(embed=embed, hidden=True)

            else:
                role = ctx.guild.get_role(int(guild.manager_role_id))
                await ctx.send(f"You don't have the required `{role.name}` Role!!", hidden=True)
        else:
            await ctx.send("Oh no, seems like Maakay-bot was not invited with correct permissions!!, \nHere are some steps to resolve the issue! \n ```1. Kick Maakay-bot. \n2. Invite Maakay-bot with 'Manage Roles' and 'Send Message' permissions.```", hidden=True)

    @cog_ext.cog_subcommand(base="admin",
                            name="withdraw",
                            description="Withdraw TNBC from guild account!!",
                            options=[
                                create_option(
                                    name="amount_of_tnbc",
                                    description="Enter the amount of TNBC to withdraw.",
                                    option_type=4,
                                    required=True
                                )
                            ]
                            )
    async def admin_withdraw(self, ctx, amount_of_tnbc: int):

        await ctx.defer(hidden=True)

        discord_user, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))

        guild, created = await sync_to_async(Guild.objects.get_or_create)(guild_id=str(ctx.guild.id))

        if guild.has_permissions:

            has_role = False
            for role in ctx.author.roles:

                if role.id == int(guild.manager_role_id):
                    has_role = True
                    break

            if has_role:

                if guild.withdrawal_address:

                    fee = estimate_fee()

                    if fee:
                        if not amount_of_tnbc < 1:
                            if convert_to_int(guild.guild_balance) < amount_of_tnbc + fee:
                                embed = discord.Embed(title="Inadequate Funds!!",
                                                      description=f"This server only has {convert_to_int(guild.guild_balance) - fee} withdrawable TNBC (network fees included) available.")

                            else:
                                block_response, fee = withdraw_tnbc(guild.withdrawal_address, amount_of_tnbc, guild.guild_id)

                                if block_response:
                                    if block_response.status_code == 201:
                                        txs = Transaction.objects.create(confirmation_status=Transaction.WAITING_CONFIRMATION,
                                                                         transaction_status=Transaction.IDENTIFIED,
                                                                         direction=Transaction.OUTGOING,
                                                                         account_number=guild.withdrawal_address,
                                                                         amount=amount_of_tnbc * settings.TNBC_MULTIPLICATION_FACTOR,
                                                                         fee=fee * settings.TNBC_MULTIPLICATION_FACTOR,
                                                                         signature=block_response.json()['signature'],
                                                                         block=block_response.json()['id'],
                                                                         memo=guild.guild_id)
                                        converted_amount_plus_fee = (amount_of_tnbc + fee) * settings.TNBC_MULTIPLICATION_FACTOR
                                        guild.guild_balance -= converted_amount_plus_fee
                                        guild.save()

                                        GuildTransaction.objects.create(withdrawn_by=discord_user,
                                                                        amount=converted_amount_plus_fee,
                                                                        type=GuildTransaction.WITHDRAW,
                                                                        transaction=txs,
                                                                        guild=guild)

                                        statistic, created = Statistic.objects.get_or_create(title="main")
                                        statistic.total_balance -= converted_amount_plus_fee
                                        statistic.save()

                                        embed = discord.Embed(title="Coins Withdrawn!",
                                                              description=f"Successfully withdrawn {amount_of_tnbc} TNBC to {guild.withdrawal_address} \nUse `/admin info` to check the server statistics.")
                                    else:
                                        embed = discord.Embed(title="Error!", description="Please try again later!!")
                                else:
                                    embed = discord.Embed(title="Error!", description="Please try again later!!")
                        else:
                            embed = discord.Embed(title="Error!", description="You cannot withdraw less than 1 TNBC!!")
                    else:
                        embed = discord.Embed(title="Error!", description="Could not retrive fee info from the bank!!")
                else:
                    embed = discord.Embed(title="No withdrawal address set!!", description="Use `/set_withdrawal_address tnbc` to set withdrawal address!!")
            else:
                role = ctx.guild.get_role(int(guild.manager_role_id))
                embed = discord.Embed(title="Error", description=f"You don't have the required `{role.name}` role")
        else:
            embed = discord.Embed(title="Error",
                                  description="Oh no, seems like Maakay-bot was not invited with correct permissions!!, \nHere are some steps to resolve the issue! \n1. Kick Maakay-bot. \n2. Invite Maakay-bot with 'Manage Roles' and 'Send Message' permissions.")
        await ctx.send(embed=embed, hidden=True)

    @cog_ext.cog_subcommand(base="admin",
                            name="transactions",
                            description="Check the recent TNBC withdrawls from the discord server!!")
    async def admin_transactions(self, ctx):

        await ctx.defer(hidden=True)

        guild, created = await sync_to_async(Guild.objects.get_or_create)(guild_id=str(ctx.guild.id))

        if guild.has_permissions:

            has_role = False
            for role in ctx.author.roles:

                if role.id == int(guild.manager_role_id):
                    has_role = True
                    break

            if has_role:

                transactions = (await sync_to_async(GuildTransaction.objects.filter)(guild=guild)).order_by('-created_at')[:5]
                embed = discord.Embed(title="Transaction History", description="", color=Color.orange())

                for transaction in transactions:
                    user = await self.bot.fetch_user(int(transaction.withdrawn_by.discord_id))
                    embed.add_field(name='\u200b', value=f"{convert_to_decimal(transaction.amount)} TNBC {transaction.type} by {user.name}", inline=False)

            else:
                role = ctx.guild.get_role(int(guild.manager_role_id))
                embed = discord.Embed(title="Error", description=f"You don't have the required `{role.name}` role")
        else:
            embed = discord.Embed(title="Error",
                                  description="Oh no, seems like Maakay-bot was not invited with correct permissions!!, \nHere are some steps to resolve the issue! \n1. Kick Maakay-bot. \n2. Invite Maakay-bot with 'Manage Roles' and 'Send Message' permissions.")
        await ctx.send(embed=embed, hidden=True)


def setup(bot):
    bot.add_cog(admin(bot))
