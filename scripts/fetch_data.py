import requests
import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
from pathlib import Path

# cargar env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

DB_URL = os.getenv("DB_URL")
API_KEY = os.getenv("FOOTBALL_API_KEY")
BASE_URL = os.getenv("FOOTBALL_API_URL")

engine = create_engine(DB_URL)

def fetch_matches():
    url = f"{BASE_URL}/competitions/PL/matches"

    headers = {
        "X-Auth-Token": API_KEY
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("Error:", response.status_code, response.text)
        return

    data = response.json()

    rows = []

    for match in data["matches"]:
        if match["score"]["fullTime"]["home"] is None:
            continue

        rows.append({
            "home_team": match["homeTeam"]["name"],
            "away_team": match["awayTeam"]["name"],
            "home_goals": match["score"]["fullTime"]["home"],
            "away_goals": match["score"]["fullTime"]["away"],
            "date": match["utcDate"]
        })

    df = pd.DataFrame(rows)

    df.to_sql("matches", engine, if_exists="replace", index=False)

    print(f"{len(df)} partidos EPL guardados")

if __name__ == "__main__":
    fetch_matches()