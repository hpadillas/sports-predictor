import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
from pathlib import Path
import joblib

# =====================================================
# IMPORTS LOGIN
# =====================================================
from auth import login
from admin import admin_dashboard
from user_view import user_dashboard

# =====================================================
# CONFIG
# =====================================================
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

engine = create_engine(os.getenv("DB_URL"))

model = joblib.load(
    Path(__file__).resolve().parent.parent / "model_real.pkl"
)

st.set_page_config(
    page_title="Betting AI",
    layout="wide"
)

# =====================================================
# SESSION
# =====================================================
if "logged" not in st.session_state:
    st.session_state["logged"] = False

if "role" not in st.session_state:
    st.session_state["role"] = None

if "username" not in st.session_state:
    st.session_state["username"] = None

# =====================================================
# LOGIN
# =====================================================
if not st.session_state["logged"]:

    login()

    st.stop()

# =====================================================
# SIDEBAR USER INFO
# =====================================================
st.sidebar.success(
    f"👤 {st.session_state['username']}"
)

st.sidebar.info(
    f"🔑 Rol: {st.session_state['role']}"
)

# =====================================================
# LOGOUT
# =====================================================
if st.sidebar.button("Cerrar sesión"):

    st.session_state["logged"] = False
    st.session_state["role"] = None
    st.session_state["username"] = None

    st.rerun()

