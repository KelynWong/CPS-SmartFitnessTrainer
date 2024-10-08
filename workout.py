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

    if user_workout_response.data and user_response.data:
        st.header("Workout Historical Data & Analytics")

        # Load data into DataFrame
        df_workouts = pd.DataFrame(user_workout_response.data)
        df_health = pd.DataFrame(user_health_response.data)
        user_info = user_response.data[0]  # Assuming only one user record

        # Goal tracking
        daily_duration_goal = user_info.get('workoutDurationPerDay', None)
        frequency_goal = user_info.get('workoutFrequencyPerWeek', None)
        calories_goal = user_info.get('caloriesBurnPerDay', None)

        # Merge health data with workout data
        df_health = df_health.merge(df_workouts[['workout_id', 'startDT', 'endDT']], on='workout_id', how='left')
        df_health['timestamp'] = pd.to_datetime(df_health['timestamp'])
        df_workouts['startDT'] = pd.to_datetime(df_workouts['startDT'])
        df_workouts['endDT'] = pd.to_datetime(df_workouts['endDT'])

        # Add calculated columns
        df_workouts['duration'] = (df_workouts['endDT'] - df_workouts['startDT']).dt.total_seconds() / 60  # in minutes
        df_workouts['workout_date'] = df_workouts['startDT'].dt.date

        # Calculate total workouts per week
        df_workouts['week'] = df_workouts['startDT'].dt.isocalendar().week
        workouts_per_week = df_workouts.groupby('week').size().reset_index(name='workouts_per_week')

        # Check goals
        st.subheader("Goal Tracking")

        # Initialize a DataFrame to store daily goal tracking results
        goal_tracking = pd.DataFrame({'date': pd.date_range(start=df_workouts['workout_date'].min(), 
                                                            end=df_workouts['workout_date'].max())})

        # Calculate daily statistics
        daily_stats = df_workouts.groupby('workout_date').agg(
            avg_duration=('duration', 'mean'),
            total_workouts=('workout_id', 'count'),
            total_calories=('calories_burned', 'sum')
        ).reset_index()

        # Merge daily stats with goal tracking DataFrame
        goal_tracking = goal_tracking.merge(daily_stats, left_on='date', right_on='workout_date', how='left')

        # Determine if goals were met
        goal_tracking['duration_goal_met'] = goal_tracking['avg_duration'] >= daily_duration_goal
        goal_tracking['frequency_goal_met'] = goal_tracking['total_workouts'] >= frequency_goal
        goal_tracking['calories_goal_met'] = goal_tracking['total_calories'] >= calories_goal

        # Create a summary column for goal tracking
        goal_tracking['goal_met'] = goal_tracking.apply(
            lambda row: 'Met' if row['duration_goal_met'] and row['frequency_goal_met'] and row['calories_goal_met'] else 'Not Met', axis=1
        )

        # Plot the heatmap for goal tracking
        fig_goal_tracking = px.density_heatmap(
            goal_tracking, 
            x='date', 
            y='goal_met',
            color_continuous_scale='RdYlGn',
            title='Goal Tracking Heatmap',
            labels={'goal_met': 'Goals Met'},
            height=300
        )
        st.plotly_chart(fig_goal_tracking, use_container_width=True)

        # Other existing visualizations
        # Reps and Calories burned over time
        col1, col2 = st.columns(2)
        with col1:
            fig_reps = px.line(df_workouts, x='startDT', y='reps', title='Total Reps Over Time', markers=True)
            st.plotly_chart(fig_reps, use_container_width=True)

        with col2:
            fig_calories = px.bar(df_workouts, x='workout_date', y='calories_burned', title='Calories Burned per Workout')
            st.plotly_chart(fig_calories, use_container_width=True)

        # Heart rate trend
        st.subheader("Heart Rate Analysis")
        fig_heart_rate = px.line(df_health, x='timestamp', y='heartrate', color='workout_id', title='Heart Rate per Workout')
        st.plotly_chart(fig_heart_rate, use_container_width=True)

        # Workout duration over time
        st.subheader("Workout Duration Analysis")
        fig_duration = px.line(df_workouts, x='startDT', y='duration', title='Workout Duration Over Time', markers=True)
        st.plotly_chart(fig_duration, use_container_width=True)

    else:
        st.warning("No workout data found for the current user.")