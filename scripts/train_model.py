import pandas as pd
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib
import os
from dotenv import load_dotenv
from pathlib import Path

# cargar env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

engine = create_engine(os.getenv("DB_URL"))

# cargar datos
df = pd.read_sql("SELECT * FROM matches_clean", engine)

# features simples
X = df[["home_goals", "away_goals"]]
y = df["result"]

# dividir datos
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# modelo
model = RandomForestClassifier()
model.fit(X_train, y_train)

# guardar modelo
joblib.dump(model, "model.pkl")

print("Modelo entrenado")