import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
from pathlib import Path
from xgboost import XGBClassifier
from sklearn.calibration import CalibratedClassifierCV

# ---------------------------
# CONFIG
# ---------------------------
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

engine = create_engine(os.getenv("DB_URL"))

# ---------------------------
# DATA
# ---------------------------
df = pd.read_sql("SELECT * FROM features_real", engine)

df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")

# mapear resultado
df["result"] = df["result"].map({
    -1: 0,
     0: 1,
     1: 2
})

# ---------------------------
# FEATURES (SIN MERCADO)
# ---------------------------
features = [
    "home_avg_goals","home_avg_conceded","home_win_rate",
    "away_avg_goals","away_avg_conceded","away_win_rate",
    "home_elo","away_elo","elo_diff"
]

# ---------------------------
# PARAMETROS
# ---------------------------
initial_bank = 1000
bank = initial_bank
stake = 5

start = int(len(df) * 0.5)
step = int(len(df) * 0.1)

bets = 0
wins = 0

i = start

# ---------------------------
# WALK-FORWARD
# ---------------------------
while i + step < len(df):

    train = df.iloc[:i]
    test = df.iloc[i:i+step]

    X_train = train[features]
    y_train = train["result"]
    X_test = test[features]

    # modelo + calibración
    base = XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        eval_metric="mlogloss"
    )

    model = CalibratedClassifierCV(base, method="isotonic", cv=3)
    model.fit(X_train, y_train)

    probs = model.predict_proba(X_test)

    # ---------------------------
    # GENERAR CANDIDATOS
    # ---------------------------
    candidates = []

    for j, row in test.reset_index(drop=True).iterrows():

        p_away, p_draw, p_home = probs[j]

        imp_home = row["imp_home"]
        imp_away = row["imp_away"]

        oh = row["odds_home"]
        oa = row["odds_away"]

        # edge vs mercado
        edge_home = p_home - imp_home
        edge_away = p_away - imp_away

        # solo apuestas fuertes
        if edge_home > 0.08:
            value = p_home * oh - 1
            candidates.append({
                "value": value,
                "bet": 2,
                "row": row
            })

        elif edge_away > 0.08:
            value = p_away * oa - 1
            candidates.append({
                "value": value,
                "bet": 0,
                "row": row
            })

    # ---------------------------
    # TOP PICKS (CLAVE)
    # ---------------------------
    candidates = sorted(candidates, key=lambda x: x["value"], reverse=True)[:5]

    # ---------------------------
    # SIMULACIÓN
    # ---------------------------
    for c in candidates:

        bet = c["bet"]
        row = c["row"]

        bets += 1
        real = row["result"]

        if bet == real:
            wins += 1
            if bet == 2:
                bank += stake * (row["odds_home"] - 1)
            else:
                bank += stake * (row["odds_away"] - 1)
        else:
            bank -= stake

    i += step

# ---------------------------
# RESULTADOS
# ---------------------------
roi = (bank - initial_bank) / initial_bank * 100

print("\n📊 BACKTEST CONSERVADOR FINAL:\n")
print(f"Banca inicial: {initial_bank}")
print(f"Banca final: {round(bank,2)}")
print(f"Apuestas: {bets}")
print(f"Aciertos: {wins}")
print(f"ROI: {round(roi,2)}%")