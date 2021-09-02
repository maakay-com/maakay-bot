from django.db import models


class ScanTracker(models.Model):

    uuid = UUID
    
    total_scans = Integer
    last_scanned = DateTime
