from django.db import models


class Tournament(models.Model):

    uuid = UUID

    title = String
    description = String
    url = URL
    amount = Integer
    referee = UserFK
    winner = UserFK
