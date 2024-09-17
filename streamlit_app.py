import streamlit as st
from workout import workout_page  # Import workout page
from profile import profile_page  # Import profile page
from login import login_page  # Import login page

st.set_page_config(layout="wide", page_icon=":material/fitness_center:", page_title="Smart Fitness Trainer")

# Ensure session state key initialization
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if "current_page" not in st.session_state:
    st.session_state["current_page"] = "workout"  # Default to workout page

# Navigation logic
if st.session_state.get("authenticated"):
    # Switch between pages based on session state
    if st.session_state['current_page'] == 'workout':
        workout_page()
    elif st.session_state['current_page'] == 'profile':
        profile_page()
else:
    login_page()
