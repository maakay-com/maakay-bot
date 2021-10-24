import uuid

from django.db import models
from django.conf import settings

from core.models.user import User


class Challenge(models.Model):

    NEW = 'NEW'
    ONGOING = 'ONGOING'
    CANCELLED = 'CANCELLED'
    COMPLETED = 'COMPLETED'

    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"

    acceptance_status = [
        (PENDING, 'Pending'),
        (ACCEPTED, 'Accepted'),
        (REJECTED, 'Rejected')
    ]

    status_choices = [
        (NEW, 'New'),
        (ONGOING, 'Ongoing'),
        (CANCELLED, 'Cancelled'),
        (COMPLETED, 'Completed')
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    uuid_hex = models.CharField(max_length=255, unique=True)

    challenger = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='challenger')
    contender = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='contender')
    referee = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='challenge_referee')

    amount = models.BigIntegerField()
    title = models.CharField(max_length=255)

    contender_status = models.CharField(max_length=255, choices=acceptance_status, default="PENDING")
    referee_status = models.CharField(max_length=255, choices=acceptance_status, default="PENDING")

    winner = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='challenge_winner')

    status = models.CharField(max_length=255, choices=status_choices, default="NEW")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_decimal_amount(self):
        amount = self.amount / settings.TNBC_MULTIPLICATION_FACTOR
        rounded_amount = round(amount, 4)
        return rounded_amount

    def __str__(self):
        return f"Title: {self.title}; Amount: {self.amount}"


# generate a random memo and check if its already taken.
# If taken, generate another memo again until we find a valid memo
def generate_hex_uuid(instance):

    while True:

        uuid_hex = f'{uuid.uuid4().hex}'

        if not Challenge.objects.filter(uuid_hex=uuid_hex).exists():
            return uuid_hex


def pre_save_post_receiver(sender, instance, *args, **kwargs):

    if not instance.uuid_hex:
        instance.uuid_hex = generate_hex_uuid(instance)


# save the memo before the User model is saved with the unique memo
models.signals.pre_save.connect(pre_save_post_receiver, sender=Challenge)
