from uuid import uuid4

from django.db import models
from django.conf import settings

from core.models.users import User


class MaakayUser(models.Model):

    uuid = models.UUIDField(default=uuid4, editable=False, primary_key=True)

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    total_won_in_challenges = models.BigIntegerField(default=0)
    total_won_in_tournaments = models.BigIntegerField(default=0)

    total_challenges_hosted = models.BigIntegerField(default=0)
    total_amount_hosted = models.BigIntegerField(default=0)

    total_tournaments_won = models.IntegerField(default=0)
    total_challenges_won = models.IntegerField(default=0)
    total_referred = models.IntegerField(default=0)

    total_tip_sent = models.BigIntegerField(default=0)
    total_tip_received = models.BigIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_decimal_total_won_in_challenges(self):
        amount = self.total_won_in_challenges / settings.TNBC_MULTIPLICATION_FACTOR
        rounded_amount = round(amount, 4)
        return rounded_amount

    def get_decimal_total_won_in_tournaments(self):
        amount = self.total_won_in_tournaments / settings.TNBC_MULTIPLICATION_FACTOR
        rounded_amount = round(amount, 4)
        return rounded_amount

    def get_decimal_total_tip_sent(self):
        amount = self.total_tip_sent / settings.TNBC_MULTIPLICATION_FACTOR
        rounded_amount = round(amount, 4)
        return rounded_amount

    def get_decimal_total_tip_received(self):
        amount = self.total_tip_received / settings.TNBC_MULTIPLICATION_FACTOR
        rounded_amount = round(amount, 4)
        return rounded_amount

    def __str__(self):
        return f"User: {self.user};"


class UserTip(models.Model):

    uuid = models.UUIDField(default=uuid4, editable=False, primary_key=True)

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tip_sender')
    recepient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tip_recepient')

    amount = models.BigIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    title = models.CharField(max_length=255, null=True, blank=True)

    def get_decimal_amount(self):
        amount = self.amount / settings.TNBC_MULTIPLICATION_FACTOR
        rounded_amount = round(amount, 4)
        return rounded_amount

    def __str__(self):
        return f"{self.sender} to {self.recepient} {self.amount} TNBC."
