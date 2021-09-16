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
