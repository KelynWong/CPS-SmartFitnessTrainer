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
        st.write(" ")
        if st.button("Go to Workout Page"):
            st.session_state['current_page'] = 'workout'
            st.rerun()

    # Get the logged-in user's username from session state
    username = st.session_state['username']

    # Fetch user details from 'user' table, excluding the password
    user_response = supabase_client.table('user').select('username, caloriesBurnPerDay, durationPerWorkout, workoutFrequencyPerWeek, profilePicture').eq('username', username).single().execute()

    if user_response.data:
        user_data = user_response.data

        # Profile form with pre-filled values
        with st.form("profile_form"):
            st.subheader(f"Edit Profile for {user_data['username']}")
            
            col1, col2 = st.columns([1,3])
            with col1:
                # Display profile picture if available, otherwise show a placeholder
                if user_data['profilePicture'] is not None and user_data['profilePicture'].strip() != "":
                    st.image(user_data['profilePicture'], width=200, caption="Profile Picture", use_column_width='auto')
                else:
                    # Use a placeholder image if no profile picture is found
                    st.image("https://avatar.iran.liara.run/public", width=200, caption="No Profile Picture", use_column_width='auto')
            
            with col2:
                # File uploader for profile picture
                st.write(" ")
                uploaded_file = st.file_uploader("Upload Profile Picture", type=["png", "jpg", "jpeg"])

            col1, col2, col3 = st.columns(3)
            with col1:
                calories_burn = st.number_input("Calories Burn per Day", value=user_data['caloriesBurnPerDay'], min_value=0)
            
            with col2:
                duration_workout = st.number_input("Duration per Workout (in minutes)", value=user_data['durationPerWorkout'], min_value=0)
            
            with col3:
                frequency_workout = st.number_input("Workout Frequency per Week", value=user_data['workoutFrequencyPerWeek'], min_value=0)

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

                # Check for an error in the upload response
                if upload_response.error is None:
                    # Get the public URL of the uploaded profile picture
                    profile_picture_url = supabase_client.storage().from_('profileImages').get_public_url(f"{username}/{file_name}")
                    st.success("Profile picture uploaded successfully!")

                    # Update the user table with the profile picture URL
                    update_response = supabase_client.table('user').update({
                        'profilePicture': profile_picture_url
                    }).eq('username', username).execute()

                    if update_response.get('error') is None:
                        st.success("Profile picture updated successfully!")
                    else:
                        st.error(f"Failed to update profile picture: {update_response.error}")
                else:
                    st.error(f"Failed to upload profile picture: {upload_response.error}")

            # Update the rest of the user profile data
            update_response = supabase_client.table('user').update({
                'caloriesBurnPerDay': calories_burn,
                'durationPerWorkout': duration_workout,
                'workoutFrequencyPerWeek': frequency_workout
            }).eq('username', username).execute()

            # Check for an error in the update response
            if update_response.error is None:
                st.success("Profile updated successfully!")
            else:
                st.error(f"An error occurred while updating the profile: {update_response.error}")

    else:
        st.error("User data not found.")
