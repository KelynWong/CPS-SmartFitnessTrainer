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
    st.markdown("""
    <style>
    /* Styling for the sidebar links */
    .sidebar-link {
        font-size: 18px;
        font-weight: bold;
        color: white;  /* Set text color to white */
        text-decoration: none;  /* Remove underline */
        padding: 10px 15px;
        display: block;
        margin-bottom: 10px;
        border-radius: 5px;
        transition: background-color 0.3s ease;
    }
    
    .sidebar-link:hover {
        background-color: #3498db;
        color: white;
        text-decoration: none;  /* Ensure no underline on hover */
    }
    
    .sidebar-link:active {
        background-color: #2980b9;
        color: white;
    }

    /* Custom styles for the sidebar header */
    .sidebar .sidebar-content {
        padding-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Sidebar content with styled links
    st.sidebar.subheader("Goals")
    st.sidebar.markdown('<a href="#overall-goal-tracking" class="sidebar-link">Overall Goal Tracking</a>', unsafe_allow_html=True)
    st.sidebar.markdown('<a href="#goal-tracking-calendar-view" class="sidebar-link">Goal Tracking Calendar</a>', unsafe_allow_html=True)
    st.sidebar.subheader("Data")
    st.sidebar.markdown('<a href="#workout-history-data" class="sidebar-link">Workout History Data</a>', unsafe_allow_html=True)
    st.sidebar.markdown('<a href="#workout-analysis" class="sidebar-link">Workout Analysis</a>', unsafe_allow_html=True)
    st.sidebar.markdown('<a href="#workout-performance-analysis" class="sidebar-link">Workout Performance Analysis</a>', unsafe_allow_html=True)
    st.sidebar.markdown('<a href="#heart-rate-analysis" class="sidebar-link">Heart Rate Analysis</a>', unsafe_allow_html=True)
    st.sidebar.markdown('<a href="#over-time-trend-analysis" class="sidebar-link">Over Time Trend Analysis</a>', unsafe_allow_html=True)

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
                "workout": selected_workout.replace(" ", ""), 
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
            today = pd.Timestamp.today()
            start_of_year = pd.Timestamp(today.year, 1, 1)

            # Create a date range from the start of the year to today
            date_range = pd.date_range(start=start_of_year, end=today)

            # Ensure the date_range is not empty
            if len(date_range) > 0:
                # Create a new DataFrame for goal tracking based on the date range
                goal_tracking = pd.DataFrame(date_range, columns=['workout_date'])

                # Convert 'workout_date' to datetime in both DataFrames to avoid merge errors
                goal_tracking['workout_date'] = pd.to_datetime(goal_tracking['workout_date'])
                df_workouts['workout_date'] = pd.to_datetime(df_workouts['workout_date'])

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
                    title = "No workouts :("
                    background_color = "gray"
                    text_color = "white"
                elif row['met_duration_goal'] and row['met_calories_goal']:
                    title = "✅ Met both daily workout duration and calorie goals!"
                    background_color = "green"
                    text_color = "white"
                elif row['met_duration_goal']:
                    title = "✅ Met daily workout duration goal but ❌ did not meet daily calorie goal."
                    background_color = "yellow"
                    text_color = "black"
                elif row['met_calories_goal']:
                    title = "✅ Met daily calorie goal but ❌ did not meet daily workout duration goal."
                    background_color = "yellow"
                    text_color = "black"
                else:
                    title = "❌ Did not meet either daily workout or calorie goals."
                    background_color = "red"
                    text_color = "white"
                
                calendar_events.append({
                    "title": title,
                    "start": date,
                    "end": date,
                    "resourceId": "a",  # Assuming a single resource for simplicity
                    "backgroundColor": background_color,  # Set background color for the event
                    "textColor": text_color
                })

            
            # Add workout streak progression to the calendar
            goal_tracking['worked_out'] = goal_tracking['duration'] > 0
            goal_tracking['day_diff'] = goal_tracking['workout_date'].diff().dt.days.fillna(0)

            # Define a streak where the difference between days is 1 (consecutive days)
            goal_tracking['is_streak'] = (goal_tracking['day_diff'] == 1) & goal_tracking['worked_out']

            # Initialize streak tracking
            streak_length = 0
            previous_streak_end = None

            # Iterate through the goal_tracking DataFrame
            for index, row in goal_tracking.iterrows():
                if row['worked_out']:
                    streak_length += 1
                    # Check if the next day breaks the streak or if this is the last day in the DataFrame
                    if index == len(goal_tracking) - 1 or not goal_tracking.iloc[index + 1]['worked_out']:
                        # This is the end of the current streak, append the event only here
                        calendar_events.append({
                            "title": f"🔥 Workout streak: {streak_length} days!",
                            "start": row['workout_date'].strftime("%Y-%m-%d"),
                            "end": row['workout_date'].strftime("%Y-%m-%d"),
                            "resourceId": "a",
                            "backgroundColor": "orange"
                        })
                        # Reset streak length after adding the event
                        streak_length = 0
                else:
                    # Reset streak if there's no workout on that day
                    streak_length = 0

            # Get a list of all Mondays (start of the week) for the whole year until today
            all_weeks = pd.date_range(start=start_of_year, end=today, freq='W-MON')

            # Calculate total workouts, average duration, and calories burned per week
            df_workouts['week'] = df_workouts['startDT'].dt.isocalendar().week
            df_workouts['year'] = df_workouts['startDT'].dt.isocalendar().year

            weekly_stats = df_workouts.groupby(['year', 'week']).agg({
                'duration': 'mean',
                'calories_burned': 'sum',
                'startDT': 'count'  # Number of workouts per week
            }).reset_index().rename(columns={'startDT': 'workouts_per_week'})

            # Weekly goal tracking for all weeks in the year
            for start_of_week in all_weeks:
                # Get the year and week number for this Monday
                year, week = start_of_week.year, start_of_week.isocalendar().week
                end_of_week = start_of_week + pd.Timedelta(days=7)

                # Check if there are workouts for this week
                week_stats = weekly_stats[(weekly_stats['year'] == year) & (weekly_stats['week'] == week)]

                if not week_stats.empty:
                    num_workouts = week_stats['workouts_per_week'].values[0]
                    avg_duration = week_stats['duration'].values[0]
                    total_calories = week_stats['calories_burned'].values[0]
                    
                    # Check if weekly goals were met
                    if frequency_goal and num_workouts >= frequency_goal:
                        weekly_title = f"✅ Met weekly workout frequency goal with {num_workouts} workouts!"
                        weekly_background_color = "green"
                        text_color = "white"
                    else:
                        weekly_title = f"❌ Did not fully meet weekly workout frequency goal. Only {num_workouts} workouts."
                        weekly_background_color = "yellow"
                        text_color = "black"
                    
                    calendar_events.append({
                        "title": weekly_title,
                        "start": start_of_week.strftime("%Y-%m-%d"),
                        "end": end_of_week.strftime("%Y-%m-%d"),
                        "resourceId": "a",
                        "backgroundColor": weekly_background_color,  # Set background color for the event
                        "textColor": text_color
                    })
                    
                    # Add average workout duration per week
                    calendar_events.append({
                        "title": f"Avg duration: {avg_duration:.2f} mins",
                        "start": start_of_week.strftime("%Y-%m-%d"),
                        "end": end_of_week.strftime("%Y-%m-%d"),
                        "resourceId": "a",
                        "backgroundColor": "lightblue"
                    })
                    
                    # Add total calories burned per week
                    calendar_events.append({
                        "title": f"Total calories burned: {total_calories:.0f}",
                        "start": start_of_week.strftime("%Y-%m-%d"),
                        "end": end_of_week.strftime("%Y-%m-%d"),
                        "resourceId": "a",
                        "backgroundColor": "purple"
                    })
                else:
                    # No workouts this week
                    calendar_events.append({
                        "title": "No workouts for this week :(",
                        "start": start_of_week.strftime("%Y-%m-%d"),
                        "end": end_of_week.strftime("%Y-%m-%d"),
                        "resourceId": "a",
                        "backgroundColor": "grey"
                    })

            # Calendar options
            calendar_options = {
                "editable": "false",
                "selectable": "false",
                "headerToolbar": {
                    "left": "today prev,next",
                    "center": "title",
                    "right": "dayGridMonth,dayGridWeek,dayGridDay",
                },
                "slotMinTime": "06:00:00",
                "slotMaxTime": "18:00:00",
                "initialView": "dayGridMonth",
                "resourceGroupField": "building",
                "firstDay": 1,
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
                /* Reduce calendar event font size */
                .fc-event-title {
                    font-size: 0.8rem; /* Make event titles smaller */
                }
                /* Reduce height of calendar cells */
                .fc-daygrid-day-frame {
                    min-height: 20px; /* Adjust this value to decrease cell height */
                }
                .fc-event-title {
                    white-space: normal !important; /* Allow text to wrap */
                    word-wrap: break-word; /* Break long words if necessary */
                    font-size: 0.9em; /* Optional: Make the text slightly smaller */
                    line-height: 1.2em; /* Optional: Adjust the line height */
                }
                .fc-daygrid-event {
                    height: auto !important; /* Allow the height to adjust to content */
                }
            """

            # Create the calendar object
            calendar_view = calendar(events=calendar_events, options=calendar_options, custom_css=custom_css)

            # Render the calendar
            st.write(calendar_view)

            # Workout and health data visualization
            st.subheader(f"Workout History Data")
            st.dataframe(df_workouts[['startDT', 'endDT', 'duration', 'workout', 'reps', 'overallAccuracy', 'avg_heartbeat', 'calories_burned']])

            st.subheader("Workout Analysis")
            df_workouts['day_of_week'] = df_workouts['startDT'].dt.day_name()
            fig_frequency = px.bar(df_workouts, x='day_of_week', title='Workout Frequency by Day of the Week')
            st.plotly_chart(fig_frequency, use_container_width=True)

            fig_duration_per_workout = px.bar(df_workouts, x='workout_date', y='duration', title='Total Duration per Workout')
            st.plotly_chart(fig_duration_per_workout, use_container_width=True)

            # Display calories graph only if weight, age, and gender are set 
            if weight is not None and age is not None and gender is not None:
                    fig_calories = px.bar(df_workouts, x='workout_date', y='calories_burned', title='Calories Burned per Workout')
                    st.plotly_chart(fig_calories, use_container_width=True)

            st.subheader("Workout Performance Analysis")
            # Line chart of workout_date vs overallAccuracy, colored by workout
            fig_accuracy = px.line(df_workouts, x='workout_date', y='overallAccuracy', color='workout', 
                                title='Form Accuracy Over Time by Workout Type')
            st.plotly_chart(fig_accuracy, use_container_width=True)

            # Box plot comparing workout against duration, calories_burned, or overallAccuracy
            fig_comparison = px.box(df_workouts, x='workout', y='duration', title='Workout Type vs Duration')
            st.plotly_chart(fig_comparison, use_container_width=True)

            # You can create similar box plots for calories_burned and overallAccuracy:
            fig_calories = px.box(df_workouts, x='workout', y='calories_burned', title='Workout Type vs Calories Burned')
            st.plotly_chart(fig_calories, use_container_width=True)

            fig_accuracy_comparison = px.box(df_workouts, x='workout', y='overallAccuracy', title='Workout Type vs Accuracy')
            st.plotly_chart(fig_accuracy_comparison, use_container_width=True)

            # Scatter plot of reps vs duration, colored by workout
            fig_reps_duration = px.scatter(df_workouts, x='reps', y='duration', color='workout', 
                                        title='Reps vs Duration')
            st.plotly_chart(fig_reps_duration, use_container_width=True)

            # Heart rate  
            st.subheader("Heart Rate Analysis")
            fig_heart_rate = px.line(df_health, x='timestamp', y='heartrate', color='workout_id', title='Heart Rate per Workout')
            st.plotly_chart(fig_heart_rate, use_container_width=True)  # Full-width chart
            
            avg_heart_rate = df_health.groupby('workout_id')['heartrate'].mean().reset_index()
            df_workouts_avg_hr = df_workouts.merge(avg_heart_rate, on='workout_id', how='left')
            fig_avg_hr = px.line(df_workouts_avg_hr, x='startDT', y='heartrate', title='Average Heart Rate per Workout')
            st.plotly_chart(fig_avg_hr, use_container_width=True)

            fig_hr_distribution = px.histogram(df_health, x='heartrate', nbins=50, title='Heart Rate Distribution')
            st.plotly_chart(fig_hr_distribution, use_container_width=True)

            fig_intensity = px.box(df_health, x='workout_id', y='heartrate', title='Workout Intensity Distribution')
            st.plotly_chart(fig_intensity, use_container_width=True)

            st.subheader("Over Time Trend Analysis")
            # Workout duration over time 
            fig_duration = px.line(df_workouts, x='startDT', y='duration', title='Workout Duration Over Time', markers=True)
            st.plotly_chart(fig_duration, use_container_width=True)  # Full-width chart

            # Reps over time graph 
            fig_reps = px.line(df_workouts, x='startDT', y='reps', title='Total Reps Over Time', markers=True)
            st.plotly_chart(fig_reps, use_container_width=True)

            fig_calories_line = px.line(df_workouts, x='workout_date', y='calories_burned', title='Calories Burned Over Time', markers=True)
            st.plotly_chart(fig_calories_line, use_container_width=True)


    else:
        st.warning("No workout data found for the current user.")
