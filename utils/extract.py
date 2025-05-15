"""
ACME Questionnaire Bot - Extraction Utilities

Functions for extracting information from user responses.
"""
import streamlit as st
from services.ai_service import get_ai_response

def extract_user_info(user_input):
    """
    Extract user name and company from the first response.
    
    Args:
        user_input (str): The user's input text
    
    Returns:
        dict: Dictionary with name and company information
    """
    # Extract name and company from response to first question
    extract_messages = [
        {"role": "system", "content": "Extract the user name and organization name from this response to the question 'Could you please provide your name and your organization name?'. Even if the response is brief or partial, try to identify name and organization information."},
        {"role": "user", "content": f"User response: {user_input}\nExtract only the name and organization. Format your response exactly as: NAME: [name], ORGANIZATION: [organization]. If you can only extract one of these, still provide it and use 'unknown' for the other."}
    ]
    extract_response = get_ai_response(extract_messages)
    
    try:
        # Parse the extraction response
        name_part = "unknown"
        company_part = "unknown"
        
        if "NAME:" in extract_response:
            name_part = extract_response.split("NAME:")[1].split(",")[0].strip()
            name_part = name_part.replace("[", "").replace("]", "")
            
        if "ORGANIZATION:" in extract_response or "COMPANY:" in extract_response:
            # Handle both possible labels
            if "ORGANIZATION:" in extract_response:
                company_part = extract_response.split("ORGANIZATION:")[1].strip()
            else:
                company_part = extract_response.split("COMPANY:")[1].strip()
                
            company_part = company_part.replace("[", "").replace("]", "")
        
        # Only update if we found something useful
        if name_part != "unknown" or company_part != "unknown":
            st.session_state.user_info = {
                "name": name_part if name_part != "unknown" else "",
                "company": company_part if company_part != "unknown" else ""
            }
            
            # Add this information to the AI context to prevent redundant questions
            context_message = {"role": "system", "content": f"The user's name is {name_part if name_part != 'unknown' else 'not provided yet'} and they work for {company_part if company_part != 'unknown' else 'an organization that has not been mentioned yet'}. If you know the user's name, address them by it. Do not ask for name or organization information again if it has been provided."}
            st.session_state.chat_history.append(context_message)
            
            # If we only got partial info, immediately ask for the rest
            if name_part == "unknown" or company_part == "unknown":
                if name_part == "unknown" and company_part != "unknown":
                    follow_up = {"role": "system", "content": f"The user has mentioned their organization ({company_part}) but not their name. In your next response, thank them for the organization information and ask for their name."}
                    st.session_state.chat_history.append(follow_up)
                elif name_part != "unknown" and company_part == "unknown":
                    follow_up = {"role": "system", "content": f"The user has mentioned their name ({name_part}) but not their organization. In your next response, address them by name and ask for their organization name."}
                    st.session_state.chat_history.append(follow_up)
                    
            return st.session_state.user_info
    except Exception as e:
        print(f"Could not extract user information: {e}")
        return {"name": "", "company": ""}

def multi_answer_detection(user_input, current_question):
    """
    Detect if a user response answers multiple questions at once.
    
    Args:
        user_input (str): The user's input text
        current_question (str): The current question being asked
        
    Returns:
        list: List of additional topics covered by the response
    """
    from services.ai_service import get_ai_response
    
    # Check if this answer also provides information for future questions
    multi_answer_check = [
        {"role": "system", "content": "Analyze if this user response answers multiple questions at once. Identify any additional topics covered beyond the current question."},
        {"role": "user", "content": f"Current question: {current_question}\nUser response: {user_input}\nCheck if this response covers information about any of these additional topics: crew_manager_usage, emergency_contract_ops, resources_reporting, current_practices.\nRespond with a JSON object listing any additional topics covered, like {{'additional_topics': ['topic1', 'topic2']}}. If no additional topics, respond with {{'additional_topics': []}}"}
    ]
    
    try:
        multi_answer_response = get_ai_response(multi_answer_check)
        if "additional_topics" in multi_answer_response:
            import json
            # Try to extract the JSON part
            json_part = multi_answer_response.split("{", 1)[1].rsplit("}", 1)[0]
            json_str = "{" + json_part + "}"
            additional_topics = json.loads(json_str).get("additional_topics", [])
            
            # If additional topics were found, add a system message about it
            if additional_topics:
                topics_str = ", ".join(additional_topics)
                st.session_state.chat_history.append({
                    "role": "system", 
                    "content": f"The user's response also provided information about these additional topics: {topics_str}. Take this into account and avoid asking questions about these topics if the information has already been provided."
                })
                
                # Update the topic coverage based on additional topics
                for topic in additional_topics:
                    if topic in st.session_state.topic_areas_covered:
                        st.session_state.topic_areas_covered[topic] = True
                        
            return additional_topics
    except Exception as e:
        # If we hit an error processing multi-answers, just continue normally
        print(f"Error in multi-answer detection: {e}")
        
    return []