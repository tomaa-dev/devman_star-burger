from django.db import models
from django.utils import timezone


class Location(models.Model):
    address = models.CharField(
        'адрес',
        max_length=200,
        unique=True,
    )
    lat = models.FloatField(
        'широта',
    )
    lon = models.FloatField(
        'долгота',
    )
    requested_at = models.DateTimeField(
        'дата запроса',
        default=timezone.now,
    )

    class Meta:
        verbose_name = 'локация'
        verbose_name_plural = 'локации'

    def __str__(self):
        return f'{self.address} - ({self.lat}, {self.lon})'
