import streamlit as st

# Define your pages
login_page = st.Page("login.py", title="Login", icon=":material/login:")
workout_page = st.Page("workout.py", title="Workout Dashboard", icon=":material/fitness_center:")

# Navigation for the app
if "authenticated" in st.session_state and st.session_state.authenticated:
    pg = st.navigation([login_page, workout_page])
else:
    pg = st.navigation([login_page])

st.set_page_config(page_title="Smart Fitness Trainer", page_icon=":material/sports:")

pg.run()
