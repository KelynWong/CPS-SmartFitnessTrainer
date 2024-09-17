import streamlit as st
import supabase

def profile_page():
    # Initialize Supabase client
    supabase_client = supabase.create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

    col1, col2 = st.columns(2)
    with col1:
        st.title("Profile Page")

    with col2:
        # Add a button to navigate back to the workout page
        if st.button("Go to Workout Page"):
            st.session_state['current_page'] = 'workout'
            st.rerun()

    # Get the logged-in user's username from session state
    username = st.session_state['username']

    # Fetch user details from 'user' table, excluding the password
    user_response = supabase_client.table('user').select('username, caloriesBurnPerDay, durationPerWorkout, workoutFrequencyPerWeek').eq('username', username).single().execute()

    if user_response.data:
        user_data = user_response.data

        # Profile form with pre-filled values
        with st.form("profile_form"):
            st.subheader(f"Edit Profile for {user_data['username']}")
            
            calories_burn = st.number_input("Calories Burn per Day", value=user_data['caloriesBurnPerDay'], min_value=0)
            duration_workout = st.number_input("Duration per Workout (in minutes)", value=user_data['durationPerWorkout'], min_value=0)
            frequency_workout = st.number_input("Workout Frequency per Week", value=user_data['workoutFrequencyPerWeek'], min_value=0)

            # Submit button for saving changes
            save_button = st.form_submit_button("Save Changes")

        # Save the updated details
        if save_button:
            update_response = supabase_client.table('user').update({
                'caloriesBurnPerDay': calories_burn,
                'durationPerWorkout': duration_workout,
                'workoutFrequencyPerWeek': frequency_workout
            }).eq('username', username).execute()

            if update_response.status_code == 200:
                st.success("Profile updated successfully!")
            else:
                st.error("An error occurred while updating the profile.")

    else:
        st.error("User data not found.")
