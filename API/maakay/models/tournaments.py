import uuid

from django.db import models

from core.models.users import User


class Tournament(models.Model):

    ONGOING = 'ONGOING'
    CANCELLED = 'CANCELLED'
    COMPLETED = 'COMPLETED'

    status_choices = [
        (ONGOING, 'Ongoing'),
        (CANCELLED, 'Cancelled'),
        (COMPLETED, 'Completed')
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)

    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    url = models.URLField(null=True, blank=True)
    amount = models.BigIntegerField()

    hosted_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='hosted_by')
    winner = models.ForeignKey(User, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='winner')

    status = models.CharField(max_length=255, choices=status_choices, default='ONGOING')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Title: {self.title}; Amount: {self.amount}; Status: {self.status}'
