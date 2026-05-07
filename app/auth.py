import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
from pathlib import Path

# ============================================
# ENV
# ============================================
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

engine = create_engine(os.getenv("DB_URL"))

# ============================================
# LOGIN
# ============================================
def login():

    st.sidebar.title("🔐 Login")

    username = st.sidebar.text_input(
        "Usuario"
    )

    password = st.sidebar.text_input(
        "Contraseña",
        type="password"
    )

    login_btn = st.sidebar.button(
        "Ingresar"
    )

    if login_btn:

        query = f"""
        SELECT *
        FROM users
        WHERE username = '{username}'
        AND password = '{password}'
        """

        user = pd.read_sql(query, engine)

        if len(user) > 0:

            st.session_state["logged"] = True

            st.session_state["role"] = user.iloc[0]["role"]

            st.session_state["username"] = username

            st.success("Login exitoso")

            st.rerun()

        else:

            st.error("Credenciales incorrectas")