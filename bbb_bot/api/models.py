from django.db import models


class Bot(models.Model):
    pid = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Bot {self.id}"
