from django.db import models


class Challenge(models.Model):

    uuid = UUID
    challenger = UserFK
    contender = UserFK
    referee = UserFK
    
    title = String

    contender_accepted = Bool
    referee_accepted = Bool
    
    status = NEW, ONGOING, CANCELLED, COMPLETED
