from django.contrib import admin

from .models.transactions import Transaction
from .models.users import User, UserTransactionHistory
from .models.scan_tracker import ScanTracker
from .models.statistics import Statistic
from .models.guilds import Guild


# Register your models here.
admin.site.register(Transaction)
admin.site.register(User)
admin.site.register(ScanTracker)
admin.site.register(Guild)
admin.site.register(Statistic)
admin.site.register(UserTransactionHistory)
