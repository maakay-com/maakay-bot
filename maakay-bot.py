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
from django.db.models import Q, F
from core.models.transactions import Transaction
from core.models.statistics import Statistic
from core.models.users import User, UserTransactionHistory
from core.utils.scan_chain import match_transaction, check_confirmation, scan_chain
from core.utils.send_tnbc import estimate_fee, withdraw_tnbc
from maakay.models.users import UserTip, MaakayUser
from maakay.models.challenges import Challenge
from maakay.models.tournaments import Tournament
from maakay.shortcuts import convert_to_decimal

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


@slash.slash(name="balance", description="Check User Balance.")
async def user_balance(ctx):

    await ctx.defer(hidden=True)

    obj, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))

    embed = discord.Embed()
    embed.add_field(name='Withdrawal Address', value=obj.withdrawal_address, inline=False)
    embed.add_field(name='Balance', value=obj.get_decimal_balance())
    embed.add_field(name='Locked Amount', value=obj.get_decimal_locked_amount())
    embed.add_field(name='Available Balance', value=obj.get_decimal_available_balance())

    await ctx.send(embed=embed, hidden=True)


@slash.subcommand(base="deposit", name="tnbc", description="Deposit TNBC into your maakay account.")
async def user_deposit(ctx):

    await ctx.defer(hidden=True)

    obj, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))

    embed = discord.Embed(title="Send TNBC to the address with memo!!")
    embed.add_field(name='Address', value=settings.MAAKAY_PAYMENT_ACCOUNT_NUMBER, inline=False)
    embed.add_field(name='MEMO (MEMO is required, or you will lose your coins)', value=obj.memo, inline=False)

    await ctx.send(embed=embed, hidden=True, components=[create_actionrow(create_button(custom_id="chain-scan", style=ButtonStyle.green, label="Sent? Scan Chain"))])


@slash.subcommand(base="set_withdrawal_address", name="tnbc", description="Set a new withdrawal address.",
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


@slash.subcommand(base="withdraw", name="tnbc", description="Withdraw TNBC into your account!!",
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
            if not amount < 1:
                if obj.get_int_available_balance() < amount + fee:
                    embed = discord.Embed(title="Inadequate Funds!!",
                                          description=f"You only have {obj.get_int_available_balance() - fee} withdrawable TNBC (network fees included) available. \n Use `/user deposit` to deposit TNBC!!")

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
                            converted_amount_plus_fee =  (amount + fee) * settings.TNBC_MULTIPLICATION_FACTOR
                            obj.balance -= converted_amount_plus_fee
                            obj.save()
                            UserTransactionHistory.objects.create(user=obj, amount=converted_amount_plus_fee, type=UserTransactionHistory.WITHDRAW, transaction=txs)
                            statistic = Statistic.objects.first()
                            statistic.total_balance -= converted_amount_plus_fee
                            statistic.save()
                            embed = discord.Embed(title="Coins Withdrawn!",
                                                  description=f"Successfully withdrawn {amount} TNBC to {obj.withdrawal_address} \n Use `/user balance` to check your new balance.")
                        else:
                            embed = discord.Embed(title="Error!", description="Please try again later!!")
                    else:
                        embed = discord.Embed(title="Error!", description="Please try again later!!")
            else:
                embed = discord.Embed(title="Error!", description="You cannot withdraw less than 1 TNBC!!")
        else:
            embed = discord.Embed(title="Error!", description="Could not retrive fee info from the bank!!")
    else:
        embed = discord.Embed(title="No withdrawal address set!!", description="Use `/user set_withdrawal_address` to set withdrawal address!!")

    await ctx.send(embed=embed, hidden=True)


@slash.subcommand(base="transactions", name="tnbc", description="Check Transaction History!!")
async def user_transactions(ctx):

    await ctx.defer(hidden=True)

    obj, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))

    transactions = (await sync_to_async(UserTransactionHistory.objects.filter)(user=obj)).order_by('-created_at')[:8]

    embed = discord.Embed(title="Transaction History", description="")

    for txs in transactions:

        natural_day = humanize.naturalday(txs.created_at)

        embed.add_field(name='\u200b', value=f"{txs.type} - {txs.get_decimal_amount()} TNBC - {natural_day}", inline=False)

    await ctx.send(embed=embed, hidden=True)


