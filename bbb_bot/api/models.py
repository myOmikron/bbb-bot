from django.db import models


class Bot(models.Model):
    pid = models.PositiveIntegerField(default=1)
