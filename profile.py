import streamlit as st
import supabase
import io

def profile_page():
    # Initialize Supabase client
    supabase_client = supabase.create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_SERVICE_ROLE_KEY"])

    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("Profile Page")

    with col2:
        # Add a button to navigate back to the workout page
        if st.button("Go to Workout Page"):
            st.session_state['current_page'] = 'workout'
            st.rerun()

    # Get the logged-in user's username from session state
    username = st.session_state['username']

    try:
        # Fetch user details from 'user' table
        user_response = supabase_client.table('user').select('username, caloriesBurnPerDay, durationPerWorkout, workoutFrequencyPerWeek, profilePicture').eq('username', username).single().execute()
        
        if user_response:
            user_data = user_response.data

            # Profile form with pre-filled values
            with st.form("profile_form"):
                st.subheader(f"Edit Profile for {user_data['username']}")
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    # Display profile picture if available, otherwise show a placeholder
                    if user_data['profilePicture']:
                        st.image(user_data['profilePicture'], width=150, caption="Profile Picture", use_column_width='auto')
                    else:
                        st.image("https://avatar.iran.liara.run/public", width=150, caption="No Profile Picture", use_column_width='auto')
                
                with col2:
                    # File uploader for profile picture
                    uploaded_file = st.file_uploader("Upload Profile Picture", type=["png", "jpg", "jpeg"])

                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    calories_burn = st.number_input("Calories Burn per Day", value=user_data['caloriesBurnPerDay'], min_value=0)
                
                with col2:
                    duration_workout = st.number_input("Duration per Workout (in minutes)", value=user_data['durationPerWorkout'], min_value=0)
                
                with col3:
                    frequency_workout = st.number_input("Workout Frequency per Week", value=user_data['workoutFrequencyPerWeek'], min_value=0)

                # Submit button for saving changes
                save_button = st.form_submit_button("Save Changes")

            if save_button:
                if uploaded_file is not None:
                    try:
                        # Handle profile picture upload
                        image_bytes = uploaded_file.read()  # Read raw bytes from the uploaded file
                        file_ext = uploaded_file.name.split('.')[-1]
                        file_name = f"profile_{username}.{file_ext}"

                        public_url_response = supabase_client.storage.from_('profileImages').get_public_url(f"{username}/{file_name}")
                        st.write(public_url_response)
                        # Check if the user already has a profile picture, and delete the old one if it exists
                        if public_url_response:
                            # Extract the file path from the URL (assuming the public URL is like: <bucket>/<username>/<filename>)
                            old_file_path = user_data['profilePicture'].split(st.secrets["SUPABASE_URL"])[-1]
                            delete_response = supabase_client.storage.from_('profileImages').remove([old_file_path])

                        # Upload the file directly using raw bytes
                        upload_response = supabase_client.storage.from_('profileImages').upload(f"{username}/{file_name}", image_bytes)
                        public_url_response = supabase_client.storage.from_('profileImages').get_public_url(f"{username}/{file_name}")
                        profile_picture_url = public_url_response

                        # Update the user table with the profile picture URL
                        update_profile_picture_response = supabase_client.table('user').update({
                            'profilePicture': profile_picture_url
                        }).eq('username', username).execute()

                        st.success("Profile picture URL updated successfully!")
  
                    except Exception as e:
                        st.error(f"An error occurred during the upload: {e}")

                try:
                    # Update the rest of the user profile data
                    update_response = supabase_client.table('user').update({
                        'caloriesBurnPerDay': calories_burn,
                        'durationPerWorkout': duration_workout,
                        'workoutFrequencyPerWeek': frequency_workout
                    }).eq('username', username).execute()

                    st.success("Profile updated successfully!")
                
                except Exception as e:
                    st.error(f"An error occurred while updating the profile: {e}")
        
        else:
            st.error("User data not found.")
    
    except Exception as e:
        st.error(f"An error occurred: {e}")
