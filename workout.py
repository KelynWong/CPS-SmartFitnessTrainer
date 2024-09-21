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
    col1, col2, col3 = st.columns([3, 3, 1])

    with col1:
        selected_workout = st.selectbox("Select a Workout", workouts)

    with col2:
        ip_address = st.text_input("Enter Raspberry Pi IP Address")

    with col3:
        st.write(" ")
        st.write(" ")
        start_button = st.button("Start Workout")

    # Button click logic to display YouTube URL
    if start_button and ip_address:
        try:
            # Call the API to start the workout stream
            st.write("Starting workout...")
            api_url = f"http://{ip_address}:5000/start"
            response = requests.post(api_url)

            # Check if the request was successful
            if response.status_code == 200:
                result = response.json()
                watch_url = result.get("watch_url")

                # Display the returned watch_url
                if watch_url:
                    st.write("Stream started successfully! Here is your workout video:")
                    st.video(watch_url, autoplay=True)
                else:
                    st.error("Failed to retrieve the watch URL from the response.")
            else:
                st.error(f"Failed to start the workout stream. Status code: {response.status_code}")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

    # Fetch user workout data from 'userWorkouts' table where username matches session state
    username = st.session_state['username']
    user_workout_response = supabase_client.table('userWorkouts').select('*').eq('username', username).execute()

    if user_workout_response.data:
        # Convert the data into a pandas DataFrame for easier analysis and visualization
        df = pd.DataFrame(user_workout_response.data)

        # Display the data as a table
        st.subheader(f"Workout Data for {username}")
        st.dataframe(df)

        # Convert startDT and endDT columns to datetime format for plotting
        df['startDT'] = pd.to_datetime(df['startDT'])
        df['endDT'] = pd.to_datetime(df['endDT'])

        st.subheader(f"Workout Analysis")
        # First Row: Total Reps Over Time and Workout Frequency
        col1, col2 = st.columns(2)
        with col1:
            # Calculate total reps over time
            fig_reps = px.line(df, x='startDT', y='reps', title='Total Reps Over Time', markers=True)
            st.plotly_chart(fig_reps, use_container_width=True)

        with col2:
            # Workout frequency analysis (count of workouts over time)
            df['workout_date'] = df['startDT'].dt.date
            workout_count = df.groupby('workout_date').size().reset_index(name='Workout Count')
            fig_workout_freq = px.bar(workout_count, x='workout_date', y='Workout Count', title='Workout Frequency Over Time')
            st.plotly_chart(fig_workout_freq, use_container_width=True)

        # Second Row: Average Reps per Workout and Duration of Workouts
        col1, col2 = st.columns(2)
        with col1:
            # Average reps per workout
            avg_reps_per_workout = df.groupby('workout')['reps'].mean().reset_index()
            fig_avg_reps = px.bar(avg_reps_per_workout, x='workout', y='reps', title='Average Reps per Workout')
            st.plotly_chart(fig_avg_reps, use_container_width=True)

        with col2:
            # Duration of workouts
            df['duration'] = (df['endDT'] - df['startDT']).dt.total_seconds() / 60  # Convert duration to minutes
            fig_duration = px.bar(df, x='workout', y='duration', title='Duration of Workouts', text='duration')
            fig_duration.update_traces(texttemplate='%{text:.2f} min', textposition='outside')
            st.plotly_chart(fig_duration, use_container_width=True)
    else:
        st.warning("No workout data found for the current user.")
