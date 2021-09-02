from django.db import models


class Transaction(models.Model):

    uuid = UUID

    confirmation_status = WAITING_CONFIRMATION, CONFIRMED
    direction = INCOMING, OUTGOING
    transaction_status = NEW, IDENTIFIED, UNIDENTIFIED, REFUNDED

    account_number = String
    amount = Integer
    fee = Integer
    signature = String
    memo = String
    total_confirmations = Integer
    remarks = String
