from st_socketio import sio, st_socketio
import streamlit as st
import supabase
import pandas as pd
import plotly.express as px
from PIL import Image
import io
import base64
import numpy as np
import asyncio

# Global variable to store the latest frame
latest_frame = None

@sio.on('video_frame')
def video_frame_event(sid, data):
    global latest_frame
    # Convert base64 string to image
    img_bytes = base64.b64decode(data)
    latest_frame = Image.open(io.BytesIO(img_bytes))

def update_image():
    if 'image_container' in st.session_state and latest_frame is not None:
        st.session_state.image_container.image(latest_frame, channels="RGB", use_column_width=True)

@st_socketio(path='/ws/')
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
        start_button = st.button("Start Workout", disabled=not ip_address)

    # Create a placeholder for the video feed
    st.session_state.image_container = st.empty()

    # Button click logic
    if ip_address and start_button:
        try:
            st.write("Attempting to connect to the Raspberry Pi...")
            
            # Use a callback to emit the 'start_stream' event
            asyncio.run(sio.emit('start_stream', {'ip': ip_address}))
            
            st.write("Connected successfully! Starting video feed:")
            
            # Start updating the image
            while True:
                update_image()
                if st.button("Stop Workout"):
                    st.write("Stopping workout...")
                    asyncio.run(sio.emit('stop_stream'))
                    break
                st.rerun()
            
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")
            st.error("Please check the following:")
            st.error("1. Is the Raspberry Pi powered on and connected to the network?")
            st.error("2. Is the socket server running on the Raspberry Pi?")
            st.error("3. Is the Raspberry Pi's IP address correct?")
            st.error("4. Are both devices on the same network?")

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

sio.connect()