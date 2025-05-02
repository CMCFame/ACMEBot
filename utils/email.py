"""
ACME Questionnaire Bot - Email Notification

Functions for sending email notifications.
"""
import smtplib
import streamlit as st
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
from utils.export import generate_csv, generate_excel
from config import SMTP_SERVER_DEFAULT, SMTP_PORT_DEFAULT

def send_email(user_info, answers, completed=False):
    """
    Send an email notification with questionnaire responses.
    
    Args:
        user_info (dict): Dictionary with user information
        answers (list): List of (question, answer) tuples
        completed (bool): Whether the questionnaire is completed
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Get email settings from secrets
        sender_email = st.secrets.get("EMAIL_SENDER", "")
        sender_password = st.secrets.get("EMAIL_PASSWORD", "")
        recipient_email = st.secrets.get("EMAIL_RECIPIENT", "")
        smtp_server = st.secrets.get("SMTP_SERVER", SMTP_SERVER_DEFAULT)
        smtp_port = st.secrets.get("SMTP_PORT", SMTP_PORT_DEFAULT)
        
        if not sender_email or not sender_password or not recipient_email:
            st.warning("Email configuration not complete. Notification email not sent.")
            return False
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        
        # Set subject based on whether questionnaire was completed
        status = "completed" if completed else "in progress"
        msg['Subject'] = f"ACME Questionnaire {status} - {user_info['name']} from {user_info['company']}"
        
        # Create email body
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
        <h2 style="color: #D22B2B;">ACME Questionnaire Submission</h2>
        <p><strong>Status:</strong> {"Completed" if completed else "In Progress"}</p>
        <p><strong>User:</strong> {user_info['name']}</p>
        <p><strong>Organization:</strong> {user_info['company']}</p>
        <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h3 style="margin-top: 20px;">Summary of Responses</h3>
        <table style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f2f2f2;">
                <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Question</th>
                <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Answer</th>
            </tr>
        """
        
        # Add up to 5 question-answer pairs in the email body
        for i, (question, answer) in enumerate(answers[:5]):
            body += f"""
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;">{question}</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{answer}</td>
            </tr>
            """
            
        # Add message if there are more responses
        if len(answers) > 5:
            body += f"""
            <tr>
                <td colspan="2" style="border: 1px solid #ddd; padding: 8px; text-align: center;">
                    <em>... {len(answers) - 5} more responses (see attached files) ...</em>
                </td>
            </tr>
            """
            
        body += """
        </table>
        <p style="margin-top: 20px;">Please check the attached files for complete responses.</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Create and attach CSV file (more reliable than Excel)
        csv_data = generate_csv(answers)
        attachment = MIMEApplication(csv_data)
        attachment.add_header('Content-Disposition', 'attachment', 
                             filename=f"ACME_Questionnaire_{user_info['company']}_{datetime.now().strftime('%Y%m%d')}.csv")
        msg.attach(attachment)
        
        # Try to also attach Excel file if available
        try:
            excel_data = generate_excel(answers)
            # Skip if we got CSV back instead (fallback when Excel libs aren't available)
            if not excel_data[:10].decode('utf-8', errors='ignore').startswith("Question,Answer"):
                excel_attachment = MIMEApplication(excel_data)
                excel_attachment.add_header('Content-Disposition', 'attachment', 
                                filename=f"ACME_Questionnaire_{user_info['company']}_{datetime.now().strftime('%Y%m%d')}.xlsx")
                msg.attach(excel_attachment)
        except Exception as e:
            print(f"Excel attachment failed: {e}")
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