import requests

url = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"

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

    game = {
        "espn_id": event["id"],
        "home_team": home_team,
        "away_team": away_team,
        "home_score": home_score,
        "away_score": away_score,
        "status": status["type"]["name"],
        "minute": status["displayClock"],   
    }
    print(game)