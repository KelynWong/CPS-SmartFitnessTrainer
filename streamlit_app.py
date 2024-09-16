import streamlit as st
from login import login_page  # Import the function from login.py
from workout import workout_page  # Import the function from workout.py

# Ensure session state key initialization
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# Navigation logic
if st.session_state.get("authenticated"):
    workout_page()  # If authenticated, show workout page
else:
    login_page()  # If not authenticated, show login page