@slash.slash(name="profile", description="Check the user profile!!",
                  options=[
                      create_option(
                          name="user",
                          description="User you want to check stats of.",
                          option_type=6,
                          required=False
                      )
                  ]
                  )
async def user_profile(ctx, user: discord.Member = None):

    await ctx.defer()

    if user:
        obj, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(user.id))
        embed = discord.Embed(title=f"Maakay Profile", description="")
        embed.set_author(name=user.name, icon_url=user.avatar_url)
    else:
        obj, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))
        embed = discord.Embed(title=f"Maakay Profile", description="")
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
    
    user_profile = await sync_to_async(MaakayUser.objects.get_or_create)(user=obj)

    embed.add_field(name='Total Challenges Won', value=f"{user_profile[0].total_challenges_won}")
    embed.add_field(name='Total Tournaments Won', value=f"{user_profile[0].total_tournaments_won}")
    embed.add_field(name='TNBC won in challenges', value=f"{user_profile[0].get_decimal_total_won_in_challenges()}")
    embed.add_field(name='TNBC won in tournaments', value=f"{user_profile[0].get_decimal_total_won_in_tournaments()}")
    embed.add_field(name='Total Times Referred', value=f"{user_profile[0].total_referred}")
    embed.add_field(name='Total Tip Sent', value=f"{user_profile[0].get_decimal_total_tip_sent()}")
    embed.add_field(name='Total Tip Received', value=f"{user_profile[0].get_decimal_total_tip_received()}")

    await ctx.send(embed=embed)


@slash.subcommand(base="tip", name="tnbc", description="Tip another user!!",
                  options=[
                      create_option(
                          name="amount",
                          description="Enter TNBC amount you want to escrow.",
                          option_type=10,
                          required=True
                      ),
                      create_option(
                          name="user",
                          description="Enter your escrow partner.",
                          option_type=6,
                          required=True
                      )
                  ]
                  )
async def tip_new(ctx, amount: float, user: discord.Member):

    sender, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))
    recepient, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(user.id))

    if sender != recepient:

        total_amount = int(amount * settings.TNBC_MULTIPLICATION_FACTOR)
        total_amount_including_fees = total_amount + settings.TIP_FEE

        if sender.get_available_balance() < total_amount_including_fees:
            available_balace_including_fee = sender.get_available_balance() - settings.TIP_FEE
            decimal_available_balace_including_fee = convert_to_decimal(available_balace_including_fee)
            embed = discord.Embed(title="Inadequate Funds!!",
                                  description=f"You only have {decimal_available_balace_including_fee} tippable TNBC available. \n Use `/user deposit` to deposit TNBC!!")
            await ctx.send(embed=embed, hidden=True)

        else:
            sender.balance -= total_amount_including_fees
            recepient.balance += total_amount
            sender.save()
            recepient.save()
            UserTip.objects.create(sender=sender, recepient=recepient, amount=total_amount)

            sender_profile = MaakayUser.objects.get_or_create(user=sender)
            recepient_profile = MaakayUser.objects.get_or_create(user=recepient)
            sender_profile[0].total_tip_sent += total_amount_including_fees
            sender_profile[0].save()
            recepient_profile[0].total_tip_received += total_amount
            recepient_profile[0].save()

            await ctx.send(f"{ctx.author.mention} tipped {user.mention} {amount} TNBC.")

    else:
        embed = discord.Embed(title="Sorry!", description=f"We cannot let you tip yourself.")
        embed.set_image(url="https://i.ibb.co/YWdpD99/e33.jpg")
        await ctx.send(embed=embed, hidden=True)


