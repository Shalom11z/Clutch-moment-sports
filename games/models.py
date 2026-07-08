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

    minute = models.CharField(max_length=20, default="0'")
    status = models.CharField(max_length=20)

    notified_clutch = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.away_team} @ {self.home_team} ({self.away_score}-{self.home_score})"


    def is_clutch(self):
        """Return (bool, reason_string)."""

        if self.status != "in":
            return False, None

        if self.went_to_extra_time or (self.home_penalties is not None and self.away_penalties is not None):
            return True, "catch this game at extra time"

        current_minute = int(self.minute.split("'")[0])

        score_margin = abs(self.home_score - self.away_score)

        if current_minute >= 80 and score_margin <= 1:
            return True, "Catch this thriller game"

        return False, None
            