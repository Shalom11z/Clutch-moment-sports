import os
from django.core.management.base import BaseCommand
import requests
from games.models import Game

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def send_discord_notifications(message):
    requests.post(DISCORD_WEBHOOK_URL, json={"content": message})
class Command(BaseCommand):
    help = "Poll ESPN scoreboards and upsert Game rows."

    def handle(self, *args, **options):
        url = f"{ESPN_BASE}/soccer/fifa.world/scoreboard"
        response = requests.get(url)
        data = response.json()

        for event in data["events"]:
            competition = event["competitions"][0]
            status = competition["status"]
            competitors = competition["competitors"]

            for competitor in competitors:
                if competitor["homeAway"] == "home":
                    home_team = competitor["team"]["name"]
                    home_score = int(competitor["score"])
                elif competitor["homeAway"] == "away":
                    away_team = competitor["team"]["name"]
                    away_score = int(competitor["score"])

            game, created = Game.objects.update_or_create(
                espn_id=event["id"],
                defaults={
                    "round_name": event["season"]["slug"],
                    "home_team": home_team,
                    "away_team": away_team,
                    "home_score": home_score,
                    "away_score": away_score,
                    "status": status["type"]["state"],
                    "minute": status["displayClock"],
                }
            )
            is_clutch, reason = game.is_clutch()

            if is_clutch and not game.notified_clutch:
                send_discord_notifications(f"{game} - {reason}")
                game.notified_clutch = True
                game.save()

        self.stdout.write(self.style.SUCCESS("Updated games"))