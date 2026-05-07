import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
from pathlib import Path

# =====================================================
# ENV
# =====================================================
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

engine = create_engine(os.getenv("DB_URL"))

# =====================================================
# ADMIN DASHBOARD
# =====================================================
def admin_dashboard(df):

    st.header("👑 Panel Administrador")

    # =================================================
    # METRICS
    # =================================================
    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Total Partidos",
            len(df)
        )

    with col2:

        avg_conf = round(
            df["confidence"].mean() * 100,
            2
        )

        st.metric(
            "Confianza Promedio",
            f"{avg_conf}%"
        )

    st.divider()

    # =================================================
    # ADMIN MENU
    # =================================================
    admin_option = st.radio(
        "⚙️ Administración",
        [
            "Crear Usuario",
            "Usuarios"
        ],
        horizontal=True
    )

    # =================================================
    # CREATE USER
    # =================================================
    if admin_option == "Crear Usuario":

        st.subheader("➕ Crear Nuevo Usuario")

        with st.form("create_user_form"):

            new_username = st.text_input(
                "Usuario"
            )

            new_password = st.text_input(
                "Contraseña",
                type="password"
            )

            new_role = st.selectbox(
                "Rol",
                ["user", "admin"]
            )

            submitted = st.form_submit_button(
                "Crear Usuario"
            )

            if submitted:

                if (
                    new_username == ""
                    or new_password == ""
                ):

                    st.warning(
                        "Completa todos los campos"
                    )

                else:

                    # =================================
                    # CHECK EXISTING USER
                    # =================================
                    query = text("""
                    SELECT *
                    FROM users
                    WHERE username = :username
                    """)

                    existing = pd.read_sql(
                        query,
                        engine,
                        params={
                            "username": new_username
                        }
                    )

                    if len(existing) > 0:

                        st.error(
                            "Ese usuario ya existe"
                        )

                    else:

                        insert_query = text("""
                        INSERT INTO users (
                            username,
                            password,
                            role
                        )
                        VALUES (
                            :username,
                            :password,
                            :role
                        )
                        """)

                        with engine.begin() as conn:

                            conn.execute(
                                insert_query,
                                {
                                    "username": new_username,
                                    "password": new_password,
                                    "role": new_role
                                }
                            )

                        st.success(
                            "✅ Usuario creado correctamente"
                        )

    # =================================================
    # USERS CRUD
    # =================================================
    elif admin_option == "Usuarios":

        st.subheader("👥 Gestión de Usuarios")

        users = pd.read_sql(
            "SELECT id, username, role FROM users ORDER BY id",
            engine
        )

        if len(users) == 0:

            st.warning(
                "No hay usuarios registrados"
            )

        else:

            for _, user in users.iterrows():

                with st.expander(
                    f"👤 {user['username']} ({user['role']})"
                ):

                    col1, col2 = st.columns(2)

                    # =================================
                    # UPDATE USER
                    # =================================
                    with col1:

                        st.markdown("### ✏️ Modificar")

                        updated_username = st.text_input(
                            "Usuario",
                            value=user["username"],
                            key=f"username_{user['id']}"
                        )

                        updated_password = st.text_input(
                            "Nueva contraseña",
                            type="password",
                            key=f"password_{user['id']}"
                        )

                        updated_role = st.selectbox(
                            "Rol",
                            ["user", "admin"],
                            index=0 if user["role"] == "user" else 1,
                            key=f"role_{user['id']}"
                        )

                        if st.button(
                            "Guardar cambios",
                            key=f"update_{user['id']}"
                        ):

                            # =========================
                            # UPDATE WITH PASSWORD
                            # =========================
                            if updated_password != "":

                                update_query = text("""
                                UPDATE users
                                SET username = :username,
                                    password = :password,
                                    role = :role
                                WHERE id = :id
                                """)

                                params = {
                                    "username": updated_username,
                                    "password": updated_password,
                                    "role": updated_role,
                                    "id": int(user["id"])
                                }

                            # =========================
                            # UPDATE WITHOUT PASSWORD
                            # =========================
                            else:

                                update_query = text("""
                                UPDATE users
                                SET username = :username,
                                    role = :role
                                WHERE id = :id
                                """)

                                params = {
                                    "username": updated_username,
                                    "role": updated_role,
                                    "id": int(user["id"])
                                }

                            with engine.begin() as conn:

                                conn.execute(
                                    update_query,
                                    params
                                )

                            st.success(
                                "✅ Usuario actualizado"
                            )

                            st.rerun()

                    # =================================
                    # DELETE USER
                    # =================================
                    with col2:

                        st.markdown("### 🗑️ Eliminar")

                        st.warning(
                            "Esta acción no se puede deshacer"
                        )

                        if st.button(
                            "Eliminar usuario",
                            key=f"delete_{user['id']}"
                        ):

                            delete_query = text("""
                            DELETE FROM users
                            WHERE id = :id
                            """)

                            with engine.begin() as conn:

                                conn.execute(
                                    delete_query,
                                    {
                                        "id": int(user["id"])
                                    }
                                )

                            st.success(
                                "✅ Usuario eliminado"
                            )

                            st.rerun()