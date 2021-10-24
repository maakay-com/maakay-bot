from django.contrib import admin

from .models.transaction import Transaction
from .models.user import User, UserTransactionHistory
from .models.scan_tracker import ScanTracker
from .models.statistic import Statistic
from .models.guild import Guild


# Register your models here.
admin.site.register(Transaction)
admin.site.register(User)
admin.site.register(ScanTracker)
admin.site.register(Guild)
admin.site.register(Statistic)
admin.site.register(UserTransactionHistory)
