from discord.ext import commands
import sys
sys.path.append("..")
from discord_slash import cog_ext
from core.models.users import User, UserTransactionHistory
from discord import Color
import discord
from asgiref.sync import sync_to_async
from discord_slash.utils.manage_components import create_button, create_actionrow
from django.conf import settings
from discord_slash.model import ButtonStyle
from discord_slash.utils.manage_commands import create_option
from core.utils.send_tnbc import estimate_fee, withdraw_tnbc
from core.models.transactions import Transaction
from core.models.statistics import Statistic
from maakay.models.users import  MaakayUser
from maakay.shortcuts import convert_to_decimal
import humanize

class general(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @cog_ext.cog_slash(name="balance", description="Check User Balance.")
    async def user_balance(self, ctx):

        # ctx.defer(hidden=True)

        obj, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))

        embed = discord.Embed(color=Color.orange())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        embed.add_field(name='Withdrawal Address', value=obj.withdrawal_address, inline=False)
        embed.add_field(name='Balance (TNBC)', value=obj.get_decimal_balance())
        embed.add_field(name='Locked Amount (TNBC)', value=obj.get_decimal_locked_amount())
        embed.add_field(name='Available Balance (TNBC)', value=obj.get_decimal_available_balance())

        await ctx.send(embed=embed, hidden=True)


    @cog_ext.cog_subcommand(base="deposit", name="tnbc", description="Deposit TNBC into your maakay account.")
    async def user_deposit(self, ctx):

        await ctx.defer(hidden=True)

        obj, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))

        qr_data = f"{{'address':{settings.TNBCROW_BOT_ACCOUNT_NUMBER},'memo':'{obj.memo}'}}"

        embed = discord.Embed(title="Send TNBC to the address with memo!!", color=Color.orange())
        embed.add_field(name='Warning', value="Do not deposit TNBC with Keysign Mobile Wallet/ Keysign Extension or **you'll lose your coins**.", inline=False)
        embed.add_field(name='Address', value=settings.MAAKAY_PAYMENT_ACCOUNT_NUMBER, inline=False)
        embed.add_field(name='MEMO (MEMO is required, or you will lose your coins)', value=obj.memo, inline=False)
        # embed.set_image(url=f"https://chart.googleapis.com/chart?chs=150x150&cht=qr&chl={qr_data}")
        # embed.set_footer(text="Or, scan the QR code using Keysign Mobile App.")
        
        await ctx.send(embed=embed, hidden=True, components=[create_actionrow(create_button(custom_id="chain-scan", style=ButtonStyle.green, label="Sent? Scan Chain"))])

    @cog_ext.cog_subcommand(base="set_withdrawal_address", name="tnbc", description="Set a new withdrawal address.",
                  options=[
                      create_option(
                          name="address",
                          description="Enter your withdrawal address.",
                          option_type=3,
                          required=True
                      )
                  ]
                  )
    async def user_setwithdrawaladdress(self, ctx, address: str):

        await ctx.defer(hidden=True)

        obj, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))

        embed = discord.Embed(color=Color.orange())

        if len(address) == 64:
            if address not in settings.PROHIBITED_ACCOUNT_NUMBERS:
                obj.withdrawal_address = address
                obj.save()

                embed.add_field(name='Success!!', value=f"Successfully set `{address}` as your withdrawal address!!")
            else:
                embed.add_field(name='Error!!', value="You can not set this account number as your withdrawal address!!")
        else:
            embed.add_field(name='Error!!', value="Please enter a valid TNBC account number!!")

        await ctx.send(embed=embed, hidden=True)


    @cog_ext.cog_subcommand(base="withdraw", name="tnbc", description="Withdraw TNBC into your account!!",
                  options=[
                      create_option(
                          name="amount",
                          description="Enter the amount to withdraw.",
                          option_type=4,
                          required=True
                      )
                  ]
                  )
    async def user_withdraw(self, ctx, amount: int):

        await ctx.defer(hidden=True)

        obj, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))

        if obj.withdrawal_address:

            fee = estimate_fee()

            if fee:
                if not amount < 1:
                    if obj.get_int_available_balance() < amount + fee:
                        embed = discord.Embed(title="Inadequate Funds!!",
                                            description=f"You only have {obj.get_int_available_balance() - fee} withdrawable TNBC (network fees included) available. \n Use `/deposit tnbc` to deposit TNBC!!")

                    else:
                        block_response, fee = withdraw_tnbc(obj.withdrawal_address, amount, obj.memo)

                        if block_response:
                            if block_response.status_code == 201:
                                txs = Transaction.objects.create(confirmation_status=Transaction.WAITING_CONFIRMATION,
                                                                transaction_status=Transaction.IDENTIFIED,
                                                                direction=Transaction.OUTGOING,
                                                                account_number=obj.withdrawal_address,
                                                                amount=amount * settings.TNBC_MULTIPLICATION_FACTOR,
                                                                fee=fee * settings.TNBC_MULTIPLICATION_FACTOR,
                                                                signature=block_response.json()['signature'],
                                                                block=block_response.json()['id'],
                                                                memo=obj.memo)
                                converted_amount_plus_fee = (amount + fee) * settings.TNBC_MULTIPLICATION_FACTOR
                                obj.balance -= converted_amount_plus_fee
                                obj.save()
                                UserTransactionHistory.objects.create(user=obj, amount=converted_amount_plus_fee, type=UserTransactionHistory.WITHDRAW, transaction=txs)
                                statistic, created = Statistic.objects.get_or_create(title="main")
                                statistic.total_balance -= converted_amount_plus_fee
                                statistic.save()
                                embed = discord.Embed(title="Coins Withdrawn!",
                                                    description=f"Successfully withdrawn {amount} TNBC to {obj.withdrawal_address} \n Use `/balance` to check your new balance.")
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

        await ctx.send(embed=embed, hidden=True)


    @cog_ext.cog_slash(name="profile", description="Check the user profile!!",
             options=[
                 create_option(
                     name="user",
                     description="User you want to check stats of.",
                     option_type=6,
                     required=False
                 )
             ]
             )
    async def user_profile(self, ctx, user: discord.Member = None):

        await ctx.defer()

        if user:
            obj, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(user.id))
            embed = discord.Embed(title=f"{user.name}'s Maakay Profile", description="", color=Color.orange())
            embed.set_thumbnail(url=user.avatar_url)
        else:
            obj, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))
            embed = discord.Embed(title=f"{ctx.author.name}'s Maakay Profile", description="", color=Color.orange())
            embed.set_thumbnail(url=ctx.author.avatar_url)

        user_profile = await sync_to_async(MaakayUser.objects.get_or_create)(user=obj)

        embed.add_field(name='Total Challenges Won', value=f"{user_profile[0].total_challenges_won}")
        embed.add_field(name='TNBC won in challenges', value=f"{user_profile[0].get_decimal_total_won_in_challenges()}")
        embed.add_field(name='TNBC won in hosted challenges', value=f"{user_profile[0].get_decimal_total_won_in_tournaments()}")
        embed.add_field(name='Total Challenges Hosted', value=f"{user_profile[0].total_challenges_hosted}")
        embed.add_field(name='TNBC Spent Hosting Challenges', value=f"{convert_to_decimal(user_profile[0].total_amount_hosted)}")
        embed.add_field(name='Total Tip Sent', value=f"{user_profile[0].get_decimal_total_tip_sent()}")
        embed.add_field(name='Total Tip Received', value=f"{user_profile[0].get_decimal_total_tip_received()}")

        await ctx.send(embed=embed)
        

    @cog_ext.cog_subcommand(base="transactions", name="tnbc", description="Check Transaction History!!")
    async def user_transactions(self, ctx):

        await ctx.defer(hidden=True)

        obj, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))

        transactions = (await sync_to_async(UserTransactionHistory.objects.filter)(user=obj)).order_by('-created_at')[:8]

        embed = discord.Embed(title="Transaction History", description="", color=Color.orange())

        for txs in transactions:

            natural_day = humanize.naturalday(txs.created_at)

            embed.add_field(name='\u200b', value=f"{txs.type} - {txs.get_decimal_amount()} TNBC - {natural_day}", inline=False)

        await ctx.send(embed=embed, hidden=True)


def setup(bot):
    bot.add_cog(general(bot))
