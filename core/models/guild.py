import uuid

from django.db import models

from .user import User
from .transaction import Transaction


class Guild(models.Model):

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)

    guild_id = models.CharField(max_length=255, unique=True)

    tournament_channel_id = models.CharField(max_length=255, blank=True, null=True)
    manager_role_id = models.CharField(max_length=255, blank=True, null=True)

    withdrawal_address = models.CharField(max_length=64, blank=True, null=True)

    total_fee_collected = models.BigIntegerField(default=0)
    guild_balance = models.BigIntegerField(default=0)

    has_permissions = models.BooleanField(default=False)

    def __str__(self):
        return f"Server: {self.guild_id}; Fees: {self.total_fee_collected}"


class GuildTransaction(models.Model):

    DEPOSIT = 'DEPOSIT'
    WITHDRAW = 'WITHDRAW'

    type_choices = [
        (DEPOSIT, 'Deposit'),
        (WITHDRAW, 'Withdraw')
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)

    guild = models.ForeignKey(Guild, on_delete=models.CASCADE)
    withdrawn_by = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction = models.ForeignKey(Transaction, on_delete=models.DO_NOTHING)
    type = models.CharField(max_length=255, choices=type_choices)
    amount = models.BigIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Guild: {self.guild}; Amount: {self.amount}; Type: {self.type}"
