import pandas as pd
import joblib
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
from pathlib import Path

# ---------------------------
# 🔧 CONFIG
# ---------------------------
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

engine = create_engine(os.getenv("DB_URL"))

# ---------------------------
# 🤖 MODELO
# ---------------------------
model_path = Path(__file__).resolve().parent.parent / "model_real.pkl"
model = joblib.load(model_path)

# ---------------------------
# 📊 DATOS
# ---------------------------
df_features = pd.read_sql("SELECT * FROM features", engine)
df_odds = pd.read_sql("SELECT * FROM odds", engine)

# ---------------------------
# 🔥 NORMALIZACIÓN SEGURA
# ---------------------------
def normalize(name):
    if pd.isna(name):
        return name

    name = name.lower().strip()
    name = name.replace("fc", "").replace("afc", "").strip()

    mapping = {
        "brighton and hove albion": "brighton hove albion",
        "brighton hove albion": "brighton hove albion",

        "sunderland afc": "sunderland",
        "sunderland": "sunderland",

        "afc bournemouth": "bournemouth",
        "bournemouth": "bournemouth",

        "wolverhampton wanderers": "wolverhampton",
        "wolves": "wolverhampton",
        "wolverhampton": "wolverhampton",

        "tottenham hotspur": "tottenham",
        "tottenham": "tottenham",

        "manchester united": "manchester united",
        "manchester city": "manchester city",

        "west ham united": "west ham united",
        "newcastle united": "newcastle united",
        "leeds united": "leeds united",

        "nottingham forest": "nottingham forest",
        "crystal palace": "crystal palace",
        "aston villa": "aston villa",
        "everton": "everton",
        "fulham": "fulham",
        "arsenal": "arsenal",
        "chelsea": "chelsea",
        "liverpool": "liverpool",
        "brentford": "brentford",
        "burnley": "burnley"
    }

    return mapping.get(name, name)

# aplicar normalización
df_features["home_norm"] = df_features["home_team"].apply(normalize)
df_features["away_norm"] = df_features["away_team"].apply(normalize)

df_odds["home_norm"] = df_odds["home_team"].apply(normalize)
df_odds["away_norm"] = df_odds["away_team"].apply(normalize)

# ---------------------------
# 🔗 MATCH FLEXIBLE
# ---------------------------
rows = []

for _, f in df_features.iterrows():
    for _, o in df_odds.iterrows():

        if (
            f["home_norm"] == o["home_norm"] and
            f["away_norm"] == o["away_norm"]
        ) or (
            f["home_norm"] == o["away_norm"] and
            f["away_norm"] == o["home_norm"]
        ):

            rows.append({
                **f,
                "odds_home": o["odds_home"],
                "odds_draw": o["odds_draw"],
                "odds_away": o["odds_away"]
            })

df = pd.DataFrame(rows)

if len(df) == 0:
    print("\n❌ No hay coincidencias entre features y odds")
    exit()

# ---------------------------
# 🎯 FEATURES PARA MODELO
# ---------------------------
X = df[[
    "home_avg_goals",
    "home_avg_conceded",
    "home_win_rate",
    "away_avg_goals",
    "away_avg_conceded",
    "away_win_rate"
]]

# probabilidades
probs = model.predict_proba(X)

# ---------------------------
# 💰 CALCULAR VALUE
# ---------------------------
results = []

for i, row in df.iterrows():
    p_away = probs[i][0]
    p_draw = probs[i][1]
    p_home = probs[i][2]

    value_home = p_home * row["odds_home"] - 1
    value_draw = p_draw * row["odds_draw"] - 1
    value_away = p_away * row["odds_away"] - 1

    results.append({
        "home_team": row["home_team"],
        "away_team": row["away_team"],

        "p_home": p_home,
        "p_draw": p_draw,
        "p_away": p_away,

        "odds_home": row["odds_home"],
        "odds_draw": row["odds_draw"],
        "odds_away": row["odds_away"],

        "value_home": value_home,
        "value_draw": value_draw,
        "value_away": value_away
    })

value_df = pd.DataFrame(results)

# ---------------------------
# 🎯 GENERAR PICKS REALES
# ---------------------------
picks = []

for _, row in value_df.iterrows():

    values = {
        "HOME": row["value_home"],
        "DRAW": row["value_draw"],
        "AWAY": row["value_away"]
    }

    best_bet = max(values, key=values.get)
    best_value = values[best_bet]

    # 🔥 FILTRO PRINCIPAL
    if best_value <= 0.25:
        continue

    # evitar valores absurdos
    if best_value > 1.5:
        continue

    if best_bet == "HOME":
        odds = row["odds_home"]
        prob = row["p_home"]
    elif best_bet == "DRAW":
        odds = row["odds_draw"]
        prob = row["p_draw"]
    else:
        odds = row["odds_away"]
        prob = row["p_away"]

    # evitar probabilidades irreales
    if prob > 0.9:
        continue

    # evitar odds locas
    if odds > 5:
        continue

    stake = round(best_value * 10, 2)

    picks.append({
        "Partido": f"{row['home_team']} vs {row['away_team']}",
        "Apuesta": best_bet,
        "Cuota": round(odds, 2),
        "Probabilidad": round(prob, 3),
        "Valor": round(best_value, 3),
        "Stake": stake
    })

picks_df = pd.DataFrame(picks)

# ordenar por mejor valor
if len(picks_df) > 0:
    picks_df = picks_df.sort_values(by="Valor", ascending=False).head(5)

# ---------------------------
# 📢 RESULTADOS
# ---------------------------
print("\n🔥 PICKS REALES (APUESTAS):\n")

if len(picks_df) == 0:
    print("⚠️ No hay apuestas buenas hoy")
else:
    print(picks_df)

print("\nTotal picks:", len(picks_df))