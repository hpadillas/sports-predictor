import pandas as pd
from sqlalchemy import create_engine
from xgboost import XGBClassifier
import joblib
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

engine = create_engine(os.getenv("DB_URL"))

df = pd.read_sql("SELECT * FROM features_real", engine)

df["result"] = df["result"].map({-1: 0, 0: 1, 1: 2})

features = [
    "home_avg_goals","home_avg_conceded","home_win_rate",
    "away_avg_goals","away_avg_conceded","away_win_rate",
    "home_elo","away_elo","elo_diff"
]

X = df[features]
y = df["result"]

model = XGBClassifier(
    n_estimators=300,
    max_depth=5,
    learning_rate=0.05,
    eval_metric="mlogloss"
)

model.fit(X, y)

joblib.dump(model, "model_real.pkl")

print("✅ Modelo listo")