### Welcome to Maakay Bot

#### Getting Started
Clone the repo.

Activate the virtual environment.

Set the required environment variables.
```shell
DJANGO_SETTINGS_MODULE  # config.settings.development
MAAKAY_PAYMENT_ACCOUNT_NUMBER  # TNBC Account number that'll be used to receive payment
SIGNING_KEY  # Signing key of TNBC account that'll be used to transfer TNBC (suggested to use same set of account number and signing key)
BOT_MANAGER_ID  # Discord ID of the user who can use /kill command
MAAKAY_DISCORD_TOKEN  # Discord Token of the bot
SECRET_KEY  # Django Secret Key
```

Navigate to API and create required database and super user.
```shell
python manage.py migrate
python manage.py createsuperuser
```

Run the bot using the command `python maakay-bot.py`.

To run django server, navigate to API directory and use command `python manage.py runserver`.

Discord Bot guide coming soon.

#### Commands
`/balance`: Check your tnbc balance.

`/deposit tnbc`: Deposit TNBC into your maakay account.

`/set_withdrawl_address tnbc`: Set your TNBC withdrawal address.

`/withdraw tnbc <amount>`: Withdraw TNBC into your withdrawal address.

`/transactions tnbc`: List all your deposit and withdraw history.

`/profile <user (optional)>`: Check your or other user's maakay gaming profile.

`/tip tnbc <user> <amount> <message>`: Tip users TNBC with your beautiful message.

`/tip history`: Check your tip history.

`/challenge new <title> <amount> <contender> <referee>`: Start a new challenge with the contender with referee to reward once challenge is over.

`/challenge all`: List all your active challenges.

`/challenge reward <challenge_id> <winner>`: Reward the winner of the challenge.

`/challenge history`: List your challenge history.

`/tournament new <title> <description> <amount> <url (optional)>`: Start a new tournament with big prizes.

`/tournament reward <tournament_id> <winner>`: Reward the winner of the tournament.

`/tournament history`: View your tournament history.
