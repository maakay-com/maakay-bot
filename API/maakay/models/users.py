from uuid import uuid4

from django.db import models

from core.models.users import User


class MaakayUser(models.Model):

    uuid = models.UUIDField(default=uuid4, editable=False, primary_key=True)

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    total_won_in_challenges = models.IntegerField(default=0)
    total_lost_in_challenges = models.IntegerField(default=0)
    total_won_in_tournaments = models.IntegerField(default=0)

    total_tournaments_won = models.IntegerField(default=0)
    total_challenges_won = models.IntegerField(default=0)
    total_referred = models.IntegerField(default=0)

    def __str__(self):
        return f"User: {self.user};"
