import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_FOOTBALL_KEY")

url = "https://v3.football.api-sports.io/teams?name=Benfica"
headers = {"x-apisports-key": API_KEY}

response = requests.get(url, headers=headers)
data = response.json()

print(data)