@slash.subcommand(base="tip", name="history", description="View tip history!!")
async def tip_history(ctx):

    await ctx.defer(hidden=True)
    
    obj, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))

    if UserTip.objects.filter(Q(sender=obj) | Q(recepient=obj)).exists():

        tips = (await sync_to_async(UserTip.objects.filter)(Q(sender=obj) | Q(recepient=obj))).order_by('-created_at')[:5]
        
        embed = discord.Embed()

        for tip in tips:

            sender = await client.fetch_user(int(tip.sender.discord_id))
            recepient = await client.fetch_user(int(tip.recepient.discord_id))

            embed.add_field(name="Sender", value=sender.mention)
            embed.add_field(name="Recepient", value=recepient.mention)
            embed.add_field(name="Amount", value=tip.get_decimal_amount())

    else:
        embed = discord.Embed(title="Error!!", description="404 Not Found.")

    await ctx.send(embed=embed, hidden=True)


@slash.subcommand(base="challenge", name="new", description="Create a new challenge!!",
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
async def challenge_new(ctx, title: str, amount: float, contender: discord.Member, referee: discord.Member):

    challenger_user, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))
    contender_user, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(contender.id))
    referee_user, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(referee.id))

    embed = discord.Embed()

    if not (challenger_user == contender_user or contender_user == referee_user or referee_user == challenger_user):

        total_amount = int(amount * settings.TNBC_MULTIPLICATION_FACTOR)

        if total_amount >= settings.MINIMUL_CHALLENGE_AMOUNT:
            if challenger_user.get_available_balance() >= total_amount:
                challenger_user.locked += total_amount
                challenger_user.save()
                embed.add_field(name='Challenge Invitation!!', value=f"Hi {contender.mention}, {ctx.author.mention} is inviting you for {amount} TNBC challenge.", inline=False)
                embed.add_field(name='Referee Invitation!!', value=f"Hi {referee.mention}, {ctx.author.mention} is inviting to be referee of challenge.")
                challenge = await sync_to_async(Challenge.objects.create)(challenger=challenger_user, contender=contender_user, referee=referee_user, title=title, amount=total_amount)
                await ctx.send(embed=embed, components=[create_actionrow(create_button(custom_id=f"challenge_accept_{challenge.uuid}", style=ButtonStyle.green, label="Accept"), create_button(custom_id=f"challenge_reject_{challenge.uuid}", style=ButtonStyle.red, label="Reject"))])
            else:
                embed.add_field(name="Error", value=f"You only have {challenger_user.get_decimal_available_balance()} TNBC availabe out of {amount}.")
                await ctx.send(embed=embed, hidden=True)
        else:
            embed.add_field(name="Error!", value=f"You can not challenge less than {settings.MINIMUL_CHALLENGE_AMOUNT / settings.TNBC_MULTIPLICATION_FACTOR} TNBC.")
            await ctx.send(embed=embed, hidden=True)
    else:
        embed.add_field(name="Error!", value="Challenger, Contender and referee all must be different users.")
        await ctx.send(embed=embed, hidden=True)


