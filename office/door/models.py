from django.db import models
from core.models import User


class DoorLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    time = models.DateTimeField(auto_now=True)
    command = models.CharField(max_length=100)
    response = models.CharField(max_length=500, null=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}: {self.command} ({self.time})"
