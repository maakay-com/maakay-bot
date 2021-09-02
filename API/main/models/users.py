from django.db import models


class User(models.Model):

    uuid = UUID

    discord_id = String

    balance = Integer
    locked = Integer
    get_available_balance() = Integer
    withdrawal_address = String

    total_tournaments_won = Integer
    total_challenges_won = Integer
    toal_referee_count = Integer
