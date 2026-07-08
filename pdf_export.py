from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from io import BytesIO
from datetime import datetime
import os
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pdf_export")

# Font used throughout the report (built-in, no external font files needed)
PDF_FONT = "Helvetica"
PDF_FONT_BOLD = "Helvetica-Bold"


def clean_html(text):
    """Clean possible HTML tags and process content"""
    if text is None:
        return ""

    # Convert text to string
    text = str(text)

    # Clean HTML tags
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', text)

    # Remove invisible characters
    text = ''.join(c for c in text if ord(c) >= 32 or ord(c) == 9)

    # Handle line breaks and spaces
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    return text


def generate_fact_check_pdf(history_item):
    """Generate PDF for fact-check report

    Args:
        history_item: Dictionary containing fact-check history details

    Returns:
        BytesIO: BytesIO object containing PDF data
    """
    logger.info("Starting PDF report generation")

    try:
        # Try using direct canvas method as approach
        logger.info("Trying to generate PDF using direct canvas method")
        return generate_pdf_with_canvas(history_item)
    except Exception as e:
        logger.error(f"Failed to generate PDF using canvas method: {e}")
        logger.info("Trying to generate PDF using reportlab's SimpleDocTemplate method")
        try:
            return generate_pdf_with_template(history_item)
        except Exception as e:
            logger.error(f"Failed to generate PDF using SimpleDocTemplate method: {e}")
            # Generate the simplest possible PDF to ensure functionality works
            return generate_simple_pdf(history_item)


