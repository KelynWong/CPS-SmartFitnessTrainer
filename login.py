import streamlit as st
from st_login_form import login_form

# Define the login form
client = login_form(
    title="Smart Fitness Trainer",  # Title of the form
    user_tablename="user",  # Custom table name in the database for storing user info
    username_col="username",  # Column name in the table for usernames
    password_col="password",  # Column name in the table for passwords
    constrain_password=True,  # Enforce password constraints
    create_title="Sign up for a new account",
    login_title="Login to your account",
    allow_guest=False,  # Allow guest login
    allow_create=True,  # Allow creating new accounts
    # guest_title="Continue as guest",
    create_username_label="Choose a unique username",
    create_password_label="Set your password",
    create_submit_label="Register",
    create_success_message="Account created successfully!",
    login_username_label="Your username",
    login_password_label="Your password",
    login_submit_label="Log in",
    login_success_message="Welcome back to Smart Fitness Tracker!",
    login_error_message="Invalid username or password",
)

# Set authentication state
if st.session_state.get("authenticated"):
    st.write(f"Hello, {st.session_state['username']}! You're logged in.")

st.write("Please log in to continue.")
