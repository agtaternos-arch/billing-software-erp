from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from io import BytesIO
from django.http import HttpResponse
from django.utils import timezone
from .models import Expense

def generate_expense_pdf(expenses):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=45, leftMargin=45, topMargin=40, bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=HexColor('#1e293b'),
        spaceAfter=20
    )
    
    story = []
    
    story.append(Paragraph("Expense History Report", title_style))
    story.append(Paragraph(f"Generated on: {timezone.now().strftime('%B %d, %Y')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Table header
    data = [["Date", "Title", "Category", "Amount (Rs)"]]
    
    total_expenses = 0
    for exp in expenses:
        data.append([
            exp.date.strftime('%d-%m-%Y'),
            str(exp.title)[:30],
            str(exp.get_category_display()),
            f"{exp.amount:,.2f}"
        ])
        total_expenses += float(exp.amount)
        
    # Append total row
    data.append(["", "", "TOTAL:", f"{total_expenses:,.2f}"])
    
    table = Table(data, colWidths=[1.5*inch, 2.5*inch, 1.5*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#475569')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (2, -1), (3, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), HexColor('#e2e8f0')),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cbd5e1')),
    ]))
    
    story.append(table)
    
    doc.build(story)
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="expenses_report.pdf"'
    return response
