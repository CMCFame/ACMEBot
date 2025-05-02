"""
ACME Questionnaire Bot - Cookie Manager

Functions for managing cookies to save and restore progress.
"""
import os
import json
import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager
from config import COOKIE_PREFIX, COOKIE_NAME
from utils.session import export_session_data, import_session_data

def init_cookie_manager():
    """Initialize the cookie manager for saving/loading progress."""
    cookie_password = os.environ.get("COOKIES_PASSWORD")
    if not cookie_password:
        st.error("The cookie encryption password (COOKIES_PASSWORD) is not set. Please configure this in your environment.")
        st.stop()

    cookies = EncryptedCookieManager(
        prefix=COOKIE_PREFIX,
        password=cookie_password,
    )

    if not cookies.ready():
        st.stop()

    return cookies

def save_to_cookies(cookies):
    """Save the conversation context to cookies."""
    try:
        context_data = export_session_data()
        cookies[COOKIE_NAME] = json.dumps(context_data)
        cookies.save()
        st.success("Progress successfully saved!")
        return True
    except Exception as e:
        st.error(f"Error saving progress: {e}")
        return False

def load_from_cookies(cookies):
    """Restore the conversation context from cookies."""
    try:
        context_json = cookies.get(COOKIE_NAME)
        if not context_json:
            st.error("No saved context found.")
            return False

        context_data = json.loads(context_json)
        
        if import_session_data(context_data):
            st.success("Progress successfully restored!")
            return True
        else:
            st.error("Could not restore progress from cookie")
            return False
    except Exception as e:
        st.error(f"Error restoring progress: {e}")
        return False

def add_save_load_ui(cookies):
    """Add save/load UI in the sidebar."""
    with st.sidebar:
        # Logo and header
        st.markdown("""
            <div style="text-align: center; margin-bottom: 25px;">
                <img src="https://placekitten.com/200/50"
                     alt="ACME Logo" style="max-width: 80%; height: auto; margin: 10px auto;" />
            </div>
            <div style="text-align: center;">
                <h3 style="color: var(--primary-red); margin-bottom: 10px;">
                    <i>Save & Resume Progress</i>
                </h3>
                <p style="font-size: 0.9em; color: #555; margin-bottom: 20px;">
                    Save your progress at any time and continue later.
                </p>
            </div>
        """, unsafe_allow_html=True)

        # Save Progress button
        if st.button("💾 Save Progress", key="save_progress"):
            save_to_cookies(cookies)

        st.markdown("---")

        # Resume from Cookie button
        if st.button("🔄 Resume from Cookie", key="load_cookie"):
            if load_from_cookies(cookies):
                st.rerun()

        st.markdown("---")

        # File upload option for resuming progress
        st.markdown("### Or Upload Progress File")
        uploaded_file = st.file_uploader("Choose a saved progress file", type=["json"], key="progress_file")
        
        if uploaded_file is not None:
            try:
                # Read file content as string
                content = uploaded_file.read().decode("utf-8")
                
                # Parse the JSON data
                data = json.loads(content)
                
                # Load button only shows after file is uploaded
                if st.button("📤 Load from File", key="load_file"):
                    if import_session_data(data):
                        st.success("✅ Progress restored from file!")
                        st.rerun()
                    else:
                        st.error("Could not restore progress from file")
            except json.JSONDecodeError:
                st.error("Invalid JSON file format")
            except Exception as e:
                st.error(f"Error processing file: {e}")
                print(f"File load error: {e}")