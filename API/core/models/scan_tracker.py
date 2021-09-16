from django.db import models


class ScanTracker(models.Model):

    title = models.CharField(max_length=255)
    total_scans = models.IntegerField(default=0)
    last_scanned = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Total: {self.total_scans}; {self.last_scanned}'
