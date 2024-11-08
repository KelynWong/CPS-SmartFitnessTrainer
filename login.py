import streamlit as st
from st_login_form import login_form

def login_page():
    # Define the login form
    client = login_form(
        title="Smart Fitness Trainer",
        user_tablename="user",
        username_col="username",
        password_col="password",
        constrain_password=True,
        create_title="Sign up for a new account",
        login_title="Login to your account",
        allow_guest=False,
        allow_create=True,
        create_username_label="Choose a unique username",
        create_password_label="Set your password",
        create_submit_label="Register",
        login_username_label="Your username",
        login_password_label="Your password",
        login_submit_label="Log in",
        login_error_message="Invalid username or password",
    )

    # Set authentication state
    if st.session_state.get("authenticated"):
        st.write(f"Hello, {st.session_state['username']}! You're logged in.")
        st.rerun()
    else:
        st.write("Please log in to continue.")
