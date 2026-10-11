import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Preformatted, KeepTogether, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        # Header rule and text
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(40, 755, 572, 755)
        self.drawString(40, 760, "EXOPLANET HABITABILITY CATALOG // DBMS PROJECT DEFENSE GUIDE")
        
        # Footer rule and text
        self.line(40, 42, 572, 42)
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(572, 30, page_text)
        self.drawString(40, 30, "CONFIDENTIAL & PROPRIETARY // CAPSTONE PRESENTATION DEFENSE")
        self.restoreState()

def clean_inline_md(text):
    # Convert **bold** to <b>bold</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Convert *italic* to <i>italic</i>
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    # Convert `code` to monospace font
    text = re.sub(r'`(.*?)`', r'<font name="Courier" color="#0369a1">\1</font>', text)
    # Remove markdown links [text](url) -> <u>text</u>
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'<u>\1</u>', text)
    # Fix XML entities
    text = text.replace('&', '&amp;') if '&amp;' not in text else text
    text = text.replace('&Delta;', 'Delta')
    return text

def parse_markdown_to_pdf(md_file_path, pdf_output_path):
    print(f"Reading markdown from: {md_file_path}...")
    with open(md_file_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    doc = SimpleDocTemplate(
        pdf_output_path,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=55,
        bottomMargin=55
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    style_h1 = ParagraphStyle(
        'CustomH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=14,
        spaceAfter=6
    )

    style_h2 = ParagraphStyle(
        'CustomH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#0284c7'),
        spaceBefore=12,
        spaceAfter=5
    )

    style_h3 = ParagraphStyle(
        'CustomH3',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#7c3aed'),
        spaceBefore=8,
        spaceAfter=4
    )

    style_body = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=3,
        spaceAfter=4
    )

    style_bullet = ParagraphStyle(
        'CustomBullet',
        parent=style_body,
        leftIndent=15,
        firstLineIndent=-10,
        spaceBefore=2,
        spaceAfter=2
    )

    style_code = ParagraphStyle(
        'CustomCode',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor('#0f172a'),
        backColor=colors.HexColor('#f8fafc'),
        borderColor=colors.HexColor('#cbd5e1'),
        borderWidth=0.5,
        borderPadding=6,
        spaceBefore=5,
        spaceAfter=6
    )

    style_callout = ParagraphStyle(
        'CustomCallout',
        parent=style_body,
        fontName='Helvetica-Oblique',
        textColor=colors.HexColor('#0369a1'),
        backColor=colors.HexColor('#f0f9ff'),
        borderColor=colors.HexColor('#38bdf8'),
        borderWidth=1,
        borderPadding=6,
        spaceBefore=6,
        spaceAfter=6
    )

    elements = []
    lines = md_text.splitlines()

    in_code_block = False
    code_lines = []
    table_lines = []
    in_table = False

    def flush_table():
        nonlocal table_lines, in_table
        if not table_lines:
            return
        
        # Parse table lines
        parsed_rows = []
        for tl in table_lines:
            if re.match(r'^\s*\|?\s*[-:]+[-| :]*$', tl):
                continue # Skip separator line
            cols = [c.strip() for c in tl.split('|')]
            if cols and cols[0] == '': cols.pop(0)
            if cols and cols[-1] == '': cols.pop()
            if cols:
                parsed_rows.append(cols)
        
        if parsed_rows:
            # Wrap cells in Paragraph
            col_count = max(len(r) for r in parsed_rows)
            flowable_rows = []
            for r_idx, row in enumerate(parsed_rows):
                f_row = []
                # Pad row
                while len(row) < col_count:
                    row.append("")
                for c_idx, cell in enumerate(row):
                    cell_clean = clean_inline_md(cell)
                    cell_style = ParagraphStyle(
                        'TableCell',
                        parent=style_body,
                        fontSize=8.5,
                        leading=11,
                        textColor=colors.white if r_idx == 0 else colors.HexColor('#1e293b'),
                        fontName='Helvetica-Bold' if r_idx == 0 else 'Helvetica'
                    )
                    f_row.append(Paragraph(cell_clean, cell_style))
                flowable_rows.append(f_row)

            # Available width = 572 - 40 = 532
            avail_w = 532
            col_w = avail_w / col_count

            tbl = Table(flowable_rows, colWidths=[col_w] * col_count)
            tbl.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#f8fafc')]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ]))
            elements.append(Spacer(1, 4))
            elements.append(tbl)
            elements.append(Spacer(1, 6))

        table_lines = []
        in_table = False

    for line in lines:
        stripped = line.strip()

        # Handle Code Blocks
        if stripped.startswith('```'):
            if in_code_block:
                in_code_block = False
                raw_code = '\n'.join(code_lines)
                # Escape code for XML pre
                raw_code_esc = raw_code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                elements.append(Paragraph(f"<font size=7.5>{raw_code_esc.replace('\n', '<br/>')}</font>", style_code))
                elements.append(Spacer(1, 4))
                code_lines = []
            else:
                if in_table: flush_table()
                in_code_block = True
                code_lines = []
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        # Handle Tables
        if '|' in stripped and not stripped.startswith('#'):
            in_table = True
            table_lines.append(stripped)
            continue
        elif in_table:
            flush_table()

        if not stripped:
            continue

        # Handle Headings
        if stripped.startswith('# '):
            h_text = clean_inline_md(stripped[2:])
            elements.append(Paragraph(h_text, style_h1))
            elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284c7'), spaceBefore=2, spaceAfter=8))
        elif stripped.startswith('## '):
            h_text = clean_inline_md(stripped[3:])
            elements.append(Paragraph(h_text, style_h2))
            elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e1'), spaceBefore=1, spaceAfter=5))
        elif stripped.startswith('### '):
            h_text = clean_inline_md(stripped[4:])
            elements.append(Paragraph(h_text, style_h3))
        elif stripped.startswith('#### '):
            h_text = clean_inline_md(stripped[5:])
            elements.append(Paragraph(f"<b>{h_text}</b>", style_h3))
        elif stripped.startswith('> '):
            call_text = clean_inline_md(stripped[2:])
            elements.append(Paragraph(call_text, style_callout))
        elif stripped.startswith('* ') or stripped.startswith('- '):
            bullet_text = clean_inline_md(stripped[2:])
            elements.append(Paragraph(f"&bull;&nbsp;&nbsp;{bullet_text}", style_bullet))
        elif re.match(r'^\d+\.\s', stripped):
            num_match = re.match(r'^(\d+\.)\s*(.*)', stripped)
            prefix = num_match.group(1)
            content = clean_inline_md(num_match.group(2))
            elements.append(Paragraph(f"<b>{prefix}</b>&nbsp;{content}", style_bullet))
        elif stripped == '---':
            elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0'), spaceBefore=4, spaceAfter=6))
        else:
            p_text = clean_inline_md(stripped)
            elements.append(Paragraph(p_text, style_body))

    if in_table:
        flush_table()

    print(f"Building PDF document: {pdf_output_path}...")
    doc.build(elements, canvasmaker=NumberedCanvas)
    print("PDF build successful!")

if __name__ == '__main__':
    base_dir = os.path.dirname(__file__)
    md_path = os.path.join(base_dir, 'FINAL_PRESENTATION_GUIDE.md')
    pdf_path = os.path.join(base_dir, 'Exoplanet_Habitability_Presentation_Guide.pdf')
    parse_markdown_to_pdf(md_path, pdf_path)
