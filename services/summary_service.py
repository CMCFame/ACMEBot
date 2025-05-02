"""
ACME Questionnaire Bot - Summary Service

Functions for generating summaries of the conversation.
"""
import streamlit as st
from datetime import datetime
from collections import OrderedDict
from config import TOPIC_AREAS

def generate_conversation_summary():
    """
    Generate a summary of the conversation as a formatted string.
    
    Returns:
        str: Formatted summary text
    """
    # Extract all question-answer pairs from the conversation
    summary_pairs = []
    current_question = ""
    
    # Process conversation in order
    for i in range(len(st.session_state.visible_messages)):
        message = st.session_state.visible_messages[i]
        
        # Identify questions from the assistant (excluding examples)
        if message["role"] == "assistant" and "?" in message["content"]:
            question_content = message["content"]
            
            # Skip example text when identifying the question
            if "*Example:" in question_content:
                parts = question_content.split("*Example:")
                if len(parts) > 1 and "?" in parts[1]:
                    # Look for the real question after the example
                    lines = parts[1].split("\n")
                    for line in lines:
                        if "?" in line and not line.startswith("*Example:"):
                            current_question = line.strip()
                            break
            else:
                # Extract the question - look for the last sentence with a question mark
                sentences = question_content.split(". ")
                for sentence in reversed(sentences):
                    if "?" in sentence:
                        current_question = sentence.strip()
                        break
        
        # If user message follows a question, it's likely an answer (except examples)
        elif message["role"] == "user" and current_question and i > 0:
            # Skip if this is just an example request
            if message["content"].lower().strip() in ["example", "can you show me an example?", "show example"]:
                continue
                
            # This is an actual answer - add it to our pairs
            summary_pairs.append((current_question, message["content"]))
            current_question = ""  # Reset current question
    
    # Format the summary as a string
    summary = "# ACME Questionnaire Summary\n\n"
    summary += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    if st.session_state.user_info["name"] or st.session_state.user_info["company"]:
        summary += f"## User Information\n"
        if st.session_state.user_info["name"]:
            summary += f"Name: {st.session_state.user_info['name']}\n"
        if st.session_state.user_info["company"]:
            summary += f"Organization: {st.session_state.user_info['company']}\n"
        summary += "\n"
    
    summary += "## Questionnaire Responses\n\n"
    
    # Categorizing responses based on sections from the ACME template
    section_mapping = {
        "crew": "Section 1: Crew Manager Usage",
        "daily crew": "Section 1: Crew Manager Usage",
        "daily resource": "Section 1: Crew Manager Usage",
        "work assignments": "Section 1: Crew Manager Usage",
        "situation": "Section 1: Crew Manager Usage",
        
        "mutual assistance": "Section 2: Emergency and Contract Operations",
        "contract crews": "Section 2: Emergency and Contract Operations",
        "lodging": "Section 2: Emergency and Contract Operations",
        "emergency": "Section 2: Emergency and Contract Operations",
        
        "additional crew": "Section 3: Resources and Reporting",
        "tracking crew": "Section 3: Resources and Reporting",
        "crew manager usage": "Section 3: Resources and Reporting",
        "resources": "Section 3: Resources and Reporting",
        "availability": "Section 3: Resources and Reporting",
        
        "current crew": "Section 4: Current Practices and Needs",
        "crew management reporting": "Section 4: Current Practices and Needs",
        "data organization": "Section 4: Current Practices and Needs",
        "reports": "Section 4: Current Practices and Needs",
        "tools": "Section 4: Current Practices and Needs"
    }
    
    # Define the preferred order of sections
    section_order = [
        "Section 1: Crew Manager Usage", 
        "Section 2: Emergency and Contract Operations", 
        "Section 3: Resources and Reporting", 
        "Section 4: Current Practices and Needs",
        "Other"
    ]
    
    # Initialize ordered dict with empty lists for each section
    section_buckets = OrderedDict()
    for section in section_order:
        section_buckets[section] = []
    
    # Add "Other" for anything that doesn't match
    section_buckets["Other"] = []
    
    # Improved categorization algorithm
    for question, answer in summary_pairs:
        section_assigned = False
        
        # Combine question and answer text for better matching
        combined_text = (question + " " + answer).lower()
        
        # Find the best matching section
        for keyword, section in section_mapping.items():
            if keyword.lower() in combined_text:
                # If we find a match, assign to this section
                section_buckets[section].append((question, answer))
                section_assigned = True
                break
        
        # If no match found, assign to "Other"
        if not section_assigned:
            section_buckets["Other"].append((question, answer))
    
    # Add sections to summary
    for section, qa_pairs in section_buckets.items():
        if qa_pairs:  # Only include sections that have QA pairs
            summary += f"### {section}\n\n"
            for question, answer in qa_pairs:
                summary += f"**Q: {question}**\n\n"
                summary += f"A: {answer}\n\n"
    
    return summary