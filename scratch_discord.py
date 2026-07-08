import os
import requests 

webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")

response = requests.post(webhook_url, json={"content": "testing notification setting" })

print(response.status_code)