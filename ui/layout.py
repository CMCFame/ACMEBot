"""
ACME Questionnaire Bot - UI Layout

UI layout components and styling for the application.
"""
import streamlit as st
from config import APP_TITLE, APP_DESCRIPTION, APP_LOGO_URL

def apply_css():
    """Apply custom CSS styling to the application."""
    css = """
    /* Red and White Color Palette */
    :root {
        --primary-red: #D22B2B;
        --light-red: #F8D7DA;
        --dark-red: #A61C1C;
        --white: #FFFFFF;
        --light-gray: #F5F5F5;
        --text-dark: #333333;
    }

    /* Main container and general styles */
    .main {
        padding: 20px;
        color: var(--text-dark);
    }

    /* Logo container */
    .logo-container {
        padding: 10px;
        margin-bottom: 20px;
    }

    /* Header styling */
    h1, h2, h3 {
        color: var(--primary-red);
    }

    /* Improve form button styling */
    div[data-testid="stForm"] button {
        background-color: var(--primary-red);
        color: var(--white);
        border-radius: 20px;
        padding: 8px 20px;
        border: none;
        transition: all 0.3s;
    }

    div[data-testid="stForm"] button:hover {
        background-color: var(--dark-red);
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
    }

    /* Style text inputs */
    div[data-testid="stTextInput"] input {
        border-radius: 8px;
        border: 1px solid #ddd;
        padding: 10px 15px;
        transition: border 0.3s;
    }

    div[data-testid="stTextInput"] input:focus {
        border-color: var(--primary-red);
        box-shadow: 0 0 0 1px var(--primary-red);
    }

    /* Style download buttons */
    .stDownloadButton button {
        background-color: var(--primary-red);
        color: var(--white);
        border: none;
        border-radius: 20px;
        padding: 8px 16px;
        font-weight: 500;
        transition: all 0.3s;
    }

    .stDownloadButton button:hover {
        background-color: var(--dark-red);
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
    }

    /* Style the sidebar */
    section[data-testid="stSidebar"] {
        background-color: var(--light-gray);
        border-right: 1px solid #eee;
    }

    /* Make help button more prominent */
    button[data-testid="baseButton-secondary"] {
        background-color: var(--light-red);
        color: var(--dark-red);
        border: 1px solid var(--dark-red);
        border-radius: 20px;
        transition: all 0.3s;
        min-width: 100px;
        padding: 0.5rem 1rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    button[data-testid="baseButton-secondary"]:hover {
        background-color: var(--primary-red);
        color: var(--white);
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: var(--light-gray);
        border-radius: 4px 4px 0 0;
        padding: 8px 16px;
        border: 1px solid #ddd;
        border-bottom: none;
    }

    .stTabs [aria-selected="true"] {
        background-color: var(--primary-red);
        color: var(--white);
    }
    
    /* Progress tracker */
    .progress-container {
        margin: 20px 0;
    }
    
    .progress-bar {
        height: 20px;
        background-color: var(--light-red);
        border-radius: 10px;
    }
    
    .progress-fill {
        height: 100%;
        background-color: var(--primary-red);
        border-radius: 10px;
    }
    """
    
    # Apply the CSS
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