def generate_pdf_with_canvas(history_item):
    """Draw PDF directly using Canvas"""
    buffer = BytesIO()

    # Page setup
    page_width, page_height = A4
    margin = 72  # 1 inch margin
    text_width = page_width - 2 * margin  # Text area width

    # Create Canvas
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setTitle("Fact Check Report")

    # Add title
    c.setFont(PDF_FONT_BOLD, 18)
    title = "Fact Check Report"
    title_width = c.stringWidth(title, PDF_FONT_BOLD, 18)
    c.drawString((page_width - title_width) / 2, page_height - margin, title)

    # Add generation time
    c.setFont(PDF_FONT, 10)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.drawString(margin, page_height - margin - 30, f"Generated at: {current_time}")

    # Current Y position (decreasing from top to bottom)
    y_position = page_height - margin - 60

    def wrap_text(text, line_width, font_name, font_size):
        """Word-based text wrapping"""
        if not text:
            return []

        lines = []

        # First split by natural paragraphs
        paragraphs = text.split('\n')

        for paragraph in paragraphs:
            if not paragraph.strip():
                lines.append("")
                continue

            words = paragraph.split(' ')
            line = ""

            for word in words:
                test_line = f"{line} {word}".strip()
                width = c.stringWidth(test_line, font_name, font_size)

                if width <= line_width:
                    line = test_line
                else:
                    if line:
                        lines.append(line)
                    line = word

            if line:
                lines.append(line)

        return lines

    # Text drawing function
    def draw_text_block(title, content, start_y):
        # Draw subtitle
        c.setFont(PDF_FONT_BOLD, 14)
        c.drawString(margin, start_y, title)
        start_y -= 20

        # Process text content
        content = clean_html(content)

        # Use wrapping algorithm
        c.setFont(PDF_FONT, 10)
        lines = wrap_text(content, text_width, PDF_FONT, 10)

        # Draw text lines
        for line in lines:
            if start_y < margin:  # If reaching bottom of page, add new page
                c.showPage()
                c.setFont(PDF_FONT, 10)
                start_y = page_height - margin

            c.drawString(margin, start_y, line)
            start_y -= 15

        return start_y - 15  # Return starting Y position for next section

    # Draw original text
    y_position = draw_text_block("Original Text", history_item['original_text'], y_position)

    # Draw core claim
    y_position = draw_text_block("Core Claim", history_item['claim'], y_position)

    # Get verdict label
    verdict = history_item['verdict'].upper()
    if verdict == "TRUE":
        verdict_label = "True"
    elif verdict == "FALSE":
        verdict_label = "False"
    elif verdict == "PARTIALLY TRUE":
        verdict_label = "Partially True"
    else:
        verdict_label = "Unverifiable"

    # Draw conclusion
    c.setFont(PDF_FONT_BOLD, 14)
    if y_position < margin:  # Check if new page is needed
        c.showPage()
        c.setFont(PDF_FONT_BOLD, 14)
        y_position = page_height - margin

    c.drawString(margin, y_position, f"Conclusion: {verdict_label}")
    y_position -= 20

    # Draw reasoning process
    y_position = draw_text_block("Reasoning Process", history_item['reasoning'], y_position)

    # Draw evidence sources
    c.setFont(PDF_FONT_BOLD, 14)
    if y_position < margin:  # Check if new page is needed
        c.showPage()
        c.setFont(PDF_FONT_BOLD, 14)
        y_position = page_height - margin

    c.drawString(margin, y_position, "Evidence Sources")
    y_position -= 20

    # Draw each piece of evidence
    for j, chunk in enumerate(history_item['evidence']):
        c.setFont(PDF_FONT, 10)
        if y_position < margin:  # Check if new page is needed
            c.showPage()
            c.setFont(PDF_FONT, 10)
            y_position = page_height - margin

        c.drawString(margin, y_position, f"[{j+1}]:")
        y_position -= 15

        # Draw evidence text
        evidence_lines = wrap_text(clean_html(chunk['text']), text_width, PDF_FONT, 10)
        for line in evidence_lines:
            if y_position < margin:  # Check if new page is needed
                c.showPage()
                c.setFont(PDF_FONT, 10)
                y_position = page_height - margin

            c.drawString(margin, y_position, line)
            y_position -= 15

        # Draw source
        if y_position < margin:  # Check if new page is needed
            c.showPage()
            c.setFont(PDF_FONT, 10)
            y_position = page_height - margin

        c.drawString(margin, y_position, f"Source: {clean_html(chunk['source'])}")
        y_position -= 15

        # Draw relevance/similarity
        if 'similarity' in chunk and chunk['similarity'] is not None:
            if y_position < margin:  # Check if new page is needed
                c.showPage()
                c.setFont(PDF_FONT, 10)
                y_position = page_height - margin

            c.drawString(margin, y_position, f"Relevance: {chunk['similarity']:.2f}")
            y_position -= 15

        y_position -= 10  # Extra spacing between evidence items

    # Save PDF
    c.save()

    # Reset buffer position
    buffer.seek(0)

    # Return PDF data
    return buffer.getvalue()


