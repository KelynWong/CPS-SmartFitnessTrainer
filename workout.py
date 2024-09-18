import streamlit as st
import supabase
import pandas as pd
import plotly.express as px
import requests
import socket
import cv2
import numpy as np
from PIL import Image
import io
import threading

def receive_video_frame(client_socket):
    try:
        frame_size = int.from_bytes(client_socket.recv(4), byteorder='big')
        
        img_bytes = b''
        while len(img_bytes) < frame_size:
            chunk = client_socket.recv(frame_size - len(img_bytes))
            if not chunk:
                return None
            img_bytes += chunk

        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame_rgb)
        
        return image
    except Exception as e:
        st.error(f"An error occurred while receiving video frame: {str(e)}")
        return None

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
    video_placeholder = st.empty()

    # Button click logic
    if ip_address and start_button:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((ip_address, 12345))
            
            st.write("Video Feed:")
            
            # Use st.empty() to create a container that we can update
            image_container = st.empty()
            
            while True:
                image = receive_video_frame(client_socket)
                if image is None:
                    break
                
                image_container.image(image, channels="RGB", use_column_width=True)

                # Check if the user wants to stop the stream
                if st.button("Stop Workout"):
                    break
            
            client_socket.close()
            st.write("Video stream ended.")
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.error("Please check the following:")
            st.error("1. Is the Raspberry Pi powered on and connected to the network?")
            st.error("2. Is the socket server running on the Raspberry Pi?")
            st.error("3. Is port 12345 open on the Raspberry Pi's firewall?")
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


def on_change():
    if 'video_thread' in st.session_state:
        # Implement a way to stop the thread safely
        pass

st.session_state.on_change = on_change