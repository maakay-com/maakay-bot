from django.db import models


class Statistic(models.Model):

    uuid = UUID
    
    total_balance = Integer
