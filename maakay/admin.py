from django.contrib import admin

from .models.challenge import Challenge
from .models.tournament import Tournament
from .models.profile import UserProfile


admin.site.register(Challenge)
admin.site.register(UserProfile)
admin.site.register(Tournament)
