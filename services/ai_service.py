"""
ACME Questionnaire Bot - AI Service

Functions for interacting with OpenAI API.
"""
import openai
import streamlit as st
from config import OPENAI_MODEL, OPENAI_TEMPERATURE, OPENAI_MAX_TOKENS

def initialize_openai_client():
    """
    Initialize the OpenAI client with API key from Streamlit secrets.
    
    Returns:
        OpenAI: Initialized OpenAI client
    """
    try:
        client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        return client
    except Exception as e:
        st.error(f"Error initializing OpenAI client: {e}")
        st.error("Please check that OPENAI_API_KEY is set in your Streamlit secrets.")
        st.stop()

def get_ai_response(messages):
    """
    Get a response from the OpenAI API.
    
    Args:
        messages (list): List of message dictionaries with role and content
        
    Returns:
        str: The AI's response text
    """
    try:
        # Initialize the OpenAI client
        client = initialize_openai_client()
        
        # Call the API
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=OPENAI_MAX_TOKENS,
            temperature=OPENAI_TEMPERATURE
        )
        
        return response.choices[0].message.content.strip()
    except openai.APIError as e:
        error_msg = f"Error: {e}"
        print(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        print(error_msg)
        return error_msg