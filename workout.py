import streamlit as st
import supabase
import requests
from streamlit_webrtc import webrtc_streamer

def workout_page():
    # Initialize Supabase client
    supabase_client = supabase.create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

    st.title("Smart Fitness Trainer - Workout Dashboard")

    # Fetch workouts from Supabase
    workout_response = supabase_client.table('workouts').select('*').execute()
    if workout_response.data:
        workouts = [workout['name'] for workout in workout_response.data]
        selected_workout = st.selectbox("Select a Workout", workouts)

    # Input box for Raspberry Pi IP address
    ip_address = st.text_input("Enter Raspberry Pi IP Address")

    # Button to start the workout
    if st.button("Start Workout", disabled=not ip_address):
        try:
            # Attempt to connect to the Raspberry Pi's API server
            raspberry_pi_url = f"http://{ip_address}:5000/start_workout"
            response = requests.get(raspberry_pi_url)
            response.raise_for_status()

            st.success("Connected to Raspberry Pi!")
            
            # Display the video stream from Raspberry Pi
            webrtc_streamer(key="raspberry-pi-stream", video_processor_factory=None, video_source=f"http://{ip_address}:5000/video_feed")
        
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to connect: {e}")
