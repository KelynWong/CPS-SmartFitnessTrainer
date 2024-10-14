import streamlit as st
import supabase
import pandas as pd
import plotly.express as px
import requests
import time
from datetime import datetime, timedelta
import pytz
from streamlit_calendar import calendar

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

        # Check for necessary user data
        weight = user_info.get('weight', None)
        age = user_info.get('age', None)
        gender = user_info.get('gender', None)

        if weight is None or age is None or gender is None:
            st.warning("To provide more accurate analytics, please update your profile with your weight, age, and gender.")
        else: 
            # Calories burned calculation
            avg_heart_rate = df_health.groupby('workout_id')['heartrate'].mean().reset_index(name='avg_heartbeat')
            df_workouts = df_workouts.merge(avg_heart_rate, on='workout_id', how='left')

            # Calculate calories burned based on gender
            if gender == "Female":
                df_workouts['calories_burned'] = df_workouts['duration'] * (
                    (0.4472 * df_workouts['avg_heartbeat']) - 
                    (0.1263 * weight) + 
                    (0.074 * age) - 
                    20.4022) / 4.184
            else:  # Male
                df_workouts['calories_burned'] = df_workouts['duration'] * (
                    (0.6309 * df_workouts['avg_heartbeat']) + 
                    (0.1988 * weight) + 
                    (0.2017 * age) - 
                    55.0969) / 4.184

            # Goal Tracking Section
            st.subheader("Overall Goal Tracking")

            col1, col2, col3 = st.columns(3)

            with col1:
                # Check daily duration goal
                if daily_duration_goal:
                    avg_duration = df_workouts['duration'].mean()
                    st.write(f"**Daily Duration Goal:** {daily_duration_goal} minutes")
                    st.write(f"**Average Workout Duration:** {avg_duration:.2f} minutes")
                    if avg_duration >= daily_duration_goal:
                        st.success("You are meeting your daily workout duration goal on average!")
                    else:
                        st.warning("You are not meeting your daily workout duration goal on average.")

            with col2:
                # Check weekly frequency goal
                if frequency_goal:
                    avg_frequency = workouts_per_week['workouts_per_week'].mean()
                    st.write(f"**Weekly Frequency Goal:** {frequency_goal} workouts/week")
                    st.write(f"**Average Workouts Per Week:** {avg_frequency:.2f} workouts/week")
                    if avg_frequency >= frequency_goal:
                        st.success("You are meeting your weekly workout frequency goal on average!")
                    else:
                        st.warning("You are not meeting your weekly workout frequency goal on average.")

            with col3:
                # Check daily calories goal and display related metrics
                if calories_goal and 'calories_burned' in df_workouts.columns:
                    total_calories_burned = df_workouts['calories_burned'].sum()
                    st.write(f"**Daily Calories Burn Goal:** {calories_goal} calories")
                    st.write(f"**Total Calories Burned:** {total_calories_burned:.2f} calories")
                    if total_calories_burned >= calories_goal:
                        st.success("You are meeting your daily calories burn goal on average!")
                    else:
                        st.warning("You are not meeting your daily calories burn goal on average.")
                else:
                    st.warning("Calories burned data is not available. Please ensure your weight, age, and gender are set.")

            # Workout and health data visualization
            st.subheader("Goal Tracking Calendar View")

            # Get the current year
            today = datetime.today()
            start_of_year = datetime(today.year, 1, 1)

            # Create a date range from the start of the year until today
            date_range = pd.date_range(start=start_of_year, end=today)

            # Create a new DataFrame for goal tracking based on the date range
            goal_tracking = pd.DataFrame(date_range, columns=['workout_date'])

            # Merge with the existing workout data to track goals
            goal_tracking = goal_tracking.merge(df_workouts.groupby('workout_date').agg({
                'duration': 'mean', 
                'calories_burned': 'sum'
            }).reset_index(), on='workout_date', how='left')

            # Fill missing workout data with zeros or NaNs
            goal_tracking['duration'].fillna(0, inplace=True)
            goal_tracking['calories_burned'].fillna(0, inplace=True)

            # Track if the daily goals were met or not
            goal_tracking['met_duration_goal'] = goal_tracking['duration'] >= daily_duration_goal
            goal_tracking['met_calories_goal'] = goal_tracking['calories_burned'] >= calories_goal if calories_goal else False

            # Prepare calendar events based on the goal tracking results
            calendar_events = []
            for index, row in goal_tracking.iterrows():
                date = row['workout_date'].strftime("%Y-%m-%d")
                
                # Determine the status of the goals and set the appropriate message and background color
                if row['duration'] == 0 and row['calories_burned'] == 0:
                    title = "No workouts"
                    background_color = "gray"
                elif row['met_duration_goal'] and row['met_calories_goal']:
                    title = "✅ Met both daily workout duration and calorie goals!"
                    background_color = "green"
                elif row['met_duration_goal']:
                    title = "✅ Met daily workout duration goal but ❌ did not meet daily calorie goal."
                    background_color = "yellow"
                elif row['met_calories_goal']:
                    title = "✅ Met daily calorie goal but ❌ did not meet daily workout duration goal."
                    background_color = "yellow"
                else:
                    title = "❌ Did not meet either daily workout or calorie goals."
                    background_color = "red"
                
                calendar_events.append({
                    "title": title,
                    "start": date,
                    "end": date,
                    "resourceId": "a",  # Assuming a single resource for simplicity
                    "backgroundColor": background_color  # Set background color for the event
                })

            # Calculate total workouts per week
            df_workouts['week'] = df_workouts['startDT'].dt.isocalendar().week
            workouts_per_week = df_workouts.groupby('week').size().reset_index(name='workouts_per_week')

            # Weekly goal tracking
            for week, group in df_workouts.groupby('week'):
                start_date = group['startDT'].min().strftime("%Y-%m-%d")
                end_date = group['endDT'].max().strftime("%Y-%m-%d")
                num_workouts = group.shape[0]

                if frequency_goal and num_workouts >= frequency_goal:
                    weekly_title = f"✅ Met weekly workout frequency goal with {num_workouts} workouts!"
                    weekly_background_color = "green"
                else:
                    weekly_title = f"❌ Did not meet weekly workout frequency goal. Only {num_workouts} workouts."
                    weekly_background_color = "red"

                # Stretch this event across the whole week (Monday to Sunday)
                calendar_events.append({
                    "title": weekly_title,
                    "start": start_date,
                    "end": end_date,
                    "resourceId": "a",
                    "backgroundColor": weekly_background_color  # Set background color for the event
                })

            # Calendar options
            calendar_options = {
                "editable": "true",
                "selectable": "true",
                "headerToolbar": {
                    "left": "today prev,next",
                    "center": "title",
                    "right": "dayGridMonth,dayGridWeek,dayGridDay",
                },
                "slotMinTime": "06:00:00",
                "slotMaxTime": "18:00:00",
                "initialView": "dayGridMonth",
                "resourceGroupField": "building",
                "resources": [
                    {"id": "a", "building": "Goals", "title": "Goals Tracking"}
                ]
            }

            # Custom CSS for calendar styling
            custom_css = """
                .fc-event-past {
                    opacity: 0.8;
                }
                .fc-event-time {
                    font-style: italic;
                }
                .fc-event-title {
                    font-weight: 700;
                }
                .fc-toolbar-title {
                    font-size: 2rem;
                }
                .fc-event { 
                    background-color: var(--fc-event-background-color); 
                }
            """

            # Create the calendar object
            calendar_view = calendar(events=calendar_events, options=calendar_options, custom_css=custom_css)

            # Render the calendar
            st.write(calendar_view)

            # Workout and health data visualization
            st.subheader(f"Raw Workout Data for {username}")
            st.dataframe(df_workouts)

            st.subheader("Workout Frequency by Day of the Week")
            df_workouts['day_of_week'] = df_workouts['startDT'].dt.day_name()
            fig_frequency = px.bar(df_workouts, x='day_of_week', title='Workout Frequency by Day of the Week')
            st.plotly_chart(fig_frequency, use_container_width=True)

            st.subheader("Total Duration per Workout")
            fig_duration_per_workout = px.bar(df_workouts, x='workout_date', y='duration', title='Total Duration per Workout')
            st.plotly_chart(fig_duration_per_workout, use_container_width=True)

            # Display calories graph only if weight, age, and gender are set 
            if weight is not None and age is not None and gender is not None:
                    fig_calories = px.bar(df_workouts, x='workout_date', y='calories_burned', title='Calories Burned per Workout')
                    st.plotly_chart(fig_calories, use_container_width=True)

            # Heart rate  
            st.subheader("Heart Rate Analysis")
            fig_heart_rate = px.line(df_health, x='timestamp', y='heartrate', color='workout_id', title='Heart Rate per Workout')
            st.plotly_chart(fig_heart_rate, use_container_width=True)  # Full-width chart
            
            st.subheader("Average Heart Rate per Workout")
            avg_heart_rate = df_health.groupby('workout_id')['heartrate'].mean().reset_index()
            df_workouts_avg_hr = df_workouts.merge(avg_heart_rate, on='workout_id', how='left')
            fig_avg_hr = px.line(df_workouts_avg_hr, x='startDT', y='heartrate', title='Average Heart Rate per Workout')
            st.plotly_chart(fig_avg_hr, use_container_width=True)

            st.subheader("Heart Rate Distribution")
            fig_hr_distribution = px.histogram(df_health, x='heartrate', nbins=50, title='Heart Rate Distribution')
            st.plotly_chart(fig_hr_distribution, use_container_width=True)

            st.subheader("Workout Intensity Analysis")
            fig_intensity = px.box(df_health, x='workout_id', y='heartrate', title='Workout Intensity Distribution (Heart Rate)')
            st.plotly_chart(fig_intensity, use_container_width=True)

            st.subheader("Over time trends")
            # Workout duration over time 
            st.subheader("Workout Duration Analysis")
            fig_duration = px.line(df_workouts, x='startDT', y='duration', title='Workout Duration Over Time', markers=True)
            st.plotly_chart(fig_duration, use_container_width=True)  # Full-width chart

            # Reps over time graph 
            fig_reps = px.line(df_workouts, x='startDT', y='reps', title='Total Reps Over Time', markers=True)
            st.plotly_chart(fig_reps, use_container_width=True)

            st.subheader("Calories Burned Over Time")
            fig_calories_line = px.line(df_workouts, x='workout_date', y='calories_burned', title='Calories Burned Over Time', markers=True)
            st.plotly_chart(fig_calories_line, use_container_width=True)


    else:
        st.warning("No workout data found for the current user.")