# =====================================================
# CSS PREMIUM LIGHT
# =====================================================
st.markdown("""
<style>

.block-container {
    padding-top: 2rem;
}

.card {

    background-color: #ffffff;

    padding: 22px;

    border-radius: 18px;

    margin-bottom: 20px;

    border: 1px solid #e2e8f0;

    box-shadow: 0px 4px 12px rgba(0,0,0,0.08);
}

.green {
    color: #16a34a;
    font-weight: bold;
}

.yellow {
    color: #ca8a04;
    font-weight: bold;
}

.red {
    color: #dc2626;
    font-weight: bold;
}

.big-font {

    font-size: 26px;

    font-weight: bold;

    color: #0f172a;
}

.small-gray {
    color: #64748b;
}

.metric {
    font-size: 18px;
    font-weight: bold;
}

hr {
    margin-top: 10px;
    margin-bottom: 10px;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# TITLE
# =====================================================
st.title("⚽ Betting AI - Predictor")

# =====================================================
# LOAD FUTURE MATCHES
# =====================================================
future_path = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "future_matches.csv"
)

df_future = pd.read_csv(future_path)

# =====================================================
# DATE FORMAT
# =====================================================
df_future["date"] = pd.to_datetime(
    df_future["date"]
).dt.date

# =====================================================
# SIDEBAR FILTERS
# =====================================================

# -------- LEAGUES --------
leagues = ["Todas"] + sorted(
    df_future["league"].unique().tolist()
)

selected_league = st.sidebar.selectbox(
    "🏆 Liga",
    leagues
)

if selected_league != "Todas":

    df_future = df_future[
        df_future["league"] == selected_league
    ]

# -------- DATES --------
available_dates = sorted(
    df_future["date"].unique()
)

selected_date = st.sidebar.date_input(
    "📅 Fecha",
    value=available_dates[0],
    min_value=min(available_dates),
    max_value=max(available_dates)
)

# FILTER DATE
df_future = df_future[
    df_future["date"] == selected_date
]

# =====================================================
# HISTORICAL DATA
# =====================================================
df_hist = pd.read_sql(
    "SELECT * FROM features_real",
    engine
)

# =====================================================
# TEAM STATS
# =====================================================
def get_team_stats(team):

    data = df_hist[
        (df_hist.home_team == team) |
        (df_hist.away_team == team)
    ].tail(5)

    if len(data) == 0:
        return [0] * 6

    return [

        data["home_avg_goals"].mean(),
        data["home_avg_conceded"].mean(),
        data["home_win_rate"].mean(),

        data["away_avg_goals"].mean(),
        data["away_avg_conceded"].mean(),
        data["away_win_rate"].mean(),
    ]

# =====================================================
# BUILD FEATURES
# =====================================================
rows = []

for _, match in df_future.iterrows():

    home_stats = get_team_stats(match["home_team"])
    away_stats = get_team_stats(match["away_team"])

    rows.append({

        "date": match["date"],
        "league": match["league"],

        "home_team": match["home_team"],
        "away_team": match["away_team"],

        "home_avg_goals": home_stats[0],
        "home_avg_conceded": home_stats[1],
        "home_win_rate": home_stats[2],

        "away_avg_goals": away_stats[3],
        "away_avg_conceded": away_stats[4],
        "away_win_rate": away_stats[5],

        "home_elo": 1500,
        "away_elo": 1500,
        "elo_diff": 0
    })

df = pd.DataFrame(rows)

# =====================================================
# EMPTY CHECK
# =====================================================
if len(df) == 0:

    st.warning(
        "No hay partidos disponibles para esa fecha."
    )

    st.stop()

# =====================================================
# MODEL FEATURES
# =====================================================
features = [

    "home_avg_goals",
    "home_avg_conceded",
    "home_win_rate",

    "away_avg_goals",
    "away_avg_conceded",
    "away_win_rate",

    "home_elo",
    "away_elo",
    "elo_diff"
]

# =====================================================
# PREDICT
# =====================================================
probs = model.predict_proba(df[features])

df["p_away"] = probs[:, 0]
df["p_draw"] = probs[:, 1]
df["p_home"] = probs[:, 2]

# =====================================================
# WINNER
# =====================================================
def get_prediction(row):

    probs = {

        row["home_team"]: row["p_home"],

        "Empate": row["p_draw"],

        row["away_team"]: row["p_away"]
    }

    winner = max(probs, key=probs.get)

    confidence = probs[winner]

    return winner, confidence

df[["winner", "confidence"]] = df.apply(
    lambda r: pd.Series(get_prediction(r)),
    axis=1
)

# =====================================================
# CONFIDENCE COLOR
# =====================================================
def confidence_color(value):

    if value >= 0.70:
        return "green"

    elif value >= 0.55:
        return "yellow"

    return "red"

# =====================================================
# TOP PICKS
# =====================================================
st.subheader("🔥 Picks del Día")

top_matches = df.sort_values(
    "confidence",
    ascending=False
).head(5)

for _, row in top_matches.iterrows():

    color = confidence_color(row["confidence"])

    st.markdown(f"""
    <div class="card">

    <div class="big-font">
    ⚽ {row['home_team']} vs {row['away_team']}
    </div>

    <br>

    📅 {row['date']} <br>
    🏆 {row['league']} <br><br>

    🧠 <b>Ganador probable:</b> {row['winner']} <br><br>

    <span class="{color} metric">
    📊 Confianza: {round(row['confidence'] * 100, 2)}%
    </span>

    <hr>

    <div class="small-gray">

    🏠 Local:
    {round(row['p_home'] * 100, 1)}%
    &nbsp;&nbsp;&nbsp;

    🤝 Empate:
    {round(row['p_draw'] * 100, 1)}%
    &nbsp;&nbsp;&nbsp;

    ✈️ Visitante:
    {round(row['p_away'] * 100, 1)}%

    </div>

    </div>
    """, unsafe_allow_html=True)

# =====================================================
# TABLE ALL MATCHES
# =====================================================
st.subheader("📋 Todos los Partidos")

table_df = df[[
    "date",
    "league",
    "home_team",
    "away_team",
    "winner",
    "confidence"
]].copy()

table_df.columns = [

    "Fecha",
    "Liga",
    "Local",
    "Visitante",
    "Ganador",
    "Confianza"
]

table_df["Confianza"] = (
    table_df["Confianza"] * 100
).round(2)

st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True
)

# =====================================================
# RECOMMENDED PICKS
# =====================================================
recommended = table_df[
    table_df["Confianza"] >= 55
].sort_values(
    "Confianza",
    ascending=False
)

st.subheader("🔥 Partidos Recomendados")

if len(recommended) > 0:

    st.dataframe(
        recommended,
        use_container_width=True,
        hide_index=True
    )

else:

    st.warning(
        "No hay picks fuertes hoy."
    )

# =====================================================
# ROLE PANELS
# =====================================================
if st.session_state["role"] == "admin":

    admin_dashboard(df)

else:

    user_dashboard()