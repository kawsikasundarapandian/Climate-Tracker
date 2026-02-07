import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import plotly.express as px
from sklearn.linear_model import LinearRegression
st.set_page_config(page_title="Smart Climate Impact Tracker", layout="wide")
conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users(
    username TEXT PRIMARY KEY,
    password TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS emissions(
    username TEXT,
    total_emission REAL
)
""")

conn.commit()
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
language = st.sidebar.selectbox("🌐 Language", ["English", "Tamil"])
theme = st.sidebar.selectbox("🎨 Theme", ["Light", "Dark"])

def translate(en, ta):
    return en if language == "English" else ta
if theme == "Dark":
    st.markdown("""
        <style>
        .stApp {
            background-color: #0E1117;
            color: white;
        }
        section[data-testid="stSidebar"] {
            background-color: #111827;
        }
        </style>
    """, unsafe_allow_html=True)
st.title(translate("🌱 Smart Climate Impact Tracker",
                   "🌱 ஸ்மார்ட் காலநிலை தாக்க கண்காணிப்பு"))


if not st.session_state.logged_in:

    menu = st.sidebar.selectbox("Menu", ["Login", "Register"])
    if menu == "Register":

        st.subheader("Create Account")

        new_user = st.text_input("Username")
        new_pass = st.text_input("Password", type="password")

        if st.button("Register"):
            try:
                c.execute("INSERT INTO users VALUES (?,?)", (new_user, new_pass))
                conn.commit()
                st.success("Account Created Successfully!")
            except sqlite3.IntegrityError:
                st.error("Username already exists!")
    elif menu == "Login":

        st.subheader("Login")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):

            c.execute("SELECT * FROM users WHERE username=? AND password=?",
                      (username, password))
            data = c.fetchone()

            if data:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Login Successful!")
                st.rerun()
            else:
                st.error("Invalid Credentials")
else:

    username = st.session_state.username

    st.sidebar.success(f"Logged in as {username}")

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()
    EMISSION_FACTORS = {
        "electricity": 0.82,
        "petrol": 2.31,
        "food": 0.5
    }

    st.subheader("Enter Monthly Data")

    col1, col2, col3 = st.columns(3)

    with col1:
        electricity = st.number_input("Electricity (kWh)", 0)

    with col2:
        petrol = st.number_input("Petrol (Liters)", 0)

    with col3:
        food = st.number_input("Food Expense (Rs)", 0)

    electricity_emission = electricity * EMISSION_FACTORS["electricity"]
    petrol_emission = petrol * EMISSION_FACTORS["petrol"]
    food_emission = (food / 100) * EMISSION_FACTORS["food"]

    total = electricity_emission + petrol_emission + food_emission

    if st.button("Calculate Emission"):

        st.metric("Total Carbon Emission (kg CO2)", round(total, 2))
        c.execute("INSERT INTO emissions VALUES (?,?)", (username, total))
        conn.commit()
        score = max(0, 100 - (total / 500 * 100))
        st.subheader("Sustainability Score")
        st.progress(int(score))
        st.subheader("AI Suggestions")

        if electricity_emission > 100:
            st.write("⚡ Use energy-efficient appliances.")
        if petrol_emission > 100:
            st.write("🚗 Try public transport.")
        if food_emission > 50:
            st.write("🥗 Reduce food waste.")
        if total < 150:
            st.success("🌍 Excellent! You are eco-friendly!")
        df = pd.DataFrame({
            "Category": ["Electricity", "Petrol", "Food"],
            "Emission": [electricity_emission,
                         petrol_emission,
                         food_emission]
        })

        fig = px.pie(df, names="Category", values="Emission")
        st.plotly_chart(fig, use_container_width=True)
        st.subheader("🏆 Leaderboard")

        leaderboard = pd.read_sql_query(
            "SELECT username, MIN(total_emission) as emission \
             FROM emissions GROUP BY username ORDER BY emission ASC",
            conn
        )

        st.dataframe(leaderboard)
        st.subheader("📈 AI Future Prediction")

        user_data = pd.read_sql_query(
            "SELECT total_emission FROM emissions WHERE username=?",
            conn,
            params=(username,)
        )

        if len(user_data) > 1:
            X = np.arange(len(user_data)).reshape(-1, 1)
            y = user_data["total_emission"]

            model = LinearRegression()
            model.fit(X, y)

            next_month = model.predict([[len(user_data)]])
            st.write("Predicted Next Month Emission:",
                     round(next_month[0], 2))
        else:
            st.info("Need at least 2 months data for prediction.")
