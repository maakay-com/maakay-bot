from django.contrib import admin

from .models.challenges import Challenge
from .models.tournaments import Tournament
from .models.users import MaakayUser


admin.site.register(Challenge)
admin.site.register(MaakayUser)
admin.site.register(Tournament)
