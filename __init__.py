"""
ACME Questionnaire Bot - Root Module

Initialize the ACME Questionnaire Bot package.
"""
from ui.layout import apply_css, setup_tabs
from ui.components import display_chat_history, create_input_form, display_completion_summary
from utils.cookie_manager import init_cookie_manager, add_save_load_ui
from utils.session import initialize_session_state, process_user_input
from utils.export import generate_csv, generate_excel, generate_json, generate_pdf
from utils.file_loader import load_questions, load_instructions, create_directory_structure
from utils.special_messages import process_special_messages, detect_conversation_loop
from utils.extract import extract_user_info, multi_answer_detection
from utils.email import send_email
from services.ai_service import initialize_openai_client, get_ai_response
from services.summary_service import generate_conversation_summary

__version__ = "1.0.0"
__author__ = "ACME Solutions"
__description__ = "ACME Questionnaire Bot for Crew Manager implementation"