import os
import streamlit as st
import json
from streamlit_cookies_manager import EncryptedCookieManager

# -------------------------------------------------------------------
# COOKIE MANAGER INITIALIZATION
# -------------------------------------------------------------------
def init_cookie_manager():
    cookie_password = os.environ.get("COOKIES_PASSWORD")
    if not cookie_password:
        st.error("The cookie encryption password (COOKIES_PASSWORD) is not set. Please configure this in your environment.")
        st.stop()

    cookies = EncryptedCookieManager(
        prefix="ace_",
        password=cookie_password,
    )

    if not cookies.ready():
        st.stop()

    return cookies

cookies = init_cookie_manager()

# -------------------------------------------------------------------
# SAVE CONVERSATION CONTEXT TO COOKIE
# -------------------------------------------------------------------
def save_conversation_context(cookies):
    try:
        context_data = {
            "user_info": st.session_state.user_info or {"name": "", "company": ""},
            "responses": st.session_state.responses or [],
            "current_question_index": st.session_state.current_question_index,
            "chat_history": st.session_state.chat_history or [],
            "visible_messages": st.session_state.visible_messages or [],
            "topic_areas_covered": st.session_state.topic_areas_covered or {},
        }

        cookies["conversation_context"] = json.dumps(context_data)
        cookies.save()
        st.success("Progress successfully saved!")
        return True

    except Exception as e:
        st.error(f"Error saving progress: {e}")
        return False

# -------------------------------------------------------------------
# RESTORE CONVERSATION CONTEXT FROM COOKIE
# -------------------------------------------------------------------
def restore_conversation_context(cookies):
    try:
        context_json = cookies.get("conversation_context")
        if not context_json:
            st.error("No saved context found.")
            return False

        context_data = json.loads(context_json)

        st.session_state.user_info = context_data.get("user_info", {"name": "", "company": ""})
        st.session_state.responses = context_data.get("responses", [])
        st.session_state.current_question_index = context_data.get("current_question_index", 0)
        st.session_state.chat_history = context_data.get("chat_history", [])
        st.session_state.visible_messages = context_data.get("visible_messages", [])
        st.session_state.topic_areas_covered = context_data.get("topic_areas_covered", {})

        st.success("Progress successfully restored!")
        return True

    except Exception as e:
        st.error(f"Error restoring progress: {e}")
        return False

# -------------------------------------------------------------------
# ADD SAVE/LOAD UI IN SIDEBAR
# -------------------------------------------------------------------
def add_save_load_ui(cookies):
    with st.sidebar:
        st.markdown("### Save & Resume Progress")

        if st.button("💾 Save Progress"):
            save_conversation_context(cookies)

        st.markdown("---")

        if st.button("🔄 Resume Progress"):
            if restore_conversation_context(cookies):
                st.rerun()

        st.markdown("---")

        st.markdown("### Upload Progress File")
        uploaded_file = st.file_uploader("Upload JSON", type=["json"])

        if uploaded_file:
            try:
                context_data = json.load(uploaded_file)
                st.session_state.user_info = context_data.get("user_info", {"name": "", "company": ""})
                st.session_state.responses = context_data.get("responses", [])
                st.session_state.current_question_index = context_data.get("current_question_index", 0)
                st.session_state.chat_history = context_data.get("chat_history", [])
                st.session_state.visible_messages = context_data.get("visible_messages", [])
                st.session_state.topic_areas_covered = context_data.get("topic_areas_covered", {})

                st.success("Progress restored from uploaded file.")
                st.rerun()

            except Exception as e:
                st.error(f"Error loading from file: {e}")
# -------------------------------------------------------------------
# Now import the rest of your dependencies
# -------------------------------------------------------------------
import openai
import pandas as pd
import smtplib
import json
import base64
import markdown
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
from io import BytesIO

#==============================================================================
# MODULE: API CONFIGURATION
#==============================================================================
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