@slash.subcommand(base="reward", name="challenge", description="Reward the challenge winner!!",
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
async def challenge_reward(ctx, challenge_id: str, user: discord.Member):

    referee, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))
    winner, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(user.id))

    embed = discord.Embed()

    # Check if the discord user is referee of the challenge
    if Challenge.objects.filter(uuid_hex=challenge_id, referee=referee).exists():

        challenge = await sync_to_async(Challenge.objects.get)(uuid_hex=challenge_id)

        # Check if the winner is either the challenger or contender of the challenge
        if challenge.challenger == winner or challenge.contender == winner:

            # Check if challenger is winner
            if challenge.challenger == winner:
                challenge.contender.balance -= challenge.amount
                challenge.contender.locked -= challenge.amount
                challenge.contender.save()
            else:
                challenge.challenger.balance -= challenge.amount
                challenge.challenger.locked -= challenge.amount
                challenge.challenger.save()
            
            winner.balance += challenge.amount - settings.CHALLENGE_FEE
            winner.locked -= challenge.amount
            MaakayUser.objects.filter(user=winner).update(total_won_in_challenges=F('total_won_in_challenges') + challenge.amount - settings.CHALLENGE_FEE,
                                                          total_challenges_won=F('total_challenges_won') + 1)
            winner.save()

            embed.add_field(name="Success!", value=f"Successfully rewarded {user.mention} for the challenge.")
            await ctx.send(embed=embed)

        else:
            embed.add_field(name="Error!", value="The winner must be participant of the challenge.")
            await ctx.send(embed=embed, hidden=True)

    else:
        embed.add_field(name="Error!", value="You're not a referee of this challenge.")
        await ctx.send(embed=embed, hidden=True)

@slash.subcommand(base="challenge", name="history", description="Show the history of challenges in which the user was included.",
                 options=[
                    create_option(
                        name="user",
                        description="User whose challenge history is being talked about",
                        option_type=6,
                        required=True
                    )
                ]
                )

async def challenge_history(ctx, user:discord.Member):

    obj, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(user.id))

    if Challenge.objects.filter(Q(challenger=obj) | Q(contender=obj)).exists():

        challenges = await sync_to_async(Challenge.objects.filter(Q(challenger=obj) | Q(contender=obj))).order_by('-created_at')[:5]
        embed = discord.Embed(title=f"{obj.name}'s Challenge History")
        
        for challenge in challenges:
            if challenge.challenger == obj:
                role = "Challenger"
            elif challenge.contender == obj:
                role = "Contender"
            embed.add_field(name=f"**{challenge.title}**", value=f'> Role: {role}\n> Amount: {str(challenge.amount)}', inline=False)
    else:
        embed = discord.Embed(title="Error!!", description="404 Not Found.")
    
    await ctx.send(embed=embed, hidden=True)

@slash.subcommand(base="challenge", name="all", description="list all the active challenges!!")
async def challenge_all(ctx):

    await ctx.defer(hidden=True)
    
    discord_user, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))
    
    embed = discord.Embed()

    if Challenge.objects.filter(Q(challenger=discord_user) | Q(contender=discord_user) | Q(referee=discord_user), Q(status=Challenge.ONGOING)).exists():

        challenges = (await sync_to_async(Challenge.objects.filter)(Q(challenger=discord_user) | Q(contender=discord_user) | Q(referee=discord_user), Q(status=Challenge.ONGOING))).order_by('-created_at')[:5]

        for challenge in challenges:

            if challenge.challenger == discord_user:
                role = "Challenger"
            elif challenge.contender == discord_user:
                role = "Contender"
            else:
                role = "Referee"
            embed.add_field(name="Challenge ID", value=challenge.uuid_hex)
            embed.add_field(name="Amount", value=convert_to_decimal(challenge.amount))
            embed.add_field(name="Your Role", value=role)
    else:
        embed.add_field(name="404!", value="You have no ongoing challenges available.")

    await ctx.send(embed=embed, hidden=True)


@slash.slash(name="tournament", description="Create a new tournament!!",
                  options=[
                      create_option(
                          name="title",
                          description="The title of the tournament.",
                          option_type=3,
                          required=True
                      ),
                      create_option(
                          name="description",
                          description="More info about the tournament.",
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
                          name="url",
                          description="Here the users will get more info.",
                          option_type=3,
                          required=False
                      )
                  ]
                  )