def generate_pdf_with_template(history_item):
    """Generate PDF using SimpleDocTemplate (traditional method)"""
    buffer = BytesIO()

    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )

    # Define styles
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Title'],
        fontName=PDF_FONT_BOLD,
        fontSize=18,
        alignment=1,  # Center
    )

    normal_style = ParagraphStyle(
        'ReportNormal',
        parent=styles['Normal'],
        fontName=PDF_FONT,
        fontSize=10,
        leading=14,  # Line spacing
    )

    heading_style = ParagraphStyle(
        'ReportHeading',
        parent=styles['Heading2'],
        fontName=PDF_FONT_BOLD,
        fontSize=14,
    )

    # Get verdict label
    verdict = history_item['verdict'].upper()
    if verdict == "TRUE":
        verdict_label = "True"
    elif verdict == "FALSE":
        verdict_label = "False"
    elif verdict == "PARTIALLY TRUE":
        verdict_label = "Partially True"
    else:
        verdict_label = "Unverifiable"

    # Report content list
    content = []

    # Add title
    content.append(Paragraph("Fact Check Report", title_style))
    content.append(Spacer(1, 12))

    # Add generation time
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content.append(Paragraph(f"Generated at: {current_time}", normal_style))
    content.append(Spacer(1, 12))

    # Add original text
    content.append(Paragraph("Original Text", heading_style))
    content.append(Spacer(1, 6))

    try:
        original_text = clean_html(history_item['original_text'])
        content.append(Paragraph(original_text, normal_style))
    except Exception as e:
        logger.error(f"Error processing original text: {e}")
        content.append(Paragraph("Unable to display original text", normal_style))

    content.append(Spacer(1, 12))

    # Add core claim
    content.append(Paragraph("Core Claim", heading_style))
    content.append(Spacer(1, 6))
    try:
        claim_text = clean_html(history_item['claim'])
        content.append(Paragraph(claim_text, normal_style))
    except Exception as e:
        logger.error(f"Error processing core claim: {e}")
        content.append(Paragraph("Unable to display core claim", normal_style))

    content.append(Spacer(1, 12))

    # Add verdict
    content.append(Paragraph(f"Conclusion: {verdict_label}", heading_style))
    content.append(Spacer(1, 12))

    # Add reasoning process
    content.append(Paragraph("Reasoning Process", heading_style))
    content.append(Spacer(1, 6))
    try:
        reasoning_text = clean_html(history_item['reasoning'])
        content.append(Paragraph(reasoning_text, normal_style))
    except Exception as e:
        logger.error(f"Error processing reasoning process: {e}")
        content.append(Paragraph("Unable to display reasoning process", normal_style))

    content.append(Spacer(1, 12))

    # Add evidence sources
    content.append(Paragraph("Evidence Sources", heading_style))
    content.append(Spacer(1, 6))

    for j, chunk in enumerate(history_item['evidence']):
        try:
            content.append(Paragraph(f"[{j+1}]:", normal_style))
            chunk_text = clean_html(chunk['text'])
            content.append(Paragraph(chunk_text, normal_style))
            source_text = clean_html(chunk['source'])
            content.append(Paragraph(f"Source: {source_text}", normal_style))
            if 'similarity' in chunk and chunk['similarity'] is not None:
                content.append(Paragraph(f"Relevance: {chunk['similarity']:.2f}", normal_style))
            content.append(Spacer(1, 6))
        except Exception as e:
            logger.error(f"Error processing evidence {j+1}: {e}")
            content.append(Paragraph(f"Unable to display evidence {j+1}", normal_style))
            content.append(Spacer(1, 6))

    # Build PDF
    doc.build(content)

    # Reset buffer position
    buffer.seek(0)

    # Return PDF data
    return buffer.getvalue()


def generate_simple_pdf(history_item):
    """Generate a simple PDF to ensure at least some content is downloadable"""
    logger.info("Generating simple PDF as final fallback")
    buffer = BytesIO()

    # Create Canvas
    c = canvas.Canvas(buffer, pagesize=A4)

    c.setFont(PDF_FONT_BOLD, 16)
    c.drawString(72, A4[1] - 108, "Fact Check Report")

    c.setFont(PDF_FONT, 12)
    c.drawString(72, A4[1] - 140, "Generated on: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # Get verdict
    verdict = history_item['verdict'].upper()
    if verdict == "TRUE":
        verdict_text = "TRUE"
    elif verdict == "FALSE":
        verdict_text = "FALSE"
    elif verdict == "PARTIALLY TRUE":
        verdict_text = "PARTIALLY TRUE"
    else:
        verdict_text = "UNVERIFIABLE"

    c.drawString(72, A4[1] - 180, "Verdict: " + verdict_text)

    # Add note explaining PDF issue
    c.setFont(PDF_FONT, 10)
    c.drawString(72, 72, "Note: There was an issue generating the complete PDF report.")
    c.drawString(72, 58, "Please check the application interface for complete results.")

    c.save()

    # Reset buffer position
    buffer.seek(0)

    # Return PDF data
    return buffer.getvalue()