#==============================================================================
# MODULE: FILE LOADING FUNCTIONS
#==============================================================================
def load_instructions(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def load_questions(file_path):
    with open(file_path, 'r') as file:
        # Skip question numbers and just store the actual questions
        questions = []
        for line in file:
            line = line.strip()
            if line:
                # Remove the number and period at the beginning of the line
                # Assuming format like "1. Question text"
                parts = line.split('. ', 1)
                if len(parts) > 1:
                    questions.append(parts[1])
                else:
                    questions.append(line)  # No number found, add the whole line
        return questions

#==============================================================================
# MODULE: AI INTERACTION
#==============================================================================
def get_openai_response(messages):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=messages,
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except openai.APIError as e:
        return f"Error: {e}"

#==============================================================================
# MODULE: DATA EXPORT FUNCTIONS
#==============================================================================
def generate_csv(answers):
    df = pd.DataFrame(answers, columns=['Question', 'Answer'])
    return df.to_csv(index=False).encode('utf-8')

def generate_excel(answers):
    try:
        df = pd.DataFrame(answers, columns=['Question', 'Answer'])
        output = BytesIO()
        
        # Try to use xlsxwriter if available
        try:
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Responses')
        except (ImportError, ModuleNotFoundError):
            # Fall back to openpyxl if xlsxwriter isn't available
            try:
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Responses')
            except (ImportError, ModuleNotFoundError):
                # If neither Excel writer is available, raise a more helpful error
                st.error("Excel export is not available. Missing required dependencies. CSV export is still available.")
                raise ImportError("Excel export libraries (xlsxwriter or openpyxl) not available")
                
        return output.getvalue()
    except Exception as e:
        st.error(f"Could not generate Excel file: {e}")
        # Return CSV as fallback
        return df.to_csv(index=False).encode('utf-8')

#==============================================================================
# MODULE: EMAIL NOTIFICATION
#==============================================================================
def send_email(user_info, answers, completed=False):
    try:
        # Get email settings from secrets
        sender_email = st.secrets.get("EMAIL_SENDER", "")
        sender_password = st.secrets.get("EMAIL_PASSWORD", "")
        recipient_email = st.secrets.get("EMAIL_RECIPIENT", "")
        smtp_server = st.secrets.get("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = st.secrets.get("SMTP_PORT", 587)
        
        if not sender_email or not sender_password or not recipient_email:
            st.warning("Email configuration not complete. Notification email not sent.")
            return False
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        
        # Set subject based on whether questionnaire was completed
        status = "completed" if completed else "in progress"
        msg['Subject'] = f"ACE Questionnaire {status} - {user_info['name']} from {user_info['company']}"
        
        # Create email body
        body = f"""
        <html>
        <body>
        <h2>ACE Questionnaire Submission</h2>
        <p><strong>Status:</strong> {"Completed" if completed else "In Progress"}</p>
        <p><strong>User:</strong> {user_info['name']}</p>
        <p><strong>Company:</strong> {user_info['company']}</p>
        <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))
        
        # Create and attach CSV file (more reliable than Excel)
        csv_data = generate_csv(answers)
        attachment = MIMEApplication(csv_data)
        attachment.add_header('Content-Disposition', 'attachment', 
                             filename=f"ACE_Questionnaire_{user_info['company']}_{datetime.now().strftime('%Y%m%d')}.csv")
        msg.attach(attachment)
        
        # Try to also attach Excel file if available
        try:
            excel_data = generate_excel(answers)
            # Skip if we got CSV back instead (fallback when Excel libs aren't available)
            if not excel_data[:10].decode('utf-8', errors='ignore').startswith("Question,Answer"):
                excel_attachment = MIMEApplication(excel_data)
                excel_attachment.add_header('Content-Disposition', 'attachment', 
                                filename=f"ACE_Questionnaire_{user_info['company']}_{datetime.now().strftime('%Y%m%d')}.xlsx")
                msg.attach(excel_attachment)
        except Exception:
            # Excel format failed, but we already have CSV, so continue
            pass
            
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False

#==============================================================================
# MODULE: UI CHAT DISPLAY
#==============================================================================
def display_chat_history():
    for message in st.session_state.visible_messages:
        # USER MESSAGES
        if message["role"] == "user":
            user_label = st.session_state.user_info.get("name", "You") or "You"
            st.markdown(
                f"""
                <div style="display: flex; justify-content: flex-end; margin-bottom: 10px;">
                  <div style="background-color: #e6f7ff; border-radius: 15px 15px 0 15px; padding: 10px 15px; max-width: 80%; box-shadow: 1px 1px 3px rgba(0,0,0,0.1);">
                    <p style="margin: 0; color: #333;"><strong>{user_label}</strong></p>
                    <p style="margin: 0; white-space: pre-wrap;">{message["content"]}</p>
                  </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # ASSISTANT MESSAGES
        elif message["role"] == "assistant":
            content = message["content"]

            # HELP BOX
            if "I need help with this question" in content:
                help_text = content.replace("I need help with this question", "").strip()
                st.markdown(
                    f"""
                    <div class="ai-help">
                      <p style="margin: 0;"><strong>Help:</strong> {help_text}</p>
                    </div>
                    <br>
                    """,
                    unsafe_allow_html=True
                )

            # EXAMPLE BOX
            elif content.strip().startswith("Example:"):
                example_text = content.strip()[len("Example:"):].strip()
                st.markdown(
                    f"""
                    <div class="ai-example">
                      <p style="margin: 0;"><strong>Example:</strong> {example_text}</p>
                    </div>
                    <br>
                    """,
                    unsafe_allow_html=True
                )

            # REGULAR ASSISTANT MESSAGE
            else:
                st.markdown(
                    f"""
                    <div style="display: flex; margin-bottom: 10px;">
                      <div style="background-color: #f0f2f6; border-radius: 15px 15px 15px 0; padding: 10px 15px; max-width: 80%; box-shadow: 1px 1px 3px rgba(0,0,0,0.1);">
                        <p style="margin: 0; color: #333;"><strong>Assistant</strong></p>
                        <p style="margin: 0; white-space: pre-wrap;">{content}</p>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
#==============================================================================
# MODULE: SESSION MANAGEMENT
#==============================================================================
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
        
#==============================================================================
# MODULE: SPECIAL MESSAGE PROCESSING
#==============================================================================
def process_special_messages(message_content):
    """Process special message formats from the AI."""
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
            
            # If we're near completion (7+ topics covered), check for missing topics
            if covered_count >= 7:
                missing_topics = [t for t, v in st.session_state.topic_areas_covered.items() if not v]
                if missing_topics:
                    # Add system message to explicitly ask about missing topics
                    missing_topics_str = ", ".join(missing_topics)
                    st.session_state.chat_history.append({
                        "role": "system",
                        "content": f"IMPORTANT: The following topics have not been covered yet: {missing_topics_str}. Focus your next questions specifically on these topics until all are covered."
                    })
                    print(f"Added system message about missing topics: {missing_topics_str}")
                    
            # Check for specific critical questions that might be missed
            if covered_count >= 6:  # When most topics are covered, check for specific gaps
                # Define critical questions that must be asked
                critical_questions = {
                    "contact_process": [
                        "why do you call this person first",
                        "how many devices do employees have",
                        "which device is called first and why"
                    ],
                    "list_management": [
                        "are lists based on attributes other than job classification",
                        "how exactly do you call the list (straight down, in order)",
                        "do you skip around on lists based on qualifications or status",
                        "are there pauses between calls"
                    ],
                    "insufficient_staffing": [
                        "do you offer positions to people not normally called",
                        "do you consider or call the whole list again",
                        "do you always follow these procedures the same way",
                        "are there situations where you handle this differently"
                    ],
                    "additional_rules": [
                        "are there rules that excuse declined callouts near shifts or vacations"
                    ]
                }
                
                # Add missing critical questions to the system prompt
                for topic, questions in critical_questions.items():
                    if st.session_state.topic_areas_covered.get(topic, False):
                        # Check conversation history for these specific questions
                        conversation_text = " ".join([msg.get("content", "") for msg in st.session_state.chat_history 
                                                    if isinstance(msg, dict) and msg.get("role") == "assistant"])
                        
                        missing_questions = []
                        for question in questions:
                            if question.lower() not in conversation_text.lower():
                                missing_questions.append(question)
                        
                        if missing_questions:
                            question_str = ", ".join(missing_questions)
                            st.session_state.chat_history.append({
                                "role": "system",
                                "content": f"IMPORTANT: Although the {topic} topic is marked as covered, you have not specifically asked about: {question_str}. Please ask about these points before moving to other topics."
                            })
            
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
            # Do a final verification of critical questions before allowing summary
            critical_questions_asked = True
            conversation_text = " ".join([msg.get("content", "") for msg in st.session_state.chat_history 
                                        if isinstance(msg, dict) and msg.get("content", "")])

            # Check for key phrases that should appear in a complete conversation
            key_phrases = [
                "why do you call first", "how many devices", "which device is called first",
                "attributes other than job classification", "straight down the list", "skip around",
                "pauses between calls", "offer positions to people not normally", "call the whole list again",
                "always handle insufficient staffing", "situations where you handle differently",
                "rules that excuse declined callouts"
            ]

            missing_phrases = []
            for phrase in key_phrases:
                if phrase.lower() not in conversation_text.lower():
                    missing_phrases.append(phrase)
                    critical_questions_asked = False

            if critical_questions_asked:
                # All critical questions asked, allow summary
                st.session_state.summary_requested = True
            else:
                # Don't allow summary yet, ask about missing items
                missing_str = ", ".join(missing_phrases)
                st.session_state.chat_history.append({
                    "role": "system",
                    "content": f"The user has requested a summary, but several critical items have not been discussed: {missing_str}. Inform the user that a few more questions are needed for a complete assessment."
                })
        else:
            # Add a system message to focus on missing topics
            missing_topics = [t for t, v in st.session_state.topic_areas_covered.items() if not v]
            missing_topics_str = ", ".join(missing_topics)
            st.session_state.chat_history.append({
                "role": "system",
                "content": f"The user has requested a summary, but the following topics have not been covered: {missing_topics_str}. Please inform the user that these topics need to be addressed before completing the questionnaire, and ask specifically about these topics."
            })
        
        processed = True
    
    # Return whether the message was processed
    return processed

#==============================================================================
# MODULE: CONVERSATION MONITORING
#==============================================================================
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

#==============================================================================
# MODULE: SUMMARY GENERATION
#==============================================================================
def generate_conversation_summary():
    """Generate a summary of the conversation as a formatted string."""
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
    summary = "# ACE Questionnaire Summary\n\n"
    summary += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    if st.session_state.user_info["name"] or st.session_state.user_info["company"]:
        summary += f"## User Information\n"
        if st.session_state.user_info["name"]:
            summary += f"Name: {st.session_state.user_info['name']}\n"
        if st.session_state.user_info["company"]:
            summary += f"Company: {st.session_state.user_info['company']}\n"
        summary += "\n"
    
    summary += "## Questionnaire Responses\n\n"
    
    # Enhanced categorization for more accurate topic mapping
    enhanced_topic_mapping = {
        # Basic Information
        "name": "Basic Information",
        "company": "Basic Information",
        "situation": "Basic Information", 
        "frequent": "Basic Information",
        "callout type": "Basic Information",
        "callout occur": "Basic Information",
        
        # Staffing Details
        "employee": "Staffing Details",
        "staff": "Staffing Details",
        "role": "Staffing Details",
        "classification": "Staffing Details",
        "journeymen": "Staffing Details",
        "apprentice": "Staffing Details",
        "supervisor": "Staffing Details",
        
        # Contact Process
        "contact first": "Contact Process",
        "contact when": "Contact Process",
        "who do you contact": "Contact Process",
        "device": "Contact Process",
        "phone": "Contact Process",
        "call first": "Contact Process",
        "why are they contacted": "Contact Process",
        
        # List Management
        "list": "List Management",
        "skip": "List Management",
        "traverse": "List Management",
        "straight down": "List Management",
        "order": "List Management",
        "pause": "List Management",
        "organized": "List Management",
        
        # Insufficient Staffing
        "required number": "Insufficient Staffing",
        "don't get": "Insufficient Staffing",
        "not enough": "Insufficient Staffing",
        "secondary list": "Insufficient Staffing",
        "part-time": "Insufficient Staffing",
        "whole list again": "Insufficient Staffing",
        "can't get enough": "Insufficient Staffing",
        "neighboring district": "Insufficient Staffing",
        "contractor": "Insufficient Staffing",
        "short-staffed": "Insufficient Staffing",
        
        # Calling Logistics
        "simultaneous": "Calling Logistics",
        "call again": "Calling Logistics",
        "second pass": "Calling Logistics",
        "nobody else accepts": "Calling Logistics",
        "all device": "Calling Logistics",
        "ensure quick response": "Calling Logistics",
        
        # List Changes
        "change": "List Changes",
        "update": "List Changes",
        "overtime hours": "List Changes",
        "new hire": "List Changes",
        "transfer": "List Changes",
        "content of the list": "List Changes",
        "pay period": "List Changes",
        
        # Tiebreakers
        "tie": "Tiebreakers",
        "tiebreaker": "Tiebreakers",
        "seniority": "Tiebreakers",
        "alphabetical": "Tiebreakers",
        "rotating": "Tiebreakers",
        
        # Additional Rules
        "text alert": "Additional Rules",
        "email": "Additional Rules",
        "rule": "Additional Rules",
        "shift": "Additional Rules",
        "exempt": "Additional Rules",
        "rest": "Additional Rules",
        "hour": "Additional Rules",
        "excuse": "Additional Rules",
        "declined callout": "Additional Rules"
    }
    
    # Use OrderedDict to maintain consistent topic order
    from collections import OrderedDict
    
    # Define the preferred order of topics
    topic_order = [
        "Basic Information", 
        "Staffing Details", 
        "Contact Process", 
        "List Management", 
        "Insufficient Staffing", 
        "Calling Logistics",
        "List Changes", 
        "Tiebreakers", 
        "Additional Rules"
    ]
    
    # Initialize ordered dict with empty lists for each topic
    topic_buckets = OrderedDict()
    for topic in topic_order:
        topic_buckets[topic] = []
    
    # Add "Other" for anything that doesn't match
    topic_buckets["Other"] = []
    
    # Improved categorization algorithm
    for question, answer in summary_pairs:
        topic_assigned = False
        best_match_topic = None
        max_matches = 0
        
        # Combine question and answer text for better matching
        combined_text = (question + " " + answer).lower()
        
        # Count matches for each topic's keywords
        for topic in topic_order:
            keyword_matches = 0
            topic_keywords = [kw for kw, t in enhanced_topic_mapping.items() if t == topic]
            
            for keyword in topic_keywords:
                if keyword.lower() in combined_text:
                    keyword_matches += 1
            
            # Track the topic with the most keyword matches
            if keyword_matches > max_matches:
                max_matches = keyword_matches
                best_match_topic = topic
        
        # Assign to best matching topic if we found any matches
        if max_matches > 0:
            topic_buckets[best_match_topic].append((question, answer))
            topic_assigned = True
        
        # If no match found, assign to "Other"
        if not topic_assigned:
            topic_buckets["Other"].append((question, answer))
    
    # Add topics to summary
    for topic, qa_pairs in topic_buckets.items():
        if qa_pairs:  # Only include topics that have QA pairs
            summary += f"### {topic}\n\n"
            for question, answer in qa_pairs:
                summary += f"**Q: {question}**\n\n"
                summary += f"A: {answer}\n\n"
    
    return summary

#==============================================================================
# MODULE: MAIN APPLICATION
#==============================================================================
def main():
    # Explicitly declare cookies as global to avoid UnboundLocalError
    global cookies
    import json  # Make sure json is imported within the main function scope
    
    # Define CSS with red and white color palette
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
    
    # Add this test cookie section right after applying the CSS
    # Simple test of cookie functionality
    if st.button("Test Cookie"):
        try:
            # Set a simple test cookie
            cookies["test_cookie"] = "test_value"
            cookies.save()
            st.success(f"Test cookie set. Value: {cookies.get('test_cookie')}")
            print(f"Test cookie set with value: test_value")
        except Exception as e:
            st.error(f"Cookie test error: {e}")
    
    # Add the debugging section here as well
    with st.expander("Cookie Debugging"):
        st.write("Cookie Status:")
        st.write(f"Cookie manager ready: {cookies.ready()}")
        
        try:
            # Test several known cookies without accessing _cookies directly
            test_keys = ["test_cookie", "conversation_context", "progress"]
            cookie_values = {}
            for key in test_keys:
                value = cookies.get(key)
                cookie_values[key] = "Found" if value else "Not found"
            
            st.write("Cookies found:", cookie_values)
        except Exception as e:
            st.write(f"Error checking cookies: {e}")
        
        # Add test buttons
        if st.button("Set Test Cookie", key="set_debug_cookie"):
            try:
                cookies["debug_cookie"] = "working"
                cookies.save()
                st.success("Test cookie set!")
            except Exception as e:
                st.error(f"Error setting cookie: {e}")
        
        if st.button("Check Test Cookie", key="check_debug_cookie"):
            try:
                value = cookies.get("debug_cookie")
                if value:
                    st.success(f"Test cookie found: {value}")
                else:
                    st.error("Test cookie not found!")
            except Exception as e:
                st.error(f"Error checking cookie: {e}")
        # Add button to clear a specific cookie        
        if st.button("Clear progress cookie", key="clear_progress"):
            try:
                # Instead of trying to delete from _cookies directly
                cookies["progress"] = None
                cookies.save()
                st.success("Progress cookie cleared")
            except Exception as e:
                st.error(f"Error clearing cookie: {e}")
                
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Questionnaire", "Instructions", "FAQ"])

    with tab1:
        # Add ARCOS logo above the header
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 10px;">
                <img src="https://www.publicpower.org/sites/default/files/logo-arcos_0.png" alt="ARCOS Logo" style="max-width: 200px; height: auto;" />
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # SECTION: PAGE HEADER
        st.markdown(
            """
            <div style="text-align: center; padding: 10px 0 20px 0;">
                <h1 style="color: #D22B2B; margin-bottom: 5px;">ACE Questionnaire</h1>
                <p style="color: #555; font-size: 16px;">
                    Help us understand your company's requirements for ARCOS implementation
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    with tab2:
        # Instructions Tab Content
        st.markdown("## How to Use the ACE Questionnaire")
        
        st.markdown("""
        ### Welcome to the ACE Questionnaire!
        
        This tool is designed to gather detailed information about your utility company's callout processes for ARCOS implementation. Follow these simple instructions to complete the questionnaire:
        
        #### Getting Started
        1. Enter your name and company name when prompted
        2. Answer each question to the best of your ability
        3. If you need to take a break, use the "Save Progress" button in the sidebar
        
        #### Special Features
        
        * **Need Help?** - Click the "Need help?" button below any question to get a detailed explanation
        * **Examples** - Click the "Example" button to see sample responses for the current question
        * **Save Progress** - Save your work at any time using the sidebar option
        * **Resume Later** - Upload your saved file to continue where you left off
        
        #### Navigation Tips
        
        * Answer one question at a time
        * The progress bar shows how many topic areas you've completed
        * All 9 topic areas must be covered to complete the questionnaire
        * When complete, you'll receive a summary you can download
        
        #### Topic Areas Covered
        
        1. Basic Information - User, company, callout types
        2. Staffing Details - Employee requirements and roles
        3. Contact Process - First contact and methods
        4. List Management - Organization and traversal
        5. Insufficient Staffing - Alternative procedures
        6. Calling Logistics - Simultaneous calls, callbacks
        7. List Changes - Updates to ordering and content
        8. Tiebreakers - Methods when ordering is equal
        9. Additional Rules - Scheduling and exceptions
        
        If you have any questions about the questionnaire, please check the FAQ tab or contact your ARCOS implementation consultant.
        """)
    
    with tab3:
        # FAQ Tab Content
        st.markdown("## Frequently Asked Questions")
        
        # Using expanders for each FAQ item
        with st.expander("What is the ACE Questionnaire?"):
            st.write("""
            The ACE (ARCOS Configuration Exploration) Questionnaire is a tool designed to gather detailed information 
            about your utility company's callout processes. This information helps ARCOS solution consultants 
            understand your specific requirements and configure the ARCOS system to match your existing workflows.
            """)
            
        with st.expander("How long does it take to complete?"):
            st.write("""
            The questionnaire typically takes 15-20 minutes to complete, depending on the complexity of your 
            callout processes. You can save your progress at any time and return to complete it later.
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
            Your responses will be shared with the ARCOS implementation team assigned to your project. 
            The information is used solely for configuring your ARCOS system to match your requirements.
            """)
            
        with st.expander("What happens after I complete the questionnaire?"):
            st.write("""
            After completion, you'll receive a summary of your responses that you can download. 
            A notification will also be sent to your ARCOS implementation consultant, who will review 
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
            answered here, please contact your ARCOS implementation consultant or email support@arcos-inc.com.
            """)            
    
    #==========================================================================
    # SECTION: SESSION STATE INITIALIZATION
    #==========================================================================
    # Initialize session state
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
        st.session_state.responses = []
        st.session_state.chat_history = []
        st.session_state.visible_messages = []
        st.session_state.current_question_index = 0
        st.session_state.questions = load_questions('questions.txt')
        st.session_state.current_question = st.session_state.questions[0]
        st.session_state.instructions = load_instructions('prompt.txt')
        st.session_state.chat_history = [{"role": "system", "content": st.session_state.instructions}]
        st.session_state.user_info = {"name": "", "company": ""}
        st.session_state.consecutive_empty_responses = 0
        
        # Initialize topic tracking
        st.session_state.topic_areas_covered = {
            'basic_info': False,
            'staffing_details': False,
            'contact_process': False,
            'list_management': False,
            'insufficient_staffing': False,
            'calling_logistics': False,
            'list_changes': False,
            'tiebreakers': False,
            'additional_rules': False
        }
        st.session_state.total_topics = len(st.session_state.topic_areas_covered)
        st.session_state.summary_requested = False
        
        # Add flag to track summary requests
        st.session_state.previous_summary_request = False
        
        # Add initial greeting that includes the first question
        welcome_message = "👋 Hello! This questionnaire is designed to help ARCOS solution consultants better understand your company's requirements. If you're unsure about any question, simply type a ? and I'll provide a brief explanation. You can also type 'example' or click the 'Example' button to see a sample response.\n\nLet's get started! Could you please provide your name and your company name?"
        st.session_state.chat_history.append({"role": "assistant", "content": welcome_message})
        st.session_state.visible_messages.append({"role": "assistant", "content": welcome_message})
        
        # Add restoration flag to prevent loops
        if 'restoring_session' not in st.session_state:
            st.session_state.restoring_session = False        
        
        st.session_state.initialized = True
        st.session_state.email_sent = False

    # ==============================================================================
    # SECTION: SIDEBAR SAVE/LOAD OPTIONS
    # ==============================================================================
    with st.sidebar:
        st.markdown("""
            <div style="text-align: center; margin-bottom: 25px;">
                <img src="https://www.publicpower.org/sites/default/files/logo-arcos_0.png"
                     alt="Company Logo" style="max-width: 80%; height: auto; margin: 10px auto;" />
            </div>
            <div style="text-align: center;">
                <h3 style="color: var(--primary-red); margin-bottom: 10px;">
                    <i>Save & Resume Progress</i>
                </h3>
                <p style="font-size: 0.9em; color: #555; margin-bottom: 20px;">
                    Save your progress at any time and continue later.
                </p>
            </div>
        """, unsafe_allow_html=True)

        # Save Progress button
        if st.button("💾 Save Progress", key="save_progress"):
            try:
                # Create serializable data for both options
                session_data = export_session_data()
                
                # Try cookie first
                cookie_success = False
                try:
                    cookies["progress"] = json.dumps(session_data)
                    cookies.save()
                    if cookies.get("progress"):
                        st.success("✅ Progress saved to browser cookie!")
                        cookie_success = True
                        print("Cookie save successful")
                    else:
                        print("Cookie save failed verification")
                except Exception as cookie_e:
                    print(f"Cookie save error: {cookie_e}")
                
                # If cookie fails, offer file download
                if not cookie_success:
                    st.warning("Could not save to browser cookie. Use the file option instead:")
                    # Convert to JSON for download
                    json_data = json.dumps(session_data)
                    st.download_button(
                        label="📥 Download Progress File",
                        data=json_data,
                        file_name=f"ace_progress_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        key="download_progress"
                    )
            except Exception as e:
                st.error(f"Error saving progress: {e}")
                print(f"General save error: {e}")
        
        st.markdown("---")
        
        # Resume section
        st.markdown("### Resume Progress")
        
        # Load from Cookie button
        if st.button("🔄 Resume from Cookie", key="load_cookie"):
            try:
                saved_data = cookies.get("progress")
                if saved_data:
                    print(f"Found progress cookie with length: {len(saved_data)}")
                    data = json.loads(saved_data)
                    
                    if restore_conversation_context(data, from_cookie=True):
                        st.success("✅ Progress restored from cookie!")
                        st.rerun()
                    else:
                        st.error("Could not restore progress from cookie")
                else:
                    st.info("No saved progress found in browser cookie")
                    print("No progress cookie found")
            except Exception as e:
                st.error(f"Error loading from cookie: {e}")
                print(f"Cookie load error: {e}")
        
        # File upload option (always available regardless of cookie status)
        st.markdown("### Or Upload Progress File")
        uploaded_file = st.file_uploader("Choose a saved progress file", type=["json"], key="progress_file")
        
        if uploaded_file is not None:
            try:
                # Read file content as string
                content = uploaded_file.read().decode("utf-8")
                
                # Parse the JSON data
                data = json.loads(content)
                
                # Load button only shows after file is uploaded
                if st.button("📤 Load from File", key="load_file"):
                    if restore_conversation_context(data, from_cookie=False):
                        st.success("✅ Progress restored from file!")
                        st.rerun()
                    else:
                        st.error("Could not restore progress from file")
            except json.JSONDecodeError:
                st.error("Invalid JSON file format")
            except Exception as e:
                st.error(f"Error processing file: {e}")
                print(f"File load error: {e}")

    # ==============================================================================
    # SECTION: AFTER SIDEBAR – DEFINE TOTAL QUESTIONS
    # ==============================================================================
    total_questions = len(st.session_state.questions)

    #==========================================================================
    # SECTION: CHAT HISTORY DISPLAY
    #==========================================================================
    # Chat history
    with st.container():
        display_chat_history()

    #==========================================================================
    # SECTION: PROGRESS INDICATOR
    #==========================================================================
    # Progress indicator with enhanced styling - based on topics covered
    if st.session_state.current_question_index > 0:
        # Count covered topics
        covered_topics = sum(st.session_state.topic_areas_covered.values())
        total_topics = st.session_state.total_topics
        
        # Calculate percentage for display
        progress_pct = int((covered_topics / total_topics) * 100)
        
        # Custom progress bar with styling
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
                    {covered_topics} of {total_topics} topic areas covered
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    #==========================================================================
    # SECTION: CURRENT QUESTION DISPLAY WITH HELP/EXAMPLE BUTTONS
    #==========================================================================
    # Current question display - only show in chat history, not separately
    if st.session_state.current_question_index < total_questions:
        # Only add the buttons, not the question display (which will be in chat history)
        buttons_col1, buttons_col2 = st.columns(2)
        
        with buttons_col1:
            help_button = st.button("Need help?", key="help_button")
        
        with buttons_col2:
            # Use a shorter label for the example button
            example_button = st.button("Example", key="example_button")

        if help_button:
            # Get the current question context from the most recent assistant message
            last_question = None
            for msg in reversed(st.session_state.visible_messages):
                if msg["role"] == "assistant" and "?" in msg["content"]:
                    last_question = msg["content"]
                    break
            
            # Create help message context with clear instructions
            help_messages = st.session_state.chat_history.copy()
            help_messages.append({
                "role": "system", 
                "content": f"The user is asking for help with the CURRENT question which is: '{last_question}'. Provide a helpful explanation specifically for THIS question, not a previous one."
            })
            help_messages.append({"role": "user", "content": "I need help with this question"})
            
            help_response = get_openai_response(help_messages)
            
            # Add help interaction to chat history without advancing question
            st.session_state.chat_history.append({"role": "user", "content": "I need help with this question"})
            st.session_state.chat_history.append({"role": "assistant", "content": help_response})
            st.session_state.visible_messages.extend([
                {"role": "user", "content": "I need help with this question"},
                {"role": "assistant", "content": help_response}
            ])
            st.rerun()
        
        if example_button:
            # Create a more specific example request that includes the current question
            current_question = st.session_state.current_question
            
            # Extract the last assistant message to see what was actually asked
            last_assistant_message = None
            for msg in reversed(st.session_state.visible_messages):
                if msg["role"] == "assistant":
                    last_assistant_message = msg["content"]
                    break
            
            example_messages = st.session_state.chat_history.copy()
            
            # Add a system message that ensures the example is for the CURRENT question
            example_messages.append({
                "role": "system", 
                "content": f"""
                Provide ONLY an example answer for the LAST question you asked, which was: 
                "{last_assistant_message}"
                
                The example MUST be directly relevant to what you just asked the user.
                Format your response exactly as: *"Example: [your example here]"*
                
                After the example, repeat the last question verbatim so the user knows what to answer.
                """
            })
            
            # Get the example response
            example_response = get_openai_response(example_messages)
            
            # Add to chat history
            st.session_state.chat_history.append({"role": "user", "content": "Can you show me an example?"})
            st.session_state.chat_history.append({"role": "assistant", "content": example_response})
            st.session_state.visible_messages.extend([
                {"role": "user", "content": "Can you show me an example?"},
                {"role": "assistant", "content": example_response}
            ])
            st.rerun()
            
    #==========================================================================
    # SECTION: INPUT FORM AND RESPONSE HANDLING
    #==========================================================================
    # Input form
    with st.form(key='chat_form', clear_on_submit=True):
        user_input = st.text_input("Your response:", placeholder="Type your response or ask a question...")
        submit_button = st.form_submit_button("Send")

    if submit_button:
        # Check if input is empty or just whitespace
        if not user_input or user_input.isspace():
            st.error("Please enter a message before sending.")
            st.rerun()
        
        # Process non-empty input
        elif user_input.lower().strip() in ["example", "show example", "give me an example", "example answer"]:
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
            example_response = get_openai_response(example_messages)
            
            # Add to chat history
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            st.session_state.chat_history.append({"role": "assistant", "content": example_response})
            st.session_state.visible_messages.extend([
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": example_response}
            ])
            st.rerun()
        
        # Check if user is requesting a summary or indicating frustration with the process
        elif user_input.lower().strip() in ["summary", "download", "download summary", "get summary", "show summary", "yes", "provide summary"] or any(phrase in user_input.lower() for phrase in ["already answered", "not helpful", "i already responded"]):
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
                    missing_topics = [t for t, v in st.session_state.topic_areas_covered.items() if not v]
                    missing_topics_str = ", ".join(missing_topics)
                    missing_response = f"I see you'd like a summary, but we still have a few important areas to cover: {missing_topics_str}. Let's quickly address these topics so we can complete your questionnaire."
                    
                    st.session_state.chat_history.append({"role": "assistant", "content": missing_response})
                    st.session_state.visible_messages.append({"role": "assistant", "content": missing_response})
            
            st.rerun()
        
        else:
            # Add user input to chat history
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            st.session_state.visible_messages.append({"role": "user", "content": user_input})
            
            # Get AI response
            ai_response = get_openai_response(st.session_state.chat_history)
            
            # Log response for debugging
            print(f"AI Response: {ai_response}")
            
            # Check if this is a special message
            is_special = process_special_messages(ai_response)
            
            # Add an explicit topic update message after each user response
            if not is_special:
                # Add the response to visible messages
                st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
                st.session_state.visible_messages.append({"role": "assistant", "content": ai_response})
                
                # Force a topic update message after each regular response
                topic_check_messages = st.session_state.chat_history.copy()
                topic_check_messages.append({
                    "role": "system", 
                    "content": "Based on all conversation so far, which topics have been covered? Respond ONLY with a TOPIC_UPDATE message that includes the status of ALL topic areas."
                })
                
                topic_update_response = get_openai_response(topic_check_messages)
                process_special_messages(topic_update_response)
                
                # Check if we're at 7+ topics and force a check for missing topics
                covered_count = sum(st.session_state.topic_areas_covered.values())
                if covered_count >= 7:
                    missing_topics = [t for t, v in st.session_state.topic_areas_covered.items() if not v]
                    if missing_topics:
                        missing_topics_str = ", ".join(missing_topics)
                        focus_message = {
                            "role": "system", 
                            "content": f"IMPORTANT: Focus on gathering information about these remaining topics in your next questions: {missing_topics_str}"
                        }
                        st.session_state.chat_history.append(focus_message)

            # For the first question, extract user and company name
            if st.session_state.current_question_index == 0:
                # Extract name and company from response to first question
                extract_messages = [
                    {"role": "system", "content": "Extract the user name and company name from this response to the question 'Could you please provide your name and your company name?'. Even if the response is brief or partial, try to identify name and company information."},
                    {"role": "user", "content": f"User response: {user_input}\nExtract only the name and company. Format your response exactly as: NAME: [name], COMPANY: [company]. If you can only extract one of these, still provide it and use 'unknown' for the other."}
                ]
                extract_response = get_openai_response(extract_messages)
                
                try:
                    # Parse the extraction response
                    name_part = "unknown"
                    company_part = "unknown"
                    
                    if "NAME:" in extract_response:
                        name_part = extract_response.split("NAME:")[1].split(",")[0].strip()
                        name_part = name_part.replace("[", "").replace("]", "")
                        
                    if "COMPANY:" in extract_response:
                        company_part = extract_response.split("COMPANY:")[1].strip()
                        company_part = company_part.replace("[", "").replace("]", "")
                    
                    # Only update if we found something useful
                    if name_part != "unknown" or company_part != "unknown":
                        st.session_state.user_info = {
                            "name": name_part if name_part != "unknown" else "",
                            "company": company_part if company_part != "unknown" else ""
                        }
                        
                        # Add this information to the AI context to prevent redundant questions
                        context_message = {"role": "system", "content": f"The user's name is {name_part if name_part != 'unknown' else 'not provided yet'} and they work for {company_part if company_part != 'unknown' else 'a company that has not been mentioned yet'}. If you know the user's name, address them by it. Do not ask for name or company information again if it has been provided."}
                        st.session_state.chat_history.append(context_message)
                        
                        # If we only got partial info, immediately ask for the rest
                        if name_part == "unknown" or company_part == "unknown":
                            if name_part == "unknown" and company_part != "unknown":
                                follow_up = {"role": "system", "content": f"The user has mentioned their company ({company_part}) but not their name. In your next response, thank them for the company information and ask for their name."}
                                st.session_state.chat_history.append(follow_up)
                            elif name_part != "unknown" and company_part == "unknown":
                                follow_up = {"role": "system", "content": f"The user has mentioned their name ({name_part}) but not their company. In your next response, address them by name and ask for their company name."}
                                st.session_state.chat_history.append(follow_up)
                except Exception as e:
                    st.error(f"Could not extract user information: {e}")

# Check if this is an answer to the current question
            if st.session_state.current_question_index < len(st.session_state.questions):
                messages_for_check = [
                    {"role": "system", "content": "You are helping to determine if a user message is an answer to a question or a request for help/clarification."},
                    {"role": "user", "content": f"Question: {st.session_state.current_question}\nUser message: {user_input}\nIs this a direct answer to the question or a request for help/clarification? Reply with exactly 'ANSWER' or 'QUESTION'."}
                ]
                response_type = get_openai_response(messages_for_check)
                
                if "ANSWER" in response_type.upper():
                    # Special handling for "Yes" responses to summary questions
                    if "summary" in st.session_state.current_question.lower() and user_input.lower().strip() in ["yes", "yeah", "sure", "ok", "okay"]:
                        # Treat as a summary request
                        all_topics_covered = all(st.session_state.topic_areas_covered.values())
                        
                        if all_topics_covered:
                            st.session_state.summary_requested = True
                            # Force all topics to be marked as covered
                            for topic in st.session_state.topic_areas_covered:
                                st.session_state.topic_areas_covered[topic] = True
                            summary_confirm = "I'll prepare a summary of your responses. You can download it below."
                            st.session_state.chat_history.append({"role": "assistant", "content": summary_confirm})
                            st.session_state.visible_messages.append({"role": "assistant", "content": summary_confirm})
                            st.rerun()
                        else:
                            # If not all topics are covered, ask about missing topics
                            missing_topics = [t for t, v in st.session_state.topic_areas_covered.items() if not v]
                            missing_topics_str = ", ".join(missing_topics)
                            missing_response = f"I see you'd like a summary, but we still have a few important areas to cover: {missing_topics_str}. Let's quickly address these topics so we can complete your questionnaire."
                            st.session_state.chat_history.append({"role": "assistant", "content": missing_response})
                            st.session_state.visible_messages.append({"role": "assistant", "content": missing_response})
                            st.rerun()
                    
                    # Check if this answer also provides information for future questions
                    multi_answer_check = [
                        {"role": "system", "content": "Analyze if this user response answers multiple questions at once. Identify any additional topics covered beyond the current question."},
                        {"role": "user", "content": f"Current question: {st.session_state.current_question}\nUser response: {user_input}\nCheck if this response covers information about any of these additional topics: staffing_details, contact_process, list_management, insufficient_staffing, calling_logistics, list_changes, tiebreakers, additional_rules.\nRespond with a JSON object listing any additional topics covered, like {{'additional_topics': ['topic1', 'topic2']}}. If no additional topics, respond with {{'additional_topics': []}}"}
                    ]
                    
                    try:
                        multi_answer_response = get_openai_response(multi_answer_check)
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
                    except Exception as e:
                        # If we hit an error processing multi-answers, just continue normally
                        pass
                    
                    # Store answer and advance to next question
                    st.session_state.responses.append((st.session_state.current_question, user_input))
                    st.session_state.current_question_index += 1
                    if st.session_state.current_question_index < len(st.session_state.questions):
                        st.session_state.current_question = st.session_state.questions[st.session_state.current_question_index]
            
            st.rerun()

    #==========================================================================
    # SECTION: COMPLETION DISPLAY
    #==========================================================================
    # Completion section - display summary when requested
    if "summary_requested" in st.session_state and st.session_state.summary_requested:
        print("Displaying summary")
        
        # Add a more explicit completion message with button
        st.markdown(
            """
            <div style="text-align: center; padding: 20px; background-color: var(--light-red); border-radius: 10px; margin: 20px 0;">
                <h2 style="color: var(--primary-red); margin-bottom: 10px;">
                    ✨ Questionnaire completed! ✨
                </h2>
                <p style="font-size: 16px; color: #1b5e20;">
                    Thank you for completing the ACE Questionnaire. Your responses will help us better understand your requirements.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Add a clear finish button above the summary
        if not st.session_state.get("explicitly_finished", False):
            if st.button("✅ FINALIZE QUESTIONNAIRE", type="primary"):
                st.session_state.explicitly_finished = True
                # Send completion email if not already sent
                if not st.session_state.get("completion_email_sent", False):
                    if send_email(st.session_state.user_info, st.session_state.responses, True):
                        st.success("Completion notification sent!")
                        st.session_state.completion_email_sent = True
                st.rerun()
        
        # Only show summary after explicit finalization
        if st.session_state.get("explicitly_finished", False):
            # Generate the summary
            summary_text = generate_conversation_summary()
            
            # Display summary in a text area
            st.write("### Summary of Responses")
            st.text_area("Summary", summary_text, height=300)
            
            # Provide download options
            col1, col2 = st.columns(2)
            
            with col1:
                # Generate CSV for download
                csv_data = generate_csv(st.session_state.responses)
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv_data,
                    file_name="questionnaire_responses.csv",
                    mime="text/csv"
                )
            
            with col2:
                # Download formatted summary
                st.download_button(
                    label="📄 Download Summary",
                    data=summary_text,
                    file_name=f"ace_questionnaire_summary_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain"
                )
        else:
            # Generate the summary even before finalization but don't show it
            # This helps ensure the summary is calculated correctly
            summary_text = generate_conversation_summary()
            
            # Provide a brief instruction and the finalize button
            st.info("Please click the FINALIZE QUESTIONNAIRE button above to complete the process and view your summary.")
        
        # Send completion email if not already sent
        if not st.session_state.get("completion_email_sent", False) and st.session_state.get("explicitly_finished", False):
            if send_email(st.session_state.user_info, st.session_state.responses, True):
                st.success("Completion notification sent!")
                st.session_state.completion_email_sent = True
#==============================================================================
# APPLICATION ENTRY POINT
#==============================================================================
if __name__ == "__main__":
    main()