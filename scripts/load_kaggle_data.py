import pandas as pd
from sqlalchemy import create_engine
import sqlite3
from dotenv import load_dotenv
from pathlib import Path
import os

# CONFIG
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

engine = create_engine(os.getenv("DB_URL"))

# SQLITE
db_path = Path(__file__).resolve().parent.parent / "data" / "database.sqlite"
conn = sqlite3.connect(db_path)

# JOIN COMPLETO
query = """
SELECT 
    m.date,
    l.name AS league,
    c.name AS country,
    ht.team_long_name AS home_team,
    at.team_long_name AS away_team,
    m.home_team_goal AS home_goals,
    m.away_team_goal AS away_goals
FROM Match m
JOIN League l ON m.league_id = l.id
JOIN Country c ON l.country_id = c.id
JOIN Team ht ON m.home_team_api_id = ht.team_api_id
JOIN Team at ON m.away_team_api_id = at.team_api_id
"""

df = pd.read_sql(query, conn)

# FECHA
df["date"] = pd.to_datetime(df["date"])

# RESULTADO
def get_result(row):
    if row["home_goals"] > row["away_goals"]:
        return 1
    elif row["home_goals"] < row["away_goals"]:
        return -1
    return 0

df["result"] = df.apply(get_result, axis=1)

# ODDS SIMULADAS
df["odds_home"] = 1.8
df["odds_draw"] = 3.2
df["odds_away"] = 2.5

df = df.dropna()

# GUARDAR
df.to_sql("historical_matches", engine, if_exists="replace", index=False)

print("✅ Datos listos:", len(df))