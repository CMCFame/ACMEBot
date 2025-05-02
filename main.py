"""
ACME Questionnaire Bot - Main Application

Entry point for the ACME Questionnaire Bot application.
"""
import streamlit as st
from ui.layout import apply_css, setup_tabs
from ui.components import display_chat_history, create_input_form
from utils.cookie_manager import init_cookie_manager, add_save_load_ui
from utils.session import initialize_session_state, process_user_input
from config import APP_TITLE, APP_DESCRIPTION

def main():
    """Main application entry point."""
    # Set page configuration
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="📋",
        layout="wide"
    )
    
    # Apply custom CSS
    apply_css()
    
    # Initialize cookie manager for saving/loading progress
    cookies = init_cookie_manager()
    
    # Add save/load UI to sidebar
    add_save_load_ui(cookies)
    
    # Initialize session state if not already done
    initialize_session_state()
    
    # Set up the tabs for the UI
    tab1, tab2, tab3 = setup_tabs()
    
    # Questionnaire tab content
    with tab1:
        # Display progress indicator if applicable
        if st.session_state.current_question_index > 0:
            # Calculate progress percentage
            covered_sections = sum(st.session_state.topic_areas_covered.values())
            total_sections = len(st.session_state.topic_areas_covered)
            progress_pct = int((covered_sections / total_sections) * 100)
            
            # Display progress bar
            st.markdown(
                f"""
                <div style="margin: 20px 0;">
                    <div style="display: flex; align-items: center; margin-bottom: 5px;">
                        <div style="flex-grow: 1; height: 20px; background-color: #f0f2f6; border-radius: 10px; overflow: hidden;">
                            <div style="width: {progress_pct}%; height: 100%; background-color: var(--primary-red); border-radius: 10px;"></div>
                        </div>
                        <div style="margin-left: 10px; font-weight: bold;">{progress_pct}%</div>
                    </div>
                    <p style="text-align: center; margin: 0; color: #555;">
                        {covered_sections} of {total_sections} sections covered
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # Display chat history
        display_chat_history()
        
        # Display the input form for user responses
        user_input, submit_button = create_input_form()
        
        # Process user input when submitted
        if submit_button and user_input:
            process_user_input(user_input, cookies)
    
if __name__ == "__main__":
    main()