from django.db import models


class ScanTracker(models.Model):

    total_scans = models.IntegerField()
    last_scanned = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Total: {self.total_scans}; {self.last_scanned}'
