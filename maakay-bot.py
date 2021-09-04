import os
import humanize
import sys
import django
from discord_slash.context import ComponentContext
import discord
from asgiref.sync import sync_to_async
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_option
from discord_slash.utils.manage_components import create_button, create_actionrow
from discord_slash.model import ButtonStyle


# Django Setup on bot
sys.path.append(os.getcwd() + '/API')
DJANGO_DIRECTORY = os.getcwd() + '/API'
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.environ["DJANGO_SETTINGS_MODULE"])
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()

from django.conf import settings
from core.models.transactions import Transaction
from core.models.statistics import Statistic
from core.models.users import User, UserTransactionHistory
from core.utils.scan_chain import match_transaction, check_confirmation, scan_chain
from core.utils.send_tnbc import estimate_fee, withdraw_tnbc

# Environment Variables
TOKEN = os.environ['MAAKAY_DISCORD_TOKEN']

# Initialize the Slash commands
client = discord.Client(intents=discord.Intents.all())
slash = SlashCommand(client, sync_commands=True)


@client.event
async def on_ready():
    print("------------------------------------")
    print("maakay Bot Running:")
    print("------------------------------------")
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="/help"))


@slash.subcommand(base="user", name="balance", description="Check User Balance!!")
async def user_balance(ctx):

    await ctx.defer(hidden=True)

    obj, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))

    embed = discord.Embed()
    embed.add_field(name='Withdrawal Address', value=obj.withdrawal_address, inline=False)
    embed.add_field(name='Balance', value=obj.balance)
    embed.add_field(name='Locked Amount', value=obj.locked)
    embed.add_field(name='Available Balance', value=obj.get_available_balance())

    await ctx.send(embed=embed, hidden=True)


@slash.subcommand(base="user", name="deposit", description="Deposit TNBC into your maakay account!!")
async def user_deposit(ctx):

    await ctx.defer(hidden=True)

    obj, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))

    embed = discord.Embed(title="Send TNBC to the address with memo!!")
    embed.add_field(name='Address', value=settings.ACCOUNT_NUMBER, inline=False)
    embed.add_field(name='MEMO (MEMO is required, or you will lose your coins)', value=obj.memo, inline=False)

    await ctx.send(embed=embed, hidden=True, components=[create_actionrow(create_button(custom_id="chain_scan", style=ButtonStyle.green, label="Sent? Scan Chain"))])


@slash.component_callback()
async def chain_scan(ctx: ComponentContext):

    await ctx.defer(hidden=True)

    scan_chain()

    check_confirmation()

    match_transaction()

    obj, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))

    embed = discord.Embed(title="Scan Completed")
    embed.add_field(name='New Balance', value=obj.balance)
    embed.add_field(name='Locked Amount', value=obj.locked)
    embed.add_field(name='Available Balance', value=obj.get_available_balance())

    await ctx.send(embed=embed, hidden=True, components=[create_actionrow(create_button(custom_id="chain_scan", style=ButtonStyle.green, label="Scan Again?"))])


@slash.subcommand(base="user", name="set_withdrawal_address", description="Set new withdrawal address!!",
                  options=[
                      create_option(
                          name="address",
                          description="Enter your withdrawal address.",
                          option_type=3,
                          required=True
                      )
                  ]
                  )
async def user_setwithdrawaladdress(ctx, address: str):

    await ctx.defer(hidden=True)

    obj, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))

    if len(address) == 64:
        if address not in settings.PROHIBITED_ACCOUNT_NUMBERS:
            obj.withdrawal_address = address
            obj.save()
            embed = discord.Embed()
            embed.add_field(name='Success!!', value=f"Successfully set `{address}` as your withdrawal address!!")
        else:
            embed = discord.Embed()
            embed.add_field(name='Error!!', value="You can not set this account number as your withdrawal address!!")
    else:
        embed = discord.Embed()
        embed.add_field(name='Error!!', value="Please enter a valid TNBC account number!!")

    await ctx.send(embed=embed, hidden=True)


@slash.subcommand(base="user", name="withdraw", description="Withdraw TNBC into your account!!",
                  options=[
                      create_option(
                          name="amount",
                          description="Enter the amount to withdraw.",
                          option_type=4,
                          required=True
                      )
                  ]
                  )
async def user_withdraw(ctx, amount: int):

    await ctx.defer(hidden=True)

    obj, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))

    if obj.withdrawal_address:

        fee = estimate_fee()

        if fee:
            if not amount < 3:
                if obj.get_available_balance() < amount + fee:
                    embed = discord.Embed(title="Inadequate Funds!!",
                                        description=f"You only have {obj.get_available_balance() - fee} withdrawable TNBC (network fees included) available. \n Use `/user deposit` to deposit TNBC!!")

                else:
                    block_response, fee = withdraw_tnbc(obj.withdrawal_address, amount, obj.memo)

                    if block_response.status_code == 201:

                        txs = Transaction.objects.create(confirmation_status=Transaction.WAITING_CONFIRMATION,
                                                        transaction_status=Transaction.IDENTIFIED,
                                                        direction=Transaction.OUTGOING,
                                                        account_number=obj.withdrawal_address,
                                                        amount=amount,
                                                        fee=fee,
                                                        signature=block_response.json()['signature'],
                                                        block=block_response.json()['id'],
                                                        memo=obj.memo)
                        obj.balance -= amount + fee
                        obj.save()
                        UserTransactionHistory.objects.create(user=obj, amount=amount + fee, type=UserTransactionHistory.WITHDRAW, transaction=txs)
                        statistic = Statistic.objects.first()
                        statistic.total_balance -= (amount + fee)
                        statistic.save()
                        embed = discord.Embed(title="Coins Withdrawn!",
                                            description=f"Successfully withdrawn {amount} TNBC to {obj.withdrawal_address} \n Use `/user balance` to check your new balance.")
                    else:
                        embed = discord.Embed(title="Error!", description="Please try again later!!")
            else:
                embed = discord.Embed(title="Error!", description="You cannot withdraw less than 3 TNBC!!")
        else:
            embed = discord.Embed(title="Error!", description="Could not retrive fee info from the bank!!")
    else:
        embed = discord.Embed(title="No withdrawal address set!!", description="Use `/user set_withdrawal_address` to set withdrawal address!!")

    await ctx.send(embed=embed, hidden=True)


@slash.subcommand(base="user", name="transactions", description="Check Transaction History!!")
async def user_transactions(ctx):

    await ctx.defer(hidden=True)

    obj, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))

    transactions = (await sync_to_async(UserTransactionHistory.objects.filter)(user=obj)).order_by('-created_at')[:8]

    embed = discord.Embed(title="Transaction History", description="")

    for txs in transactions:

        natural_day = humanize.naturalday(txs.created_at)

        embed.add_field(name='\u200b', value=f"{txs.type} - {txs.amount} TNBC - {natural_day}", inline=False)

    await ctx.send(embed=embed, hidden=True)



@slash.slash(name="kill", description="Kill the bot!!")
async def kill(ctx):

    await ctx.defer(hidden=True)

    if int(ctx.author.id) == int(settings.BOT_MANAGER_ID):
        print("Shutting Down the bot")
        await ctx.send("Bot Shut Down", hidden=True)
        await client.close()
    else:
        await ctx.send("#DonotKillMaakayBot", hidden=True)

client.run(TOKEN)
