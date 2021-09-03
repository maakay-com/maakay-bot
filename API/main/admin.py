from django.contrib import admin

from .models.challenges import Challenge
from .models.guilds import Guild
from .models.scan_tracker import ScanTracker
from .models.statistics import Statistic
from .models.tournaments import Tournament
from .models.transactions import Transaction
from .models.users import User, UserTransactionHistory


admin.site.register(Challenge)
admin.site.register(Guild)
admin.site.register(ScanTracker)
admin.site.register(Statistic)
admin.site.register(Tournament)
admin.site.register(Transaction)
admin.site.register(User)
admin.site.register(UserTransactionHistory)