def setup_tabs():
    """Set up the application tabs and their content."""
    tab1, tab2, tab3 = st.tabs(["Questionnaire", "Instructions", "FAQ"])
    
    # Questionnaire tab header
    with tab1:
        # Add ACME logo above the header
        st.markdown(
            f"""
            <div style="text-align: center; margin-bottom: 10px;">
                <img src="{APP_LOGO_URL}" alt="ACME Logo" style="max-width: 200px; height: auto;" />
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Page header
        st.markdown(
            f"""
            <div style="text-align: center; padding: 10px 0 20px 0;">
                <h1 style="color: #D22B2B; margin-bottom: 5px;">{APP_TITLE}</h1>
                <p style="color: #555; font-size: 16px;">
                    {APP_DESCRIPTION}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Instructions tab content
    with tab2:
        setup_instructions_tab()
    
    # FAQ tab content
    with tab3:
        setup_faq_tab()
    
    return tab1, tab2, tab3

def setup_instructions_tab():
    """Set up the content for the Instructions tab."""
    st.markdown("## How to Use the ACME Questionnaire")
    
    st.markdown("""
    ### Welcome to the ACME Questionnaire!
    
    This tool is designed to gather detailed information about your organization's current practices and how Crew Manager can support your operations. Follow these simple instructions to complete the questionnaire:
    
    #### Getting Started
    1. Enter your name and organization name when prompted
    2. Answer each question to the best of your ability
    3. If you need to take a break, use the "Save Progress" button in the sidebar
    
    #### Special Features
    
    * **Need Help?** - Click the "Need help?" button below any question to get a detailed explanation
    * **Examples** - Click the "Example" button to see sample responses for the current question
    * **Save Progress** - Save your work at any time using the sidebar option
    * **Resume Later** - Upload your saved file to continue where you left off
    
    #### Navigation Tips
    
    * Answer one question at a time
    * The progress bar shows how many sections you've completed
    * All 4 sections must be covered to complete the questionnaire
    * When complete, you'll receive a summary you can download
    
    #### Sections Covered
    
    1. **Crew Manager Usage** - Situations, daily crew assignments, resources, work assignments
    2. **Emergency and Contract Operations** - Mutual assistance crews, contract crews, lodging
    3. **Resources and Reporting** - Additional crew/resources, availability tracking, Crew Manager roles
    4. **Current Practices and Needs** - Current tools, reporting, data organization
    
    If you have any questions about the questionnaire, please check the FAQ tab or contact your implementation consultant.
    """)

def setup_faq_tab():
    """Set up the content for the FAQ tab."""
    st.markdown("## Frequently Asked Questions")
    
    # Using expanders for each FAQ item
    with st.expander("What is the ACME Questionnaire?"):
        st.write("""
        The ACME Questionnaire is a tool designed to gather detailed information about your organization's 
        current practices and how Crew Manager can support your operations. This information helps our 
        solution consultants understand your specific requirements and configure the Crew Manager system 
        to match your existing workflows.
        """)
        
    with st.expander("How long does it take to complete?"):
        st.write("""
        The questionnaire typically takes 15-20 minutes to complete, depending on the complexity of your 
        operations. You can save your progress at any time and return to complete it later.
        """)
        
    with st.expander("Can I save my progress and continue later?"):
        st.write("""
        Yes! Use the "Save Progress" button in the sidebar to download your current progress as a file. 
        When you return, use the "Resume from file" option to upload your saved file and continue where you left off.
        """)
        
    with st.expander("What if I don't know the answer to a question?"):
        st.write("""
        If you're unsure about any question, click the "Need help?" button for a detailed explanation. 
        If you still don't know, provide your best understanding and make a note that this area may need 
        further discussion with your implementation consultant.
        """)
        
    with st.expander("Will my answers be saved automatically?"):
        st.write("""
        No, your answers are not saved automatically. Be sure to use the "Save Progress" button in the sidebar 
        to save your work before closing the application.
        """)
        
    with st.expander("Who will see my responses?"):
        st.write("""
        Your responses will be shared with the implementation team assigned to your project. 
        The information is used solely for configuring your Crew Manager system to match your requirements.
        """)
        
    with st.expander("What happens after I complete the questionnaire?"):
        st.write("""
        After completion, you'll receive a summary of your responses that you can download. 
        A notification will also be sent to your implementation consultant, who will review 
        your responses and schedule a follow-up discussion to clarify any points as needed.
        """)
        
    with st.expander("How do I change an answer I've already provided?"):
        st.write("""
        If you need to change a previous answer, you'll need to save your progress, then restart the 
        questionnaire by refreshing the page and uploading your saved file. You can then continue through 
        the questions until you reach the one you want to change.
        """)
        
    with st.expander("Technical Issues or Questions?"):
        st.write("""
        If you encounter any technical issues with the questionnaire or have questions that aren't 
        answered here, please contact your implementation consultant or email support@example.com.
        """)