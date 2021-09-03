import uuid

from django.db import models

from .users import User


class Challenge(models.Model):

    NEW = 'NEW'
    ONGOING = 'ONGOING'
    CANCELLED = 'CANCELLED'
    COMPLETED = 'COMPLETED'

    status_choices = [
        (NEW, 'New'),
        (ONGOING, 'Ongoing'),
        (CANCELLED, 'Cancelled'),
        (COMPLETED, 'Completed')
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)

    challenger = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='challenger')
    contender = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='contender')
    referee = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='challenge_referee')

    amount = models.IntegerField()
    title = models.CharField(max_length=255)

    contender_accepted = models.BooleanField(default=False)
    referee_accepted = models.BooleanField(default=False)

    status = models.CharField(max_length=255, choices=status_choices)

    def __str__(self):
        return f"Title: {self.title}; Amount: {self.amount}"