async def tournament_new(ctx, title: str, description: str, amount: float, url: str = None):

    await ctx.defer(hidden=True)

    total_amount = int(amount * settings.TNBC_MULTIPLICATION_FACTOR)

    discord_user, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))

    if total_amount < settings.MINIMUM_TOURNAMENT_AMOUNT:
        embed = discord.Embed(title="Sorry",
                              description=f"You cannot create tournaments of less than {convert_to_decimal(settings.MINIMUM_TOURNAMENT_AMOUNT)} TNBC.")
        await ctx.send(embed=embed, hidden=True)
    else:
        if discord_user.get_available_balance() < total_amount:
            embed = discord.Embed(title="Sorry",
                                  description=f"You do not have enough maakay balance avalable.\nUse /deposit command to deposit TNBC.")
            await ctx.send(embed=embed, hidden=True)
        else:

            tournament_channel = client.get_channel(int(settings.TOURNAMENT_CHANNEL_ID))

            tournament_embed = discord.Embed(title=title, description=description)
            tournament_embed.add_field(name="Reward (TNBC)", value=amount)
            tournament_embed.add_field(name="More info", value=url)
            tournament_embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)

            await tournament_channel.send(embed=tournament_embed)

            Tournament.objects.create(title=title, description=description, url=url, amount=total_amount, hosted_by=discord_user)

            discord_user.locked += total_amount
            discord_user.save()

            await ctx.send("Tournament created successfully.", hidden=True)


@slash.subcommand(base="reward", name="tournament", description="Reward the challenge winner!!",
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
async def tournament_reward(ctx, tournament_id: str, user: discord.Member):

    discord_user, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))
    winner, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(user.id))

    embed = discord.Embed()

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

            winner.balance += tournament.amount - settings.TOURNAMENT_FEE
            winner.save()

            MaakayUser.objects.filter(user=winner).update(total_won_in_tournaments=F('total_won_in_tournaments') + tournament.amount - settings.TOURNAMENT_FEE,
                                                          total_tournaments_won=F('total_tournaments_won') + 1)

            winner = await client.fetch_user(user.id)
            hosted_by = await client.fetch_user(ctx.author.id)
            tournament_channel = client.get_channel(int(settings.TOURNAMENT_CHANNEL_ID))
            tournament_embed = discord.Embed(title="Tournament Ended", description="")
            tournament_embed.add_field(name="Title", value=tournament.title)
            tournament_embed.add_field(name="Description", value=tournament.description)
            tournament_embed.add_field(name="Reward (TNBC)", value=convert_to_decimal(tournament.amount - settings.TOURNAMENT_FEE))
            tournament_embed.add_field(name="More info", value=tournament.url)
            tournament_embed.add_field(name="Winner", value=winner.mention)
            tournament_embed.add_field(name="Hosted By", value=hosted_by.mention)
            tournament_embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            await tournament_channel.send(embed=tournament_embed)

            embed.add_field(name="Success!", value="The tournament is rewarded successfully.")
            await ctx.send(embed=embed, hidden=True)
        else:
            embed.add_field(name="Sorry!", value="The tournament is either cancelled or completed.")
            await ctx.send(embed=embed, hidden=True)
    else:
        embed.add_field(name="Sorry!", value="You donot have correct permission to reward this challenge.")
        await ctx.send(embed=embed, hidden=True)


