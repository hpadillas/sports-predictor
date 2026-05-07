import pandas as pd
import joblib
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
from pathlib import Path
from xgboost import XGBClassifier

# --- config ---
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
engine = create_engine(os.getenv("DB_URL"))

# --- data ---
df = pd.read_sql("SELECT * FROM features", engine)
df["result"] = df["result"].map({-1: 0, 0: 1, 1: 2})

if "date" in df.columns:
    df = df.sort_values("date")

cols = [
    "home_avg_goals","home_avg_conceded","home_win_rate",
    "away_avg_goals","away_avg_conceded","away_win_rate"
]

# --- params ---
initial_bank = 1000
stake = 10
threshold = 0.25
window_train = int(len(df) * 0.5)   # ventana inicial
step = int(len(df) * 0.1)           # avance

bank = initial_bank
total_bets = 0
total_wins = 0

i = window_train
while i + step <= len(df):
    train_df = df.iloc[:i]
    test_df  = df.iloc[i:i+step]

    X_train = train_df[cols]
    y_train = train_df["result"]

    X_test  = test_df[cols]

    # re-entrena en cada ventana (más realista)
    model = XGBClassifier(
        n_estimators=200, max_depth=4, learning_rate=0.05,
        eval_metric="mlogloss"
    )
    model.fit(X_train, y_train)

    probs = model.predict_proba(X_test)

    for j, row in test_df.reset_index(drop=True).iterrows():
        p_away, p_draw, p_home = probs[j]

        # ⚠️ sustituye por odds históricas reales cuando las tengas
        odds_home, odds_draw, odds_away = 1.8, 3.2, 2.8

        v_home = p_home * odds_home - 1
        v_draw = p_draw * odds_draw - 1
        v_away = p_away * odds_away - 1

        values = {2: v_home, 1: v_draw, 0: v_away}
        bet = max(values, key=values.get)
        v   = values[bet]

        if v <= threshold:
            continue

        total_bets += 1
        real = row["result"]

        if bet == real:
            total_wins += 1
            if bet == 2:
                bank += stake * (odds_home - 1)
            elif bet == 1:
                bank += stake * (odds_draw - 1)
            else:
                bank += stake * (odds_away - 1)
        else:
            bank -= stake

    i += step

roi = (bank - initial_bank) / initial_bank * 100

print("\n📊 WALK-FORWARD BACKTEST:\n")
print(f"Banca inicial: {initial_bank}")
print(f"Banca final: {round(bank,2)}")
print(f"Apuestas: {total_bets}")
print(f"Aciertos: {total_wins}")
print(f"ROI: {round(roi,2)}%")