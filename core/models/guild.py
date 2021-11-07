import uuid

from django.db import models


class Guild(models.Model):

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)

    guild_id = models.CharField(max_length=255)

    tournament_channel_id = models.CharField(max_length=255, blank=True, null=True)
    manager_role_id = models.CharField(max_length=255, blank=True, null=True)

    withdrawal_address = models.CharField(max_length=64, blank=True, null=True)

    total_fee_collected = models.BigIntegerField(default=0)
    guild_balance = models.BigIntegerField(default=0)

    def __str__(self):
        return f"Server: {self.guild_id}; Fees: {self.total_fee_collected}"
