import streamlit as st
import supabase
import pandas as pd
import plotly.express as px

def workout_page():
    # Initialize Supabase client
    supabase_client = supabase.create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

    st.title("Smart Fitness Trainer - Workout Dashboard")

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

    # Button click logic
    if ip_address and start_button:
        try:
            video_url = f"http://{ip_address}:5000/video_feed"
            st.write("Video Feed:")
            st.markdown(f'<iframe src="{video_url}" width="640" height="480"></iframe>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"An error occurred: {e}")

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
