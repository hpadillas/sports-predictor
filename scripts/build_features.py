import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
from pathlib import Path

# cargar .env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

engine = create_engine(os.getenv("DB_URL"))

# cargar datos
df = pd.read_sql("SELECT * FROM matches", engine)

# convertir fecha (IMPORTANTE)
df["date"] = pd.to_datetime(df["date"])

# ordenar por fecha
df = df.sort_values("date")

def get_team_stats(df, team, date):
    past = df[
        ((df.home_team == team) | (df.away_team == team)) &
        (df.date < date)
    ].tail(5)

    # 🔥 si no hay historial, devolver ceros (no eliminar)
    if len(past) == 0:
        return (0, 0, 0)

    goals_for = []
    goals_against = []
    wins = 0

    for _, row in past.iterrows():
        if row.home_team == team:
            gf = row.home_goals
            ga = row.away_goals
        else:
            gf = row.away_goals
            ga = row.home_goals

        goals_for.append(gf)
        goals_against.append(ga)

        if gf > ga:
            wins += 1

    return (
        sum(goals_for) / len(goals_for),
        sum(goals_against) / len(goals_against),
        wins / len(past)
    )

rows = []

for _, match in df.iterrows():
    home = match.home_team
    away = match.away_team
    date = match.date

    home_stats = get_team_stats(df, home, date)
    away_stats = get_team_stats(df, away, date)

    # resultado del partido
    result = 0
    if match.home_goals > match.away_goals:
        result = 1
    elif match.home_goals < match.away_goals:
        result = -1

    rows.append({
        # 🔥 clave para unir con odds
        "home_team": home,
        "away_team": away,

        # features
        "home_avg_goals": home_stats[0],
        "home_avg_conceded": home_stats[1],
        "home_win_rate": home_stats[2],

        "away_avg_goals": away_stats[0],
        "away_avg_conceded": away_stats[1],
        "away_win_rate": away_stats[2],

        # target
        "result": result
    })

features_df = pd.DataFrame(rows)

# guardar en DB
features_df.to_sql("features", engine, if_exists="replace", index=False)

print("Features creadas:", len(features_df))
print(features_df.head())