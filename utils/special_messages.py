"""
ACME Questionnaire Bot - Special Messages Processor

Functions for processing special messages from the AI.
"""
import json
import streamlit as st
from config import TOPIC_AREAS

def process_special_messages(message_content):
    """
    Process special message formats from the AI.
    
    Args:
        message_content (str): The message content to process
        
    Returns:
        bool: True if the message was processed as a special message, False otherwise
    """
    processed = False
    
    # Check for topic updates - key format change to make detection more reliable
    if "TOPIC_UPDATE:" in message_content:
        try:
            # Extract the JSON part - everything after TOPIC_UPDATE:
            json_str = message_content.split("TOPIC_UPDATE:")[1].strip()
            # Sometimes the AI might add additional text after the JSON
            json_str = json_str.split("\n")[0].strip()
            
            # Log the extracted string for debugging
            print(f"Extracted JSON string: {json_str}")
            
            topic_updates = json.loads(json_str)
            
            # Update the session state
            for topic, status in topic_updates.items():
                if topic in st.session_state.topic_areas_covered:
                    st.session_state.topic_areas_covered[topic] = status
                    print(f"Updated topic {topic} to {status}")
            
            # Check for near completion and proactively ask about missing topics
            covered_count = sum(st.session_state.topic_areas_covered.values())
            total_topics = len(st.session_state.topic_areas_covered)
            
            # If we're near completion (3+ sections covered), check for missing topics
            if covered_count >= 3:
                missing_topics = [t for t, v in st.session_state.topic_areas_covered.items() if not v]
                if missing_topics:
                    # Add system message to explicitly ask about missing topics
                    missing_topics_str = ", ".join([TOPIC_AREAS[t] for t in missing_topics])
                    st.session_state.chat_history.append({
                        "role": "system",
                        "content": f"IMPORTANT: The following sections have not been covered yet: {missing_topics_str}. Focus your next questions specifically on these sections until all are covered."
                    })
                    print(f"Added system message about missing topics: {missing_topics_str}")
                    
            processed = True
        except Exception as e:
            print(f"Error processing topic update: {e}")
            # If there's an error, still return True to avoid displaying the message
            processed = True
    
    # Check for summary request
    if "SUMMARY_REQUEST" in message_content or "summary_requested = True" in message_content:
        print("Summary request detected!")
        
        # Only set summary_requested if ALL topics are covered
        all_topics_covered = all(st.session_state.topic_areas_covered.values())
        if all_topics_covered:
            # All sections covered, allow summary
            st.session_state.summary_requested = True
        else:
            # Add a system message to focus on missing topics
            missing_topics = [t for t, v in st.session_state.topic_areas_covered.items() if not v]
            missing_topics_str = ", ".join([TOPIC_AREAS[t] for t in missing_topics])
            st.session_state.chat_history.append({
                "role": "system",
                "content": f"The user has requested a summary, but the following sections have not been covered: {missing_topics_str}. Please inform the user that these sections need to be addressed before completing the questionnaire, and ask specifically about these sections."
            })
        
        processed = True
    
    # Return whether the message was processed
    return processed

def detect_conversation_loop(messages, threshold=3):
    """
    Detect if the conversation is stuck in a loop asking for the same information.
    
    Args:
        messages: List of message dictionaries
        threshold: Number of similar messages to consider a loop
        
    Returns:
        bool: True if a loop is detected, False otherwise
    """
    if len(messages) < threshold * 2:
        return False
    
    # Look at only assistant messages
    assistant_messages = [msg["content"] for msg in messages if msg["role"] == "assistant"]
    
    if len(assistant_messages) < threshold:
        return False
    
    # Check the last few messages from the assistant
    recent_messages = assistant_messages[-threshold:]
    
    # Check if all recent messages are asking for the same information (name/company)
    name_company_requests = 0
    for msg in recent_messages:
        if "name" in msg.lower() and "company" in msg.lower():
            name_company_requests += 1
    
    # If all recent messages are asking for the same thing, we're in a loop
    return name_company_requests == threshold

def add_system_guidance():
    """Add system guidance to help the AI with the conversation flow."""
    
    # Check which sections are covered and which are not
    covered_sections = []
    uncovered_sections = []
    
    for topic, covered in st.session_state.topic_areas_covered.items():
        if covered:
            covered_sections.append(TOPIC_AREAS[topic])
        else:
            uncovered_sections.append(TOPIC_AREAS[topic])
    
    # If we have both covered and uncovered sections, add guidance
    if covered_sections and uncovered_sections:
        covered_str = ", ".join(covered_sections)
        uncovered_str = ", ".join(uncovered_sections)
        
        guidance = f"""
        Based on the conversation so far, we have covered: {covered_str}.
        
        We still need to cover: {uncovered_str}.
        
        In your next messages, please focus on gathering information about the uncovered sections.
        """
        
        # Add the guidance as a system message
        st.session_state.chat_history.append({
            "role": "system",
            "content": guidance
        })
        
        return True
    
    return False