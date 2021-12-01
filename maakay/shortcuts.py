from django.conf import settings

from core.models.guild import Guild


def convert_to_decimal(amount):

    amount = amount / settings.TNBC_MULTIPLICATION_FACTOR
    rounded_amount = round(amount, 4)
    return rounded_amount


def convert_to_int(amount):

    return int(amount / settings.TNBC_MULTIPLICATION_FACTOR)


def get_or_create_guild(guild_id):

    guild, created = Guild.objects.get_or_create(guild_id=str(guild_id))

    return guild
