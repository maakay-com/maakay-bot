import uuid

from django.db import models


class Transaction(models.Model):

    WAITING_CONFIRMATION = 'WAITING_CONFIRMATION'
    CONFIRMED = 'CONFIRMED'

    INCOMING = 'INCOMING'
    OUTGOING = 'OUTGOING'

    NEW = 'NEW'
    IDENTIFIED = 'IDENTIFIED'
    UNIDENTIFIED = 'UNIDENTIFIED'
    REFUNDED = 'REFUNDED'

    transaction_status_choices = [
        (NEW, 'New'),
        (IDENTIFIED, 'Identified'),
        (UNIDENTIFIED, 'Unidentified'),
        (REFUNDED, 'Refunded'),
    ]

    direction_choices = [
        (INCOMING, 'Incoming'),
        (OUTGOING, 'Outgoing')
    ]

    confirmation_status_choices = [
        (WAITING_CONFIRMATION, 'Waiting Confirmation'),
        (CONFIRMED, 'Confirmed'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)

    confirmation_status = models.CharField(max_length=255, choices=confirmation_status_choices)
    direction = models.CharField(max_length=255, choices=direction_choices)
    transaction_status = models.CharField(max_length=255, choices=transaction_status_choices)

    account_number = models.CharField(max_length=64)
    amount = models.IntegerField()
    fee = models.IntegerField(default=0)
    signature = models.CharField(max_length=255)
    block = models.CharField(max_length=255)
    memo = models.CharField(max_length=255)
    total_confirmations = models.IntegerField(default=0)
    remarks = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.direction} | {self.amount} | {self.transaction_status} | {self.confirmation_status}'
