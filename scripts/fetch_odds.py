import requests
import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
from pathlib import Path

# cargar env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("ODDS_API_KEY")
BASE_URL = os.getenv("ODDS_API_URL")

engine = create_engine(os.getenv("DB_URL"))

def fetch_odds():
    params = {
        "apiKey": API_KEY,
        "regions": "eu",
        "markets": "h2h"
    }

    response = requests.get(BASE_URL, params=params)

    if response.status_code != 200:
        print("Error:", response.status_code, response.text)
        return

    data = response.json()

    rows = []

    for game in data:
        home = game["home_team"]
        away = game["away_team"]

        # tomar primera casa
        if len(game["bookmakers"]) == 0:
            continue

        markets = game["bookmakers"][0]["markets"][0]["outcomes"]

        odds_home = None
        odds_draw = None
        odds_away = None

        for outcome in markets:
            if outcome["name"] == home:
                odds_home = outcome["price"]
            elif outcome["name"] == away:
                odds_away = outcome["price"]
            elif outcome["name"] == "Draw":
                odds_draw = outcome["price"]

        rows.append({
            "home_team": home,
            "away_team": away,
            "odds_home": odds_home,
            "odds_draw": odds_draw,
            "odds_away": odds_away
        })

    df = pd.DataFrame(rows)

    df.to_sql("odds", engine, if_exists="replace", index=False)

    print(f"{len(df)} odds guardadas")

if __name__ == "__main__":
    fetch_odds()