"""
ACME Questionnaire Bot - Session Management

Functions for managing the session state and user interactions.
"""
import os
import json
import streamlit as st
from datetime import datetime
from services.ai_service import get_ai_response
from utils.file_loader import load_questions, load_instructions
from config import QUESTIONS_FILE, PROMPT_FILE, TOPIC_AREAS

def initialize_session_state():
    """Initialize the session state if it hasn't been initialized yet."""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
        st.session_state.responses = []
        st.session_state.chat_history = []
        st.session_state.visible_messages = []
        st.session_state.current_question_index = 0
        st.session_state.questions = load_questions(QUESTIONS_FILE)
        st.session_state.current_question = st.session_state.questions[0]
        st.session_state.instructions = load_instructions(PROMPT_FILE)
        st.session_state.chat_history = [{"role": "system", "content": st.session_state.instructions}]
        st.session_state.user_info = {"name": "", "company": ""}
        st.session_state.consecutive_empty_responses = 0
        st.session_state.download_timestamp = datetime.now().strftime('%Y%m%d')
        
        # Initialize topic tracking
        st.session_state.topic_areas_covered = {
            'crew_manager_usage': False,
            'emergency_contract_ops': False,
            'resources_reporting': False,
            'current_practices': False
        }
        st.session_state.total_topics = len(st.session_state.topic_areas_covered)
        st.session_state.summary_requested = False
        st.session_state.previous_summary_request = False
        
        # Add restoration flag to prevent loops
        st.session_state.restoring_session = False        
        
        # Add initial greeting that includes the first question
        welcome_message = "👋 Hello! This questionnaire is designed to help solution consultants better understand your organization's requirements for Crew Manager. If you're unsure about any question, simply type a ? and I'll provide a brief explanation. You can also type 'example' or click the 'Example' button to see a sample response.\n\nLet's get started! Could you please provide your name and your organization name?"
        st.session_state.chat_history.append({"role": "assistant", "content": welcome_message})
        st.session_state.visible_messages.append({"role": "assistant", "content": welcome_message})
        
        st.session_state.initialized = True
        st.session_state.email_sent = False

def export_session_data():
    """Create a JSON-serializable copy of the session data."""
    # Create a clean copy of chat history and visible messages
    safe_chat_history = []
    for msg in st.session_state.chat_history:
        if isinstance(msg, dict) and "role" in msg and "content" in msg:
            safe_chat_history.append({"role": msg["role"], "content": msg["content"]})
    
    safe_visible_messages = []
    for msg in st.session_state.visible_messages:
        if isinstance(msg, dict) and "role" in msg and "content" in msg:
            safe_visible_messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Create the data dictionary with only serializable items
    data = {
        "user_info": dict(st.session_state.get("user_info", {})),
        "responses": [(q, a) for q, a in list(st.session_state.responses)],  # Ensure list of tuples
        "current_question_index": st.session_state.current_question_index,
        "chat_history": safe_chat_history,
        "visible_messages": safe_visible_messages,
        "topic_areas_covered": dict(st.session_state.topic_areas_covered)
    }
    
    # Add debugging mechanism
    try:
        # Test serialization before returning
        json.dumps(data)
        return data
    except TypeError as e:
        # If serialization fails, log the error and create a more stripped-down version
        print(f"Serialization error: {e}")
        # Fallback to even more basic version
        minimal_data = {
            "user_info": {"name": st.session_state.user_info.get("name", ""), 
                         "company": st.session_state.user_info.get("company", "")},
            "responses": [(str(q), str(a)) for q, a in st.session_state.responses],
            "current_question_index": st.session_state.current_question_index,
            "chat_history": [{"role": "system", "content": "Session restored"}],
            "visible_messages": []
        }
        return minimal_data

