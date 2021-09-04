import os
import sys
import requests
import django
from discord_slash.context import ComponentContext
import discord
from asgiref.sync import sync_to_async
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_option
from discord_slash.utils.manage_components import create_button, create_actionrow
from discord_slash.model import ButtonStyle
from datetime import datetime


# Django Setup on bot
sys.path.append(os.getcwd() + '/API')
DJANGO_DIRECTORY = os.getcwd() + '/API'
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.environ["DJANGO_SETTINGS_MODULE"])
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()

from django.db.models import Q
from django.conf import settings
from core.models.users import User, UserTransactionHistory
from core.utils.scan_chain import match_transaction, check_confirmation, scan_chain

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
