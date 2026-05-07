import requests
import pandas as pd
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

API_KEY = os.getenv("FOOTBALL_API_KEY")
BASE_URL = os.getenv("FOOTBALL_API_URL")

headers = {
    "X-Auth-Token": API_KEY
}

# 🔥 LIGAS QUE VAMOS A TRAER
competitions = {
    "PL": "England Premier League",
    "PD": "Spain La Liga",
    "SA": "Italy Serie A",
    "BL1": "Germany Bundesliga",
    "FL1": "France Ligue 1",
    "BSA": "Brazil Serie A"
}

all_matches = []

for code, name in competitions.items():

    url = f"{BASE_URL}/competitions/{code}/matches?status=SCHEDULED"

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"⚠️ Error con {name}")
        continue

    data = response.json()

    for m in data.get("matches", []):
        all_matches.append({
            "date": m["utcDate"],
            "home_team": m["homeTeam"]["name"],
            "away_team": m["awayTeam"]["name"],
            "league": name
        })

df = pd.DataFrame(all_matches)

df["date"] = pd.to_datetime(df["date"]).dt.date

print("✅ Partidos cargados:", len(df))
print(df.head())

# GUARDAR
base_path = Path(__file__).resolve().parent.parent
data_path = base_path / "data"
data_path.mkdir(exist_ok=True)

file_path = data_path / "future_matches.csv"
df.to_csv(file_path, index=False)

print("✅ Guardado en:", file_path)