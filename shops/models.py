from django.db import models
from utils.models import TimeStampedSoftDeleteModel

class Shop(TimeStampedSoftDeleteModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name