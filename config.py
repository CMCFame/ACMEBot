"""
ACME Questionnaire Bot - Configuration

Central configuration settings and constants for the application.
"""
import os

# Application metadata
APP_TITLE = "ACME Questionnaire"
APP_DESCRIPTION = "Help us understand your organization's requirements for Crew Manager"
APP_LOGO_URL = "https://placekitten.com/200/50"  # Replace with actual ACME logo

# Application sections for topic tracking
TOPIC_AREAS = {
    'crew_manager_usage': "Section 1: Crew Manager Usage",
    'emergency_contract_ops': "Section 2: Emergency and Contract Operations",
    'resources_reporting': "Section 3: Resources and Reporting",
    'current_practices': "Section 4: Current Practices and Needs"
}

# File paths
QUESTIONS_FILE = "data/questions.txt"
PROMPT_FILE = "data/prompt.txt"

# OpenAI settings
OPENAI_MODEL = "gpt-4o-2024-08-06"
OPENAI_TEMPERATURE = 0.7
OPENAI_MAX_TOKENS = 150

# Cookie settings
COOKIE_PREFIX = "acme_"
COOKIE_NAME = "conversation_context"

# Email settings
SMTP_SERVER_DEFAULT = "smtp.gmail.com"
SMTP_PORT_DEFAULT = 587