def import_session_data(data):
    """Import session data from a saved state."""
    try:
        # Set a flag to prevent infinite reruns
        if st.session_state.get("restoring_session", False):
            # Already in the process of restoring, don't rerun again
            return True
        
        # Mark that we're restoring a session
        st.session_state.restoring_session = True
        
        # Restore session state from imported data
        st.session_state.user_info = data.get("user_info", {})
        st.session_state.responses = data.get("responses", [])
        st.session_state.current_question_index = data.get("current_question_index", 0)
        
        # Ensure chat history has system prompt
        if "chat_history" in data and len(data["chat_history"]) > 0:
            st.session_state.chat_history = data.get("chat_history", [])
        else:
            # If no chat history, initialize with system prompt
            st.session_state.chat_history = [{"role": "system", "content": st.session_state.instructions}]
            
        st.session_state.visible_messages = data.get("visible_messages", [])
        
        # Restore topic areas if available
        if "topic_areas_covered" in data:
            for topic, status in data["topic_areas_covered"].items():
                if topic in st.session_state.topic_areas_covered:
                    st.session_state.topic_areas_covered[topic] = status
        
        # Set current question
        if st.session_state.current_question_index < len(st.session_state.questions):
            st.session_state.current_question = st.session_state.questions[st.session_state.current_question_index]
        else:
            # Handle edge case where index is out of bounds
            st.session_state.current_question_index = 0
            st.session_state.current_question = st.session_state.questions[0]
            
        return True
    except Exception as e:
        st.error(f"Error importing session data: {e}")
        st.session_state.restoring_session = False
        return False

def process_user_input(user_input, cookies=None):
    """Process user input and update the session state accordingly."""
    from utils.special_messages import process_special_messages
    from utils.extract import extract_user_info
    from ui.components import display_completion_summary

    # Check if input is empty or just whitespace
    if not user_input or user_input.isspace():
        st.error("Please enter a message before sending.")
        return
    
    # Process non-empty input
    elif user_input.lower().strip() in ["example", "show example", "give me an example", "example answer"]:
        handle_example_request(user_input)
        
    # Check if user is requesting a summary or indicating frustration
    elif user_input.lower().strip() in ["summary", "download", "download summary", "get summary", "show summary", "yes", "provide summary"] or any(phrase in user_input.lower() for phrase in ["already answered", "not helpful", "i already responded"]):
        handle_summary_request(user_input)
        
    else:
        # Regular user message processing
        
        # Add user input to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.visible_messages.append({"role": "user", "content": user_input})
        
        # For the first question, extract user and company name
        if st.session_state.current_question_index == 0:
            extract_user_info(user_input)
        
        # Get AI response
        ai_response = get_ai_response(st.session_state.chat_history)
        
        # Check if this is a special message
        is_special = process_special_messages(ai_response)
        
        # Add the response to visible messages if not special
        if not is_special:
            st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
            st.session_state.visible_messages.append({"role": "assistant", "content": ai_response})
            
            # Force a topic update check after each response
            check_topic_coverage()
            
        # Check if this is an answer to the current question
        handle_question_advancement(user_input)
    
    # Display completion summary if requested
    if st.session_state.get("summary_requested", False):
        display_completion_summary()
    
    # Rerun the app to update the UI
    st.rerun()

def handle_example_request(user_input):
    """Handle an example request from the user."""
    from services.ai_service import get_ai_response
    
    # Find the last question asked by the assistant
    last_question = None
    for msg in reversed(st.session_state.visible_messages):
        if msg["role"] == "assistant":
            # Extract the last question from the assistant's message
            last_question = msg["content"]
            break
    
    # Create message context
    example_messages = st.session_state.chat_history.copy()
    
    # Add a system message that ensures the example is for the CURRENT question
    example_messages.append({
        "role": "system", 
        "content": f"""
        Provide an example answer for the LAST question you asked. The example MUST be directly relevant to what you just asked the user.
        
        Format your response EXACTLY as follows, including the spacing:
        
        *Example: "[your example here]"*
        
        [BLANK LINE]
        
        To continue with our question, [restate the original question in full]
        
        Note: There must be a completely blank line between the example and the question to create visual separation.
        """
    })
    
    # Get the example response
    example_response = get_ai_response(example_messages)
    
    # Add to chat history
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    st.session_state.chat_history.append({"role": "assistant", "content": example_response})
    st.session_state.visible_messages.extend([
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": example_response}
    ])

