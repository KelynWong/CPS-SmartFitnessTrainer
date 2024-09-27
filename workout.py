import streamlit as st
import supabase
import pandas as pd
import plotly.express as px
import requests
import time
from datetime import datetime
import pytz

def workout_page():
    # Initialize Supabase client
    supabase_client = supabase.create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

    # Ensure 'startDT' is initialized in session state
    if 'startDT' not in st.session_state:
        st.session_state['startDT'] = None

    col1, col2, col3 = st.columns([4,1,1])
    with col1:
        st.title("Workout Dashboard")

    with col2:
        # Add a button to navigate to the profile page
        st.write(" ")
        profile_button = st.button("Go to profile")
        if profile_button:
            st.session_state['current_page'] = 'profile'
            st.rerun()

    with col3:
        # Add a button to logout
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.rerun()

    # Fetch workouts from Supabase
    workout_response = supabase_client.table('workouts').select('*').execute()
    if workout_response.data:
        workouts = [workout['name'] for workout in workout_response.data]

    # Use st.columns to arrange components side by side
    col1, col2, col3, col4 = st.columns([3, 3, 1, 1])

    with col1:
        selected_workout = st.selectbox("Select a Workout", workouts)

    with col2:
        ip_address = st.text_input("Enter Server Address")

    # Initialize the workout status if it's not in session state
    if "workout_running" not in st.session_state:
        st.session_state['workout_running'] = False

    # Separate buttons for Start and Stop Workout
    with col3:
        st.write(" ")
        st.write(" ")
        start_button = st.button("Start Workout", disabled=not ip_address)
        
    with col4:
        st.write(" ")
        st.write(" ")
        stop_button = st.button("Stop Workout")

    # Logic to handle the Start Workout button click
    if start_button and ip_address:
        try:
            st.write("Starting workout...")

            # Capture the current datetime when the workout starts and store it in session state
            tz = pytz.timezone('Asia/Singapore')  # Replace with the desired timezone

            # Get the current time in the specified timezone
            current_time = datetime.now(tz)

            # Format the time as a string with timezone information
            formatted_time = current_time.strftime("%Y-%m-%dT%H:%M:%S%z")  # %z adds timezone offset
            st.session_state['startDT'] = formatted_time
            
            # Prepare the payload
            payload = {
                "username": st.session_state['username'],  # Get username from session state
                "workout": selected_workout,               # Selected workout from the dropdown
                "startDT": st.session_state['startDT']     # Start datetime stored in session state
            }

            # Make the POST request to the server with the workout data
            api_url = f"https://{ip_address}.ngrok-free.app/start"
            response = requests.post(api_url, json=payload)

            if response.status_code == 200:
                result = response.json()
                watch_url = result.get("watch_url")

                # Display the returned watch_url
                if watch_url:
                    st.write("Stream started successfully! Here is your workout video:")
                    st.video(watch_url, autoplay=True)
                    st.session_state['workout_running'] = True
                else:
                    st.error("Failed to retrieve the watch URL from the response.")
            else:
                st.error(f"Failed to start the workout stream. Status code: {response.status_code}")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")


    # Logic to handle the Stop Workout button click
    if stop_button and ip_address:
        try:
            st.write("Stopping workout...")

            # Check if startDT is set in session state before proceeding
            if st.session_state['startDT'] is None:
                st.error("Start time is not set. Please start the workout first.")
            else:
                # Prepare the payload using the startDT stored in session state
                payload = {
                    "username": st.session_state['username'],  # Username from session state
                    "workout": selected_workout,               # Selected workout from the dropdown
                    "startDT": st.session_state['startDT']     # Use the startDT from session state
                }

                # Set headers to specify the content type
                headers = {
                    "Content-Type": "application/json"  
                }

                # Make the POST request to the server to stop the workout
                api_url = f"https://{ip_address}.ngrok-free.app/stop"
                response = requests.post(api_url, json=payload, headers=headers)

                if response.status_code == 200:
                    st.write("Workout stopped successfully.")
                    st.session_state['workout_running'] = False
                else:
                    st.error(f"Failed to stop the workout stream. Status code: {response.status_code}")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

    # Fetch user workout data from 'userWorkouts' table where username matches session state
    username = st.session_state['username']
    user_workout_response = supabase_client.table('userWorkouts').select('*').eq('username', username).execute()

    if user_workout_response.data:
        st.header("Workout Historical Data & A")
        df = pd.DataFrame(user_workout_response.data)

        st.subheader(f"Workout Data for {username}")
        st.dataframe(df)

        df['startDT'] = pd.to_datetime(df['startDT'])
        df['endDT'] = pd.to_datetime(df['endDT'])

        st.subheader(f"Workout Analysis")
        col1, col2 = st.columns(2)
        with col1:
            fig_reps = px.line(df, x='startDT', y='reps', title='Total Reps Over Time', markers=True)
            st.plotly_chart(fig_reps, use_container_width=True)

        with col2:
            df['workout_date'] = df['startDT'].dt.date
            workout_count = df.groupby('workout_date').size().reset_index(name='Workout Count')
            fig_workout_freq = px.bar(workout_count, x='workout_date', y='Workout Count', title='Workout Frequency Over Time')
            st.plotly_chart(fig_workout_freq, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            avg_reps_per_workout = df.groupby('workout')['reps'].mean().reset_index()
            fig_avg_reps = px.bar(avg_reps_per_workout, x='workout', y='reps', title='Average Reps per Workout')
            st.plotly_chart(fig_avg_reps, use_container_width=True)

        with col2:
            df['duration'] = (df['endDT'] - df['startDT']).dt.total_seconds() / 60
            fig_duration = px.bar(df, x='workout', y='duration', title='Duration of Workouts', text='duration')
            fig_duration.update_traces(texttemplate='%{text:.2f} min', textposition='outside')
            st.plotly_chart(fig_duration, use_container_width=True)
    else:
        st.warning("No workout data found for the current user.")
