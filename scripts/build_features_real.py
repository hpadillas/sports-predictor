import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

engine = create_engine(os.getenv("DB_URL"))

df = pd.read_sql("SELECT * FROM historical_matches", engine)
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")

# ELO
elo = {}
INITIAL_ELO = 1500
K = 20

def get_elo(team):
    if team not in elo:
        elo[team] = INITIAL_ELO
    return elo[team]

def expected(a, b):
    return 1 / (1 + 10 ** ((b - a) / 400))

def update(home, away, result):
    ra = elo[home]
    rb = elo[away]

    ea = expected(ra, rb)

    if result == 1:
        sa = 1
    elif result == -1:
        sa = 0
    else:
        sa = 0.5

    elo[home] = ra + K * (sa - ea)
    elo[away] = rb + K * ((1 - sa) - (1 - ea))

# STATS
def get_stats(data, team, date):
    past = data[
        ((data.home_team == team) | (data.away_team == team)) &
        (data.date < date)
    ].tail(5)

    if len(past) == 0:
        return 0, 0, 0

    gf, ga, wins = [], [], 0

    for _, r in past.iterrows():
        if r.home_team == team:
            f, a = r.home_goals, r.away_goals
        else:
            f, a = r.away_goals, r.home_goals

        gf.append(f)
        ga.append(a)

        if f > a:
            wins += 1

    return sum(gf)/len(gf), sum(ga)/len(ga), wins/len(past)

# BUILD
rows = []

for _, m in df.iterrows():

    home = m.home_team
    away = m.away_team
    date = m.date

    h = get_stats(df, home, date)
    a = get_stats(df, away, date)

    rows.append({
        "date": date,
        "league": m.league,
        "home_team": home,
        "away_team": away,

        "home_avg_goals": h[0],
        "home_avg_conceded": h[1],
        "home_win_rate": h[2],

        "away_avg_goals": a[0],
        "away_avg_conceded": a[1],
        "away_win_rate": a[2],

        "home_elo": get_elo(home),
        "away_elo": get_elo(away),
        "elo_diff": get_elo(home) - get_elo(away),

        "odds_home": m.odds_home,
        "odds_draw": m.odds_draw,
        "odds_away": m.odds_away,

        "result": m.result
    })

    update(home, away, m.result)

features = pd.DataFrame(rows)

features = features[
    (features["home_avg_goals"] != 0) &
    (features["away_avg_goals"] != 0)
]

features.to_sql("features_real", engine, if_exists="replace", index=False)

print("✅ Features:", len(features))