from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from io import BytesIO
from datetime import datetime
import os
import re
import tempfile
import logging
import platform

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pdf_export")

# Detect operating system
system = platform.system()
logger.info(f"Current operating system: {system}")

# Try to load Chinese font
try:
    # First try to register Source Han Sans (Adobe Source Han Sans)
    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
    chinese_font = 'STSong-Light'
    logger.info("Successfully loaded built-in Chinese font: STSong-Light")
except Exception as e:
    logger.warning(f"Unable to load built-in Chinese font STSong-Light: {e}")
    
    # Try using system Chinese font as fallback
    font_paths = []
    
    if system == 'Linux':
        font_paths = [
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/arphic/uming.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
        ]
    elif system == 'Darwin':  # macOS
        font_paths = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc"
        ]
    elif system == 'Windows':
        font_paths = [
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/simsun.ttc",
            "C:/Windows/Fonts/msyh.ttf"
        ]
    
    # Add fonts that might be distributed with the application
    font_paths.extend([
        os.path.join(os.path.dirname(__file__), "fonts/simhei.ttf"),
        os.path.join(os.path.dirname(__file__), "fonts/wqy-microhei.ttc"),
        "simhei.ttf",
        "wqy-microhei.ttc"
    ])
    
    font_loaded = False
    for font_path in font_paths:
        try:
            if os.path.exists(font_path):
                logger.info(f"Trying to load font: {font_path}")
                pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                chinese_font = 'ChineseFont'
                font_loaded = True
                logger.info(f"Successfully loaded Chinese font: {font_path}")
                break
        except Exception as e:
            logger.warning(f"Failed to load font {font_path}: {e}")
    
    # If no usable Chinese font is found, use default font
    if not font_loaded:
        chinese_font = 'Helvetica'
        logger.warning("No usable Chinese font found, will use Helvetica (may cause Chinese character garbling)")


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
    """Draw PDF directly using Canvas (suitable for Chinese)"""
    buffer = BytesIO()
    
    # Page setup
    page_width, page_height = A4
    margin = 72  # 1 inch margin
    text_width = page_width - 2 * margin  # Text area width
    
    # Create Canvas
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setTitle("Fact Check Report")
    
    # Set Chinese font
    c.setFont(chinese_font, 18)
    
    # Add title
    title = "Fact Check Report"
    title_width = c.stringWidth(title, chinese_font, 18)
    c.drawString((page_width - title_width) / 2, page_height - margin, title)
    
    # Add generation time
    c.setFont(chinese_font, 10)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.drawString(margin, page_height - margin - 30, f"Generated at: {current_time}")
    
    # Current Y position (decreasing from top to bottom)
    y_position = page_height - margin - 60
    
    # Text drawing function - improved auto-wrap algorithm
    def draw_text_block(title, content, start_y):
        # Draw subtitle
        c.setFont(chinese_font, 14)
        c.drawString(margin, start_y, title)
        start_y -= 20
        
        # Draw content
        c.setFont(chinese_font, 10)
        
        # Process text content
        content = clean_html(content)
        
        # Better Chinese text wrapping algorithm
        def wrap_chinese_text(text, line_width, font_name, font_size):
            """Text wrapping algorithm for mixed Chinese and English"""
            if not text:
                return []
                
            lines = []
            line = ""
            
            # First split by natural paragraphs
            paragraphs = text.split('\n')
            
            for paragraph in paragraphs:
                if not paragraph.strip():
                    lines.append("")
                    continue
                    
                # For Chinese, we process character by character
                # Chinese has no natural word separators, each character can be a line break point
                chars = list(paragraph)
                line = chars[0] if chars else ""
                
                for char in chars[1:]:
                    test_line = line + char
                    width = c.stringWidth(test_line, font_name, font_size)
                    
                    if width <= line_width:
                        line = test_line
                    else:
                        lines.append(line)
                        line = char
                
                if line:
                    lines.append(line)
            
            return lines
        
        # Use improved wrapping algorithm
        lines = wrap_chinese_text(content, text_width, chinese_font, 10)
        
        # Draw text lines
        for line in lines:
            if start_y < margin:  # If reaching bottom of page, add new page
                c.showPage()
                c.setFont(chinese_font, 10)
                start_y = page_height - margin
            
            c.drawString(margin, start_y, line)
            start_y -= 15
        
        return start_y - 15  # Return starting Y position for next section
    
    # Draw original text
    y_position = draw_text_block("Original Text", history_item['original_text'], y_position)
    
    # Draw core claim
    y_position = draw_text_block("Core Claim", history_item['claim'], y_position)
    
    # Get emoji and Chinese text corresponding to verdict
    verdict = history_item['verdict'].upper()
    if verdict == "TRUE":
        emoji = "✓"
        verdict_cn = "True"
    elif verdict == "FALSE":
        emoji = "✗"
        verdict_cn = "False"
    elif verdict == "PARTIALLY TRUE":
        emoji = "!"
        verdict_cn = "Partially True"
    else:
        emoji = "?"
        verdict_cn = "Unverifiable"
    
    # Draw conclusion
    c.setFont(chinese_font, 14)
    if y_position < margin:  # Check if new page is needed
        c.showPage()
        c.setFont(chinese_font, 14)
        y_position = page_height - margin
    
    # c.drawString(margin, y_position, f"Conclusion: {emoji} {verdict_cn}")
    # emoji cannot be rendered
    c.drawString(margin, y_position, f"Conclusion: {verdict_cn}")
    y_position -= 20
    
    # Draw reasoning process
    y_position = draw_text_block("Reasoning Process", history_item['reasoning'], y_position)
    
    # Draw evidence sources
    c.setFont(chinese_font, 14)
    if y_position < margin:  # Check if new page is needed
        c.showPage()
        c.setFont(chinese_font, 14)
        y_position = page_height - margin
    
    c.drawString(margin, y_position, "Evidence Sources")
    y_position -= 20
    
    # Draw each piece of evidence
    for j, chunk in enumerate(history_item['evidence']):
        c.setFont(chinese_font, 10)
        if y_position < margin:  # Check if new page is needed
            c.showPage()
            c.setFont(chinese_font, 10)
            y_position = page_height - margin
        
        c.drawString(margin, y_position, f"[{j+1}]:")
        y_position -= 15
        
        # Draw evidence text
        text_lines = clean_html(chunk['text']).split('\n')
        for line in text_lines:
            if y_position < margin:  # Check if new page is needed
                c.showPage()
                c.setFont(chinese_font, 10)
                y_position = page_height - margin
            
            c.drawString(margin, y_position, line)
            y_position -= 15
        
        # Draw source
        if y_position < margin:  # Check if new page is needed
            c.showPage()
            c.setFont(chinese_font, 10)
            y_position = page_height - margin
        
        c.drawString(margin, y_position, f"Source: {clean_html(chunk['source'])}")
        y_position -= 15
        
        # Draw relevance/similarity
        if 'similarity' in chunk and chunk['similarity'] is not None:
            if y_position < margin:  # Check if new page is needed
                c.showPage()
                c.setFont(chinese_font, 10)
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
    
    # Create Chinese title style
    title_style = ParagraphStyle(
        'ChineseTitle',
        parent=styles['Title'],
        fontName=chinese_font,
        fontSize=18,
        alignment=1,  # Center
        wordWrap='CJK'  # Key: use CJK word wrap mode
    )
    
    # Create Chinese body text style
    normal_style = ParagraphStyle(
        'ChineseNormal',
        parent=styles['Normal'],
        fontName=chinese_font,
        fontSize=10,
        leading=14,  # Line spacing
        wordWrap='CJK'  # Key: use CJK word wrap mode
    )
    
    # Create Chinese subtitle style
    heading_style = ParagraphStyle(
        'ChineseHeading',
        parent=styles['Heading2'],
        fontName=chinese_font,
        fontSize=14,
        wordWrap='CJK'  # Key: use CJK word wrap mode
    )
    
    # Get emoji and Chinese text corresponding to verdict
    verdict = history_item['verdict'].upper()
    if verdict == "TRUE":
        emoji = "✓"  # Use simple symbol in PDF
        verdict_cn = "True"
    elif verdict == "FALSE":
        emoji = "✗"
        verdict_cn = "False"
    elif verdict == "PARTIALLY TRUE":
        emoji = "!"
        verdict_cn = "Partially True"
    else:
        emoji = "?"
        verdict_cn = "Unverifiable"
    
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
    
    # Use safe text processing
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
    # content.append(Paragraph(f"Conclusion: {emoji} {verdict_cn}", heading_style))
    # emoji cannot be rendered
    content.append(Paragraph(f"Conclusion: {verdict_cn}", heading_style))
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
    
    # Set font to Helvetica (built-in font, supports ASCII)
    c.setFont("Helvetica", 16)
    c.drawString(72, A4[1]-108, "Fact Check Report")
    
    c.setFont("Helvetica", 12)
    c.drawString(72, A4[1]-140, "Generated on: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
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
    
    c.drawString(72, A4[1]-180, "Verdict: " + verdict_text)
    
    # Add note explaining PDF issue
    c.setFont("Helvetica", 10)
    c.drawString(72, 72, "Note: There was an issue generating the complete PDF with Chinese characters.")
    c.drawString(72, 58, "Please check the application interface for complete results.")
    
    c.save()
    
    # Reset buffer position
    buffer.seek(0)
    
    # Return PDF data
    return buffer.getvalue()