@client.event
async def on_component(ctx: ComponentContext):

    button = ctx.custom_id.split('_')

    button_type = button[0]

    if button_type == "challenge":

        embed = discord.Embed()

        obj, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))

        challenge_uuid = button[2]

        if Challenge.objects.filter(uuid=challenge_uuid, status=Challenge.NEW).exists():

            button_action = button[1]

            challenge = await sync_to_async(Challenge.objects.get)(uuid=challenge_uuid)

            challenger = await client.fetch_user(int(challenge.challenger.discord_id))
            contender = await client.fetch_user(int(challenge.contender.discord_id))
            referee = await client.fetch_user(int(challenge.referee.discord_id))

            if challenge.contender == obj:
                if button_action == "accept":
                    if obj.get_available_balance() >= challenge.amount:
                        if challenge.referee_status == Challenge.ACCEPTED:
                            challenge.contender.locked += challenge.amount
                            challenge.contender.save()
                            challenge.status = Challenge.ONGOING
                        challenge.contender_status = Challenge.ACCEPTED
                        challenge.save()
                        embed.add_field(name="Accepted", value=f"Challenge accepted by contender {contender.mention}", inline=False)
                        embed.add_field(name="Title", value=challenge.title)
                        embed.add_field(name="Amount (TNBC)", value=challenge.get_decimal_amount())
                        embed.add_field(name="Challenger", value=f"{challenger.mention}")
                        embed.add_field(name="Contender", value=f"{contender.mention}")
                        embed.add_field(name="Referee", value=f"{referee.mention}")
                        embed.add_field(name="Status", value=challenge.status)
                        await ctx.send(embed=embed)
                    else:
                        embed.add_field(name="Error!", value=f"You only have {obj.get_decimal_available_balance()} TNBC out of {challenge.get_decimal_amount()} TNBC.\nPlease use `/user deposit` command to deposit TNBC.")
                        await ctx.send(embed=embed, hidden=True)
                else:
                    challenge.contender_status = Challenge.REJECTED
                    challenge.status = Challenge.CANCELLED
                    challenge.save()
                    challenge.challenger.locked -= challenge.amount
                    challenge.challenger.save()
                    embed.add_field(name="Rejected", value=f"Challenge rejected by contender {contender.mention}")
                    await ctx.send(embed=embed)
            elif challenge.referee == obj:
                if button_action == "accept":
                    if challenge.contender_status == Challenge.ACCEPTED:
                        challenge.status = Challenge.ONGOING
                        challenge.contender.locked += challenge.amount
                        challenge.contender.save()
                    challenge.referee_status = Challenge.ACCEPTED
                    challenge.save()
                    embed.add_field(name="Accepted", value=f"Challenge accepted by referee {referee.mention}", inline=False)
                    embed.add_field(name="Title", value=challenge.title)
                    embed.add_field(name="Amount (TNBC)", value=challenge.get_decimal_amount())
                    embed.add_field(name="Challenger", value=f"{challenger.mention}")
                    embed.add_field(name="Contender", value=f"{contender.mention}")
                    embed.add_field(name="Referee", value=f"{referee.mention}")
                    embed.add_field(name="Status", value=challenge.status)
                    await ctx.send(embed=embed)
                else:
                    challenge.referee_status = Challenge.REJECTED
                    challenge.status = Challenge.CANCELLED
                    challenge.save()
                    challenge.challenger.locked -= challenge.amount
                    challenge.challenger.save()
                    embed.add_field(name="Rejected", value=f"Challenge rejected by referee {referee.mention}")
                    await ctx.send(embed=embed, hidden=True)
            else:
                embed.add_field(name="Error!", value="You do not have correct permission to accept or reject this challenge.")
                embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
                await ctx.send(embed=embed, hidden=True)
        else:
            embed.add_field(name="Error!", value="The challenge is already underway/ completed or cancelled.")
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed, hidden=True)

    elif button_type == "chain-scan":

        await ctx.defer(hidden=True)
        
        scan_chain()

        # check_confirmation()

        match_transaction()

        obj, created = await sync_to_async(User.objects.get_or_create)(discord_id=str(ctx.author.id))

        embed = discord.Embed(title="Scan Completed")
        embed.add_field(name='New Balance', value=obj.get_decimal_balance())
        embed.add_field(name='Locked Amount', value=obj.get_decimal_locked_amount())
        embed.add_field(name='Available Balance', value=obj.get_decimal_available_balance())

        await ctx.send(embed=embed, hidden=True, components=[create_actionrow(create_button(custom_id="chain-scan", style=ButtonStyle.green, label="Scan Again?"))])


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
