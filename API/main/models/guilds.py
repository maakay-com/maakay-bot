from django.db import models


class Guild(models.Model):

    uuid = UUID

    guild_id = String
    agent_role_id = String
    tournament_channel_id = String
    total_fee_collected = Integer
