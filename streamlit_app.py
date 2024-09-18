import asyncio
import streamlit as st
from streamlit.web.bootstrap import run
from st_socketio import get_sio_asgi_app, init_socketio
from workout import workout_page  # Import workout page
from profile import profile_page  # Import profile page
from login import login_page  # Import login page

# Initialize Socket.IO
init_socketio()

def main():
    st.set_page_config(layout="wide", page_icon=":material/fitness_center:", page_title="Smart Fitness Trainer")

    # Ensure session state key initialization
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "workout"  # Default to workout page

    # Navigation logic
    if st.session_state.get("authenticated"):
        # Switch between pages based on session state
        if st.session_state['current_page'] == 'workout':
            workout_page()
        elif st.session_state['current_page'] == 'profile':
            profile_page()
    else:
        login_page()

async def run_streamlit():
    sio_app = get_sio_asgi_app()
    await run(
        main_script_path="streamlit_app.py",
        command_line=[],
        args=[],
        flag_options={},
        asgi_app=sio_app
    )

if __name__ == "__main__":
    asyncio.run(run_streamlit())