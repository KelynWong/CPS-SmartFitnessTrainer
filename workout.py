import streamlit as st
import supabase
import pandas as pd
import plotly.express as px
import requests

def workout_page():
    # Initialize Supabase client
    supabase_client = supabase.create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

    col1, col2 = st.columns([4,1])
    with col1:
        st.title("Smart Fitness Trainer - Workout Dashboard")

    with col2:
        # Add a button to navigate to the profile page
        st.write(" ")
        profile_button = st.button("Go to profile")
        if profile_button:
            st.session_state['current_page'] = 'profile'
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
        ip_address = st.text_input("Enter Raspberry Pi IP Address")

    # Initialize the workout status if it's not in session state
    if "workout_running" not in st.session_state:
        st.session_state['workout_running'] = False

    # Separate buttons for Start and Stop Workout
    with col3:
        st.write(" ")
        st.write(" ")
        start_button = st.button("Start Workout", disabled=st.session_state['workout_running'] or not ip_address)
        
    with col4:
        st.write(" ")
        st.write(" ")
        stop_button = st.button("Stop Workout", disabled=not st.session_state['workout_running'])

    # Logic to handle the Start Workout button click
    if start_button and ip_address:
        try:
            st.write("Starting workout...")
            api_url = f"https://{ip_address}/start"
            response = requests.post(api_url)

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
            api_url = f"https://{ip_address}/stop"
            response = requests.post(api_url)

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
