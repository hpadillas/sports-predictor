import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
from pathlib import Path

# cargar env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

engine = create_engine(os.getenv("DB_URL"))

# cargar datos
df = pd.read_sql("SELECT * FROM matches", engine)

# eliminar partidos sin resultado
df = df.dropna(subset=["home_goals", "away_goals"])

# crear variable objetivo
def get_result(row):
    if row["home_goals"] > row["away_goals"]:
        return 1   # gana local
    elif row["home_goals"] < row["away_goals"]:
        return -1  # gana visitante
    else:
        return 0   # empate

df["result"] = df.apply(get_result, axis=1)

# guardar dataset limpio
df.to_sql("matches_clean", engine, if_exists="replace", index=False)

print("Datos procesados:", len(df))