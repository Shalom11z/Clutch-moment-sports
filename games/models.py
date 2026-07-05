from django.db import models

# Create your models here.

class Game(models.Model):
    espn_id = models.CharField(max_length=100, unique=True)

    round_name = models.CharField(max_length=50)

    home_team = models.CharField(max_length=50)
    away_team = models.CharField(max_length=50)
    home_score = models.IntegerField(default=0)
    away_score = models.IntegerField(default=0)

    went_to_extra_time = models.BooleanField(default=False)
    home_penalties = models.IntegerField(null=True, blank=True)
    away_penalties = models.IntegerField(null=True, blank=True)

    minute = models.IntegerField(default=0)
    status = models.CharField(max_length=20)