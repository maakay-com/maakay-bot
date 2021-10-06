from uuid import uuid4
import random
from django.conf import settings

from django.db import models
from ..models.transactions import Transaction


class User(models.Model):

    uuid = models.UUIDField(default=uuid4, editable=False, primary_key=True)

    discord_id = models.CharField(max_length=255, unique=True)
    balance = models.BigIntegerField(default=0)
    locked = models.BigIntegerField(default=0)
    memo = models.CharField(max_length=255, unique=True)
    withdrawal_address = models.CharField(max_length=64, blank=True, null=True)

    def get_available_balance(self):
        return self.balance - self.locked

    def get_decimal_balance(self):
        balance = self.balance / settings.TNBC_MULTIPLICATION_FACTOR
        rounded_balance = round(balance, 4)
        return rounded_balance

    def get_decimal_locked_amount(self):
        locked = self.locked / settings.TNBC_MULTIPLICATION_FACTOR
        rounded_locked = round(locked, 4)
        return rounded_locked

    def get_decimal_available_balance(self):
        available_balance = (self.balance - self.locked) / settings.TNBC_MULTIPLICATION_FACTOR
        rounded_available_balance = round(available_balance, 4)
        return rounded_available_balance

    def get_int_available_balance(self):
        available_balance = int((self.balance - self.locked) / settings.TNBC_MULTIPLICATION_FACTOR)
        return available_balance

    def __str__(self):
        return f"User: {self.discord_id}; Balance: {self.balance}; Available: {self.get_available_balance()}"


# generate a random memo and check if its already taken.
# If taken, generate another memo again until we find a valid memo
def generate_memo(instance):

    while True:

        memo = str(random.randint(100000, 999999))

        if not User.objects.filter(memo=memo).exists():
            return memo


def pre_save_post_receiver(sender, instance, *args, **kwargs):

    if not instance.memo:
        instance.memo = generate_memo(instance)


# save the memo before the User model is saved with the unique memo
models.signals.pre_save.connect(pre_save_post_receiver, sender=User)


class UserTransactionHistory(models.Model):

    DEPOSIT = 'DEPOSIT'
    WITHDRAW = 'WITHDRAW'

    type_choices = [
        (DEPOSIT, 'Deposit'),
        (WITHDRAW, 'Withdraw')
    ]

    uuid = models.UUIDField(default=uuid4, editable=False, primary_key=True)

    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    type = models.CharField(max_length=255, choices=type_choices)
    amount = models.BigIntegerField()
    transaction = models.ForeignKey(Transaction, on_delete=models.DO_NOTHING)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_decimal_amount(self):
        amount = self.amount / settings.TNBC_MULTIPLICATION_FACTOR
        rounded_amount = round(amount, 4)
        return rounded_amount

    def __str__(self):
        return f"User: {self.user} - {self.type} - {self.amount}"
