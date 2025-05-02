"""
ACME Questionnaire Bot - UI Components

Reusable UI components for the application.
"""
import streamlit as st
from services.summary_service import generate_conversation_summary

def display_chat_history():
    """Display the chat history in the UI."""
    if "visible_messages" not in st.session_state:
        return
        
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

def create_input_form():
    """Create the input form for user responses."""
    with st.form(key='chat_form', clear_on_submit=True):
        user_input = st.text_input("Your response:", placeholder="Type your response or ask a question...")
        submit_button = st.form_submit_button("Send")
    
    # Add help and example buttons
    if st.session_state.get("current_question_index", 0) < len(st.session_state.get("questions", [])):
        buttons_col1, buttons_col2 = st.columns(2)
        
        with buttons_col1:
            help_button = st.button("Need help?", key="help_button")
        
        with buttons_col2:
            example_button = st.button("Example", key="example_button")
            
        # Handle help button
        if help_button:
            handle_help_request()
            st.rerun()
            
        # Handle example button
        if example_button:
            handle_example_request()
            st.rerun()
    
    return user_input, submit_button

def handle_help_request():
    """Handle a help request from the user."""
    from services.ai_service import get_ai_response
    
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
    
    help_response = get_ai_response(help_messages)
    
    # Add help interaction to chat history without advancing question
    st.session_state.chat_history.append({"role": "user", "content": "I need help with this question"})
    st.session_state.chat_history.append({"role": "assistant", "content": help_response})
    st.session_state.visible_messages.extend([
        {"role": "user", "content": "I need help with this question"},
        {"role": "assistant", "content": help_response}
    ])

def handle_example_request():
    """Handle an example request from the user."""
    from services.ai_service import get_ai_response
    
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
    example_response = get_ai_response(example_messages)
    
    # Add to chat history
    st.session_state.chat_history.append({"role": "user", "content": "Can you show me an example?"})
    st.session_state.chat_history.append({"role": "assistant", "content": example_response})
    st.session_state.visible_messages.extend([
        {"role": "user", "content": "Can you show me an example?"},
        {"role": "assistant", "content": example_response}
    ])

def display_completion_summary():
    """Display the completion summary when the questionnaire is finished."""
    if not st.session_state.get("summary_requested", False):
        return
    
    # Add a completion message
    st.markdown(
        """
        <div style="text-align: center; padding: 20px; background-color: var(--light-red); border-radius: 10px; margin: 20px 0;">
            <h2 style="color: var(--primary-red); margin-bottom: 10px;">
                ✨ Questionnaire completed! ✨
            </h2>
            <p style="font-size: 16px; color: #1b5e20;">
                Thank you for completing the ACME Questionnaire. Your responses will help us better understand your requirements.
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
            from utils.email import send_email
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
        from utils.export import generate_csv, generate_excel
        
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
                file_name=f"acme_questionnaire_summary_{st.session_state.download_timestamp}.txt",
                mime="text/plain"
            )
    else:
        # Provide a brief instruction
        st.info("Please click the FINALIZE QUESTIONNAIRE button above to complete the process and view your summary.")