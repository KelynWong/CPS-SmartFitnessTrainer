import streamlit as st
import supabase
import io

def profile_page():
    # Initialize Supabase client
    supabase_client = supabase.create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

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

    # Fetch user details from 'user' table, excluding the password
    user_response = supabase_client.table('user').select('username, caloriesBurnPerDay, durationPerWorkout, workoutFrequencyPerWeek, profilePicture').eq('username', username).single().execute()

    if user_response.data:
        user_data = user_response.data

        # Display profile picture if available, otherwise show a placeholder
        if user_data['profilePicture'] is not None and user_data['profilePicture'].strip() != "":
            st.image(user_data['profilePicture'], width=150, caption="Profile Picture")
        else:
            # Use a placeholder image if no profile picture is found
            st.image("https://avatar.iran.liara.run/public", width=150, caption="No Profile Picture")

        # Profile form with pre-filled values
        with st.form("profile_form"):
            st.subheader(f"Edit Profile for {user_data['username']}")
            
            calories_burn = st.number_input("Calories Burn per Day", value=user_data['caloriesBurnPerDay'], min_value=0)
            duration_workout = st.number_input("Duration per Workout (in minutes)", value=user_data['durationPerWorkout'], min_value=0)
            frequency_workout = st.number_input("Workout Frequency per Week", value=user_data['workoutFrequencyPerWeek'], min_value=0)

            # File uploader for profile picture
            uploaded_file = st.file_uploader("Upload Profile Picture", type=["png", "jpg", "jpeg"])

            # Submit button for saving changes
            save_button = st.form_submit_button("Save Changes")

        # Save the updated details
        if save_button:
            # Handle profile picture upload if a file is uploaded
            if uploaded_file is not None:
                # Save uploaded file to Supabase storage
                image_bytes = uploaded_file.read()
                file_ext = uploaded_file.name.split('.')[-1]
                file_name = f"profile_{username}.{file_ext}"

                # Upload the image to Supabase Storage
                upload_response = supabase_client.storage().from_('profileImages').upload(f"{username}/{file_name}", io.BytesIO(image_bytes))

                if upload_response.status_code == 200:
                    # Get the public URL of the uploaded profile picture
                    profile_picture_url = supabase_client.storage().from_('profileImages').get_public_url(f"{username}/{file_name}")
                    st.success("Profile picture uploaded successfully!")

                    # Update the user table with the profile picture URL
                    supabase_client.table('user').update({
                        'profilePicture': profile_picture_url
                    }).eq('username', username).execute()
                else:
                    st.error("Failed to upload profile picture.")

            # Update the rest of the user profile data
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
