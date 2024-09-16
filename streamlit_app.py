import streamlit as st

# Define your pages
login_page = st.Page("login.py", title="Login", icon=":material/login:")
workout_page = st.Page("workout.py", title="Workout Dashboard", icon=":material/fitness_center:")

# Navigation for the app
if "authenticated" in st.session_state and st.session_state.authenticated:
    # If the user is authenticated, make both login and workout pages available
    pg = st.navigation([login_page, workout_page], position="hidden")
else:
    # If the user is not authenticated, only the login page is available
    pg = st.navigation([login_page], position="hidden")

st.set_page_config(page_title="Smart Fitness Trainer", page_icon=":material/sports:")

pg.run()
