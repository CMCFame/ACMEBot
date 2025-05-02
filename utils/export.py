"""
ACME Questionnaire Bot - Export Utilities

Functions for exporting questionnaire data to different formats.
"""
import pandas as pd
from io import BytesIO

def generate_csv(answers):
    """
    Generate a CSV file from question-answer pairs.
    
    Args:
        answers (list): List of (question, answer) tuples
        
    Returns:
        bytes: CSV file content as bytes
    """
    df = pd.DataFrame(answers, columns=['Question', 'Answer'])
    return df.to_csv(index=False).encode('utf-8')

def generate_excel(answers):
    """
    Generate an Excel file from question-answer pairs.
    
    Args:
        answers (list): List of (question, answer) tuples
        
    Returns:
        bytes: Excel file content as bytes
    """
    try:
        df = pd.DataFrame(answers, columns=['Question', 'Answer'])
        output = BytesIO()
        
        # Try to use xlsxwriter if available
        try:
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Responses')
                
                # Format the worksheet
                workbook = writer.book
                worksheet = writer.sheets['Responses']
                
                # Add formats
                header_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#D22B2B',
                    'color': 'white',
                    'border': 1,
                    'text_wrap': True,
                    'align': 'center',
                    'valign': 'vcenter'
                })
                
                # Apply formats
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Set column widths
                worksheet.set_column('A:A', 40)  # Question column
                worksheet.set_column('B:B', 60)  # Answer column
                
        except (ImportError, ModuleNotFoundError):
            # Fall back to openpyxl if xlsxwriter isn't available
            try:
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Responses')
                    
                    # Basic formatting for openpyxl
                    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
                    
                    # Get the worksheet
                    worksheet = writer.sheets['Responses']
                    
                    # Format header row
                    for cell in worksheet[1]:
                        cell.font = Font(bold=True, color="FFFFFF")
                        cell.fill = PatternFill(start_color="D22B2B", end_color="D22B2B", fill_type="solid")
                        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                        
                    # Set column widths
                    worksheet.column_dimensions['A'].width = 40
                    worksheet.column_dimensions['B'].width = 60
                    
            except (ImportError, ModuleNotFoundError):
                # If neither Excel writer is available, raise a more helpful error
                print("Excel export libraries (xlsxwriter or openpyxl) not available")
                return generate_csv(answers)  # Fallback to CSV
                
        return output.getvalue()
    except Exception as e:
        print(f"Could not generate Excel file: {e}")
        # Return CSV as fallback
        return generate_csv(answers)

def generate_json(answers, user_info):
    """
    Generate a JSON file from question-answer pairs and user info.
    
    Args:
        answers (list): List of (question, answer) tuples
        user_info (dict): Dictionary with user information
        
    Returns:
        bytes: JSON file content as bytes
    """
    import json
    from datetime import datetime
    
    # Create a structured data object
    data = {
        "user_info": user_info,
        "submission_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "responses": []
    }
    
    # Add each question-answer pair
    for question, answer in answers:
        data["responses"].append({
            "question": question,
            "answer": answer
        })
    
    # Convert to JSON string and encode as bytes
    return json.dumps(data, indent=2).encode('utf-8')

def generate_pdf(answers, user_info):
    """
    Generate a PDF file from question-answer pairs and user info.
    
    Args:
        answers (list): List of (question, answer) tuples
        user_info (dict): Dictionary with user information
        
    Returns:
        bytes: PDF file content as bytes or None if PDF generation fails
    """
    try:
        # Try to import ReportLab for PDF generation
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from io import BytesIO
        from datetime import datetime
        
        # Create a file-like buffer to receive PDF data
        buffer = BytesIO()
        
        # Create the PDF object using the buffer
        doc = SimpleDocTemplate(buffer, pagesize=letter, 
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=18)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        title_style.alignment = 1  # Center alignment
        
        # Custom styles
        section_style = ParagraphStyle(
            'SectionStyle',
            parent=styles['Heading2'],
            textColor=colors.HexColor('#D22B2B'),
            spaceAfter=12
        )
        
        question_style = ParagraphStyle(
            'QuestionStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            spaceAfter=6
        )
        
        answer_style = ParagraphStyle(
            'AnswerStyle',
            parent=styles['Normal'],
            fontSize=10,
            leftIndent=20,
            spaceAfter=12
        )
        
        # Add the title
        elements.append(Paragraph("ACME Questionnaire Responses", title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Add date
        date_text = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        elements.append(Paragraph(date_text, styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Add user information
        if user_info.get('name') or user_info.get('company'):
            elements.append(Paragraph("User Information", section_style))
            
            if user_info.get('name'):
                elements.append(Paragraph(f"Name: {user_info['name']}", styles['Normal']))
                
            if user_info.get('company'):
                elements.append(Paragraph(f"Organization: {user_info['company']}", styles['Normal']))
                
            elements.append(Spacer(1, 0.3*inch))
        
        # Group answers by section
        from collections import defaultdict
        section_answers = defaultdict(list)
        
        # Simple section detection based on keywords
        section_keywords = {
            "Section 1: Crew Manager Usage": ["crew manager", "daily crew", "resource", "work assignment", "situations"],
            "Section 2: Emergency and Contract Operations": ["mutual", "assistance", "contract", "lodging", "emergency"],
            "Section 3: Resources and Reporting": ["additional crew", "tracking", "availability", "roles", "using crew manager"],
            "Section 4: Current Practices and Needs": ["current tools", "reports", "data", "organized", "filtered"]
        }
        
        for question, answer in answers:
            # Determine which section this belongs to
            assigned_section = "Other"
            
            # Check each section's keywords
            for section, keywords in section_keywords.items():
                if any(keyword.lower() in question.lower() for keyword in keywords):
                    assigned_section = section
                    break
                    
            section_answers[assigned_section].append((question, answer))
        
        # Add responses by section
        for section in ["Section 1: Crew Manager Usage", "Section 2: Emergency and Contract Operations", 
                        "Section 3: Resources and Reporting", "Section 4: Current Practices and Needs", "Other"]:
            if section in section_answers and section_answers[section]:
                elements.append(Paragraph(section, section_style))
                
                for question, answer in section_answers[section]:
                    elements.append(Paragraph(f"Q: {question}", question_style))
                    elements.append(Paragraph(f"A: {answer}", answer_style))
                
                elements.append(Spacer(1, 0.2*inch))
        
        # Build the PDF
        doc.build(elements)
        
        # Get the value of the BytesIO buffer
        pdf = buffer.getvalue()
        buffer.close()
        
        return pdf
        
    except ImportError:
        print("ReportLab not available. PDF export requires the ReportLab library.")
        return None
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return None