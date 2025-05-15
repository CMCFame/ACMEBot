"""
ACME Questionnaire Bot - Project Initialization Script

This script initializes the directory structure and creates needed files.
"""
import os
import json
import shutil

def init_project():
    """Initialize the project structure and files."""
    print("Initializing ACME Questionnaire Bot project...")
    
    # Create directory structure
    directories = [
        "data",
        "exports",
        "services",
        "ui",
        "utils"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Create empty __init__.py files in each directory
    for directory in directories:
        with open(os.path.join(directory, "__init__.py"), "w") as f:
            f.write("# Module initialization file\n")
        print(f"Created __init__.py in {directory}")
    
    # Create sample data files if they don't exist
    if not os.path.exists("data/questions.txt"):
        questions = """Could you please provide your name and your organization name?
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
            f.write(questions)
        print("Created sample questions.txt file")
    
    # Create sample prompt.txt file if it doesn't exist
    if not os.path.exists("data/prompt.txt"):
        prompt = """# Mode 
You are a helpful, friendly, and professional AI chatbot designed to gather detailed information about organizations using the ACME Crew Manager Customer Use Case Questionnaire. Your primary goal is to collect comprehensive information through a natural conversation flow that adapts based on previous responses.

# Context 
This questionnaire is intended for clients to help solution consultants understand the customer's requirements better. The questionnaire focuses on how Crew Manager can support the organization's operations and covers key areas like crew management usage, emergency operations, resources and reporting, and current practices.

# Tone
Use a friendly, professional tone. Address the user by name when possible. Be helpful and stay on subject. If the user asks for anything unrelated to the questionnaire, politely explain that you don't have the answer for that and redirect to the questionnaire.

# Topics to Cover
1. Crew Manager Usage - Situations, daily crew assignments, resources, work assignments
2. Emergency and Contract Operations - Mutual assistance crews, contract crews, lodging
3. Resources and Reporting - Additional crew/resources, availability tracking, Crew Manager roles
4. Current Practices and Needs - Current tools, reporting, data organization

# Conversation Structure
Ask ONE question at a time and wait for a response before moving to the next question. Pay close attention to the user's answers to determine which question path to follow.

# IMPORTANT: Complete Section Coverage
It is CRUCIAL that you ensure ALL 4 sections are fully covered before suggesting completion."""
        
        with open("data/prompt.txt", "w") as f:
            f.write(prompt)
        print("Created sample prompt.txt file")
    
    # Create a sample .streamlit/secrets.toml file template
    os.makedirs(".streamlit", exist_ok=True)
    if not os.path.exists(".streamlit/secrets.toml"):
        secrets = """# API Keys
OPENAI_API_KEY = "your-openai-api-key"
COOKIES_PASSWORD = "your-secure-cookie-password"

# Email Configuration
EMAIL_SENDER = ""
EMAIL_PASSWORD = ""
EMAIL_RECIPIENT = ""
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
"""
        
        with open(".streamlit/secrets.toml", "w") as f:
            f.write(secrets)
        print("Created sample .streamlit/secrets.toml template")
    
    # Create requirements.txt file
    if not os.path.exists("requirements.txt"):
        requirements = """streamlit>=1.28.0
openai>=1.0.0
pandas>=2.0.0
streamlit-cookies-manager>=0.2.0
xlsxwriter>=3.0.0
openpyxl>=3.0.0
markdown>=3.4.0
python-dotenv>=1.0.0
"""
        
        with open("requirements.txt", "w") as f:
            f.write(requirements)
        print("Created requirements.txt file")
    
    print("\nACME Questionnaire Bot project initialized successfully!")
    print("\nNext steps:")
    print("1. Edit '.streamlit/secrets.toml' to set your OpenAI API key and other secrets")
    print("2. Run 'pip install -r requirements.txt' to install dependencies")
    print("3. Start the application with 'streamlit run main.py'")

if __name__ == "__main__":
    init_project()