def handle_summary_request(user_input):
    """Handle a summary request from the user."""
    # If user is frustrated or explicitly requesting summary multiple times, override strict checks
    force_summary = any(phrase in user_input.lower() for phrase in ["already answered", "not helpful", "i already responded", "already responded"]) or st.session_state.get("previous_summary_request", False)
    
    # Track that user has requested summary before
    st.session_state["previous_summary_request"] = True
    
    # Add user message to chat history
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    st.session_state.visible_messages.append({"role": "user", "content": user_input})
    
    # Force summary if user is requesting it again or showing frustration
    if force_summary:
        st.session_state.summary_requested = True
        
        # Force all topics to be marked as covered
        for topic in st.session_state.topic_areas_covered:
            st.session_state.topic_areas_covered[topic] = True
            
        # Add a response from assistant
        summary_confirm = "I'll prepare a summary of your responses. You can download it below."
        st.session_state.chat_history.append({"role": "assistant", "content": summary_confirm})
        st.session_state.visible_messages.append({"role": "assistant", "content": summary_confirm})
    else:
        # Check if all topics are covered
        all_topics_covered = all(st.session_state.topic_areas_covered.values())
        
        if all_topics_covered:
            st.session_state.summary_requested = True
            summary_confirm = "I'll prepare a summary of your responses. You can download it below."
            st.session_state.chat_history.append({"role": "assistant", "content": summary_confirm})
            st.session_state.visible_messages.append({"role": "assistant", "content": summary_confirm})
        else:
            # If not all topics are covered, ask about missing topics
            missing_topics = [TOPIC_AREAS[t] for t, v in st.session_state.topic_areas_covered.items() if not v]
            missing_topics_str = ", ".join(missing_topics)
            missing_response = f"I see you'd like a summary, but we still have a few important areas to cover: {missing_topics_str}. Let's quickly address these topics so we can complete your questionnaire."
            
            st.session_state.chat_history.append({"role": "assistant", "content": missing_response})
            st.session_state.visible_messages.append({"role": "assistant", "content": missing_response})

def handle_question_advancement(user_input):
    """Check if the user input should advance to the next question."""
    from services.ai_service import get_ai_response
    
    if st.session_state.current_question_index < len(st.session_state.questions):
        messages_for_check = [
            {"role": "system", "content": "You are helping to determine if a user message is an answer to a question or a request for help/clarification."},
            {"role": "user", "content": f"Question: {st.session_state.current_question}\nUser message: {user_input}\nIs this a direct answer to the question or a request for help/clarification? Reply with exactly 'ANSWER' or 'QUESTION'."}
        ]
        response_type = get_ai_response(messages_for_check)
        
        if "ANSWER" in response_type.upper():
            # Special handling for "Yes" responses to summary questions
            if "summary" in st.session_state.current_question.lower() and user_input.lower().strip() in ["yes", "yeah", "sure", "ok", "okay"]:
                # Treat as a summary request
                handle_summary_request(user_input)
            else:
                # Store answer and advance to next question
                st.session_state.responses.append((st.session_state.current_question, user_input))
                st.session_state.current_question_index += 1
                if st.session_state.current_question_index < len(st.session_state.questions):
                    st.session_state.current_question = st.session_state.questions[st.session_state.current_question_index]

def check_topic_coverage():
    """Check which topics have been covered and update system prompts."""
    from services.ai_service import get_ai_response
    
    # Force a topic update message after each regular response
    topic_check_messages = st.session_state.chat_history.copy()
    topic_check_messages.append({
        "role": "system", 
        "content": "Based on all conversation so far, which sections have been covered? Respond ONLY with a TOPIC_UPDATE message that includes the status of ALL topic areas."
    })
    
    topic_update_response = get_ai_response(topic_check_messages)
    from utils.special_messages import process_special_messages
    process_special_messages(topic_update_response)
    
    # Check if we're at 3+ sections and force a check for missing sections
    covered_count = sum(st.session_state.topic_areas_covered.values())
    if covered_count >= 3:
        missing_topics = [TOPIC_AREAS[t] for t, v in st.session_state.topic_areas_covered.items() if not v]
        if missing_topics:
            missing_topics_str = ", ".join(missing_topics)
            focus_message = {
                "role": "system", 
                "content": f"IMPORTANT: Focus on gathering information about these remaining sections in your next questions: {missing_topics_str}"
            }
            st.session_state.chat_history.append(focus_message)