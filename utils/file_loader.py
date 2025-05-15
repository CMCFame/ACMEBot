"""
ACME Questionnaire Bot - File Loader

Functions for loading questions and instructions from files.
"""
import os
import streamlit as st

def load_instructions(file_path):
    """
    Load the AI instructions from a text file.
    
    Args:
        file_path (str): Path to the instructions file
        
    Returns:
        str: The instructions content
    """
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        st.error(f"Instructions file not found: {file_path}")
        # Provide a minimal fallback instruction
        return "You are an AI assistant helping with a questionnaire about crew management."
    except Exception as e:
        st.error(f"Error loading instructions: {e}")
        return "Error loading instructions."

def load_questions(file_path):
    """
    Load questions from a text file.
    
    Args:
        file_path (str): Path to the questions file
        
    Returns:
        list: List of questions
    """
    try:
        with open(file_path, 'r') as file:
            # Read all questions, one per line
            questions = []
            for line in file:
                line = line.strip()
                if line:
                    # Remove the number and period at the beginning of the line if present
                    # Example format: "1. Question text"
                    parts = line.split('. ', 1)
                    if len(parts) > 1 and parts[0].isdigit():
                        questions.append(parts[1])
                    else:
                        questions.append(line)
            return questions
    except FileNotFoundError:
        st.error(f"Questions file not found: {file_path}")
        # Provide a minimal set of fallback questions
        return [
            "Could you please provide your name and your organization name?",
            "In what situations will crew management be used by your organization?",
            "How are you currently managing daily crew assignments?",
            "How do you manage daily resource assignments?",
            "How are you assigning work to crews or members?"
        ]
    except Exception as e:
        st.error(f"Error loading questions: {e}")
        return ["Could you please provide your name and your organization name?"]

def create_directory_structure():
    """Create the necessary directory structure if it doesn't exist."""
    
    # Create data directory for questions and prompt
    os.makedirs("data", exist_ok=True)
    
    # Create directory for exports
    os.makedirs("exports", exist_ok=True)
    
    # Check if questions.txt exists, if not create it with default questions
    if not os.path.exists("data/questions.txt"):
        default_questions = """Could you please provide your name and your organization name?
In what situations will crew management be used by your organization?
How frequently will you use crew management?
How are you currently managing daily crew assignments?
What information is needed for daily operations of crews?
How do you manage daily resource assignments?
How are resources like equipment or vehicles allocated to crews or members?
How are you currently assigning work to a crew or member?
How are you assigning mutual assistance crews?
What is your approach to obtaining these crews during high-demand scenarios?
How are you assigning contract crews?
What is your approach to obtaining contractors for operations?
How are you assigning lodging?
What are your special considerations for lodging?
What additional crew, crew member or resources do you track?
How are crews or resources managed when not assigned to a crew?
How are you currently tracking crew member availability?
Who in your organization will be using Crew Manager?
What are their roles and specific needs?
Describe how your current crew management tools are used.
What reports are currently printed and distributed?
How would you like data to be organized or filtered?
What is the significance of data organization in your operations?"""
        
        with open("data/questions.txt", "w") as f:
            f.write(default_questions)