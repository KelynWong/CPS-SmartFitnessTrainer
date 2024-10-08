import streamlit as st
import supabase
import pandas as pd
import plotly.express as px
import requests
import time
from datetime import datetime
import pytz

# Function to calculate calories burned using the formula based on gender
def calculate_calories_burned(gender, duration, heart_rate, weight, age):
    if gender == "Female":
        return duration * ((0.4472 * heart_rate - 0.1263 * weight + 0.074 * age - 20.4022) / 4.184)
    elif gender == "Male":
        return duration * ((0.6309 * heart_rate + 0.1988 * weight + 0.2017 * age - 55.0969) / 4.184)
    else:
        return 0  # Return 0 if gender is not valid

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
        st.write(" ")
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
            
            # Set headers to specify the content type
            headers = {
                "Content-Type": "application/json"  
            }
            
            # Prepare the payload
            payload = {
                "username": st.session_state['username'],  # Get username from session state
                "workout": selected_workout,               # Selected workout from the dropdown
                "startDT": st.session_state['startDT']     # Start datetime stored in session state
            }

            # Make the POST request to the server with the workout data
            api_url = f"https://{ip_address}.ngrok-free.app/start"
            response = requests.post(api_url, json=payload, headers=headers)

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

    st.divider()

    # Fetch user data
    username = st.session_state['username']

    # Fetch user workout data by username
    user_workout_response = supabase_client.table('userWorkouts').select('*').eq('username', username).execute()

    # Extract workout_id from the fetched workout data
    workout_ids = [workout['workout_id'] for workout in user_workout_response.data]

    # Fetch health data linked to the workout_ids
    user_health_response = supabase_client.table('userWorkoutHealth').select('*').in_('workout_id', workout_ids).execute()

    # Fetch user data by username
    user_response = supabase_client.table('user').select('*').eq('username', username).execute()

    # Ensure there is workout data
    if user_workout_response.data and user_response.data:
        st.header("Workout Historical Data & Analytics")
        
        # Convert data to DataFrames
        df_workout = pd.DataFrame(user_workout_response.data)
        df_health = pd.DataFrame(user_health_response.data)
        df_user = pd.DataFrame(user_response.data).iloc[0]  # Fetch the first user record (assuming one user)

        # Display User Goals and Profile Info
        st.subheader(f"User Profile for {username}")
        col1, col2 = st.columns(2)
        with col1:
            st.image(df_user['profilePicture'], width=150, caption=f"{df_user['age']} years old, {df_user['weight']} kg, {df_user['gender']}")
        with col2:
            st.metric(label="Calories Burn Goal (Daily)", value=df_user['caloriesBurnPerDay'] or 'Not Set')
            st.metric(label="Workout Duration Goal (Daily)", value=f"{df_user['workoutDurationPerDay']} mins" if df_user['workoutDurationPerDay'] else 'Not Set')
            st.metric(label="Workout Frequency Goal (Weekly)", value=f"{df_user['workoutFrequencyPerWeek']} sessions" if df_user['workoutFrequencyPerWeek'] else 'Not Set')

        # Convert dates to datetime
        df_workout['startDT'] = pd.to_datetime(df_workout['startDT'])
        df_workout['endDT'] = pd.to_datetime(df_workout['endDT'])

        # Calculate duration and calories burned
        df_workout['duration'] = (df_workout['endDT'] - df_workout['startDT']).dt.total_seconds() / 60
        
        # Assuming the health data contains heart rates during the workout
        if not df_health.empty:
            # Group health data by workout_id and get average heart rate for each workout
            avg_heart_rate = df_health.groupby('workout_id')['heartbeat'].mean().reset_index()
            df_workout = df_workout.merge(avg_heart_rate, on='workout_id', how='left')  # Join with workout data
        
        # Calculate calories burned for each workout
        df_workout['caloriesBurned'] = df_workout.apply(
            lambda row: calculate_calories_burned(df_user['gender'], row['duration'], row['heartbeat'], df_user['weight'], df_user['age']),
            axis=1
        )

        # Display workout data
        st.subheader(f"Workout Data for {username}")
        st.dataframe(df_workout[['startDT', 'endDT', 'workout', 'reps', 'heartbeat', 'duration', 'caloriesBurned']])

        # Workout Analysis
        st.subheader("Workout Analysis")
        col1, col2 = st.columns(2)
        with col1:
            fig_reps = px.line(df_workout, x='startDT', y='reps', title='Total Reps Over Time', markers=True)
            st.plotly_chart(fig_reps, use_container_width=True)
        
        with col2:
            df_workout['workout_date'] = df_workout['startDT'].dt.date
            workout_count = df_workout.groupby('workout_date').size().reset_index(name='Workout Count')
            fig_workout_freq = px.bar(workout_count, x='workout_date', y='Workout Count', title='Workout Frequency Over Time')
            st.plotly_chart(fig_workout_freq, use_container_width=True)

        # Average reps per workout type
        col1, col2 = st.columns(2)
        with col1:
            avg_reps_per_workout = df_workout.groupby('workout')['reps'].mean().reset_index()
            fig_avg_reps = px.bar(avg_reps_per_workout, x='workout', y='reps', title='Average Reps per Workout')
            st.plotly_chart(fig_avg_reps, use_container_width=True)

        with col2:
            fig_duration = px.bar(df_workout, x='workout', y='duration', title='Duration of Workouts', text='duration')
            fig_duration.update_traces(texttemplate='%{text:.2f} min', textposition='outside')
            st.plotly_chart(fig_duration, use_container_width=True)

        # Calories burned section
        st.subheader("Calories Burned Per Workout")
        st.dataframe(df_workout[['workout', 'duration', 'heartbeat', 'caloriesBurned']])

    else:
        st.warning("No workout data found for the current user.")

