import streamlit as st
import supabase
import requests
import pandas as pd
import plotly.express as px
# from streamlit_webrtc import webrtc_streamer

def workout_page():
    # Initialize Supabase client
    supabase_client = supabase.create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

    st.title("Smart Fitness Trainer - Workout Dashboard")

    # Fetch workouts from Supabase
    workout_response = supabase_client.table('workouts').select('*').execute()
    if workout_response.data:
        workouts = [workout['name'] for workout in workout_response.data]

    # Use st.columns to arrange components side by side
    col1, col2, col3 = st.columns([2, 2, 1])  # Adjust column width ratios as needed

    with col1:
        selected_workout = st.selectbox("Select a Workout", workouts)

    with col2:
        ip_address = st.text_input("Enter Raspberry Pi IP Address")

    with col3:
        st.write("")  # Adding some empty lines to align better
        st.write("")
        st.button("Start Workout", disabled=not ip_address)

    # Button click logic
    if ip_address and st.session_state.get('Start Workout'):
        try:
            # Attempt to connect to the Raspberry Pi's API server
            raspberry_pi_url = f"http://{ip_address}:5000/start_workout"
            response = requests.get(raspberry_pi_url)
            response.raise_for_status()

            st.success("Connected to Raspberry Pi!")
            
            # Display the video stream from Raspberry Pi
            # webrtc_streamer(key="raspberry-pi-stream", video_processor_factory=None, video_source=f"http://{ip_address}:5000/video_feed")
        
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to connect: {e}")

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

        # Calculate total reps over time
        fig_reps = px.line(df, x='startDT', y='reps', title='Total Reps Over Time', markers=True)
        st.plotly_chart(fig_reps)

        # Workout frequency analysis (count of workouts over time)
        df['workout_date'] = df['startDT'].dt.date
        workout_count = df.groupby('workout_date').size().reset_index(name='Workout Count')
        fig_workout_freq = px.bar(workout_count, x='workout_date', y='Workout Count', title='Workout Frequency Over Time')
        st.plotly_chart(fig_workout_freq)
    else:
        st.warning("No workout data found for the current user.")