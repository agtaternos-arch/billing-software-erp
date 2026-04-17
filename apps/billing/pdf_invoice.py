"""
Professional invoice PDF generation with clean, modern layout.
Redesigned to prevent text overlap and ensure print-quality output.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from io import BytesIO
from django.http import HttpResponse


class ProfessionalInvoicePDF:
    """Generate clean, professional invoice PDFs."""

    # Color palette
    ACCENT = HexColor('#4a7c59')       # Olive green for INVOICE title
    DARK = HexColor('#1e293b')         # Dark slate for headings
    MEDIUM = HexColor('#475569')       # Medium gray for labels
    LIGHT_BG = HexColor('#f8faf8')     # Very light green tint for header row
    BORDER = HexColor('#d1d5db')       # Light gray border
    TEXT = HexColor('#334155')         # Body text

    def __init__(self, invoice):
        self.invoice = invoice
        self.buffer = BytesIO()
        self.width, self.height = A4
        self.styles = self._create_styles()

    def _create_styles(self):
        """Create all text styles used in the invoice."""
        return {
            'invoice_title': ParagraphStyle(
                'InvoiceTitle',
                fontName='Helvetica-Bold',
                fontSize=32,
                textColor=self.ACCENT,
                leading=38,
            ),
            'biz_name': ParagraphStyle(
                'BizName',
                fontName='Helvetica-Bold',
                fontSize=11,
                textColor=self.DARK,
                leading=15,
            ),
            'biz_info': ParagraphStyle(
                'BizInfo',
                fontName='Helvetica',
                fontSize=9,
                textColor=self.MEDIUM,
                leading=13,
            ),
            'section_label': ParagraphStyle(
                'SectionLabel',
                fontName='Helvetica-Bold',
                fontSize=10,
                textColor=self.DARK,
                leading=14,
            ),
            'customer_name': ParagraphStyle(
                'CustomerName',
                fontName='Helvetica-Bold',
                fontSize=12,
                textColor=self.DARK,
                leading=16,
            ),
            'customer_info': ParagraphStyle(
                'CustomerInfo',
                fontName='Helvetica',
                fontSize=9,
                textColor=self.MEDIUM,
                leading=13,
            ),
            'field_label': ParagraphStyle(
                'FieldLabel',
                fontName='Helvetica-Bold',
                fontSize=9,
                textColor=self.ACCENT,
                alignment=TA_RIGHT,
                leading=13,
            ),
            'field_value': ParagraphStyle(
                'FieldValue',
                fontName='Helvetica',
                fontSize=9,
                textColor=self.DARK,
                alignment=TA_RIGHT,
                leading=13,
            ),
            'table_header': ParagraphStyle(
                'TableHeader',
                fontName='Helvetica-Bold',
                fontSize=9,
                textColor=self.MEDIUM,
                leading=13,
            ),
            'table_cell': ParagraphStyle(
                'TableCell',
                fontName='Helvetica',
                fontSize=9,
                textColor=self.TEXT,
                leading=13,
            ),
            'table_cell_right': ParagraphStyle(
                'TableCellRight',
                fontName='Helvetica',
                fontSize=9,
                textColor=self.TEXT,
                alignment=TA_RIGHT,
                leading=13,
            ),
            'table_cell_center': ParagraphStyle(
                'TableCellCenter',
                fontName='Helvetica',
                fontSize=9,
                textColor=self.TEXT,
                alignment=TA_CENTER,
                leading=13,
            ),
            'total_label': ParagraphStyle(
                'TotalLabel',
                fontName='Helvetica',
                fontSize=10,
                textColor=self.MEDIUM,
                alignment=TA_RIGHT,
                leading=14,
            ),
            'total_value': ParagraphStyle(
                'TotalValue',
                fontName='Helvetica-Bold',
                fontSize=10,
                textColor=self.DARK,
                alignment=TA_RIGHT,
                leading=14,
            ),
            'grand_total_label': ParagraphStyle(
                'GrandTotalLabel',
                fontName='Helvetica-Bold',
                fontSize=13,
                textColor=self.DARK,
                alignment=TA_RIGHT,
                leading=18,
            ),
            'grand_total_value': ParagraphStyle(
                'GrandTotalValue',
                fontName='Helvetica-Bold',
                fontSize=13,
                textColor=self.ACCENT,
                alignment=TA_RIGHT,
                leading=18,
            ),
            'footer': ParagraphStyle(
                'Footer',
                fontName='Helvetica-Bold',
                fontSize=9,
                textColor=self.ACCENT,
                leading=13,
            ),
            'footer_text': ParagraphStyle(
                'FooterText',
                fontName='Helvetica',
                fontSize=8,
                textColor=self.MEDIUM,
                leading=11,
            ),
            'thank_you': ParagraphStyle(
                'ThankYou',
                fontName='Helvetica-Bold',
                fontSize=12,
                textColor=self.DARK,
                alignment=TA_CENTER,
                leading=16,
            ),
        }

    def generate(self):
        """Build the complete invoice PDF."""
        try:
            doc = SimpleDocTemplate(
                self.buffer,
                pagesize=A4,
                rightMargin=45,
                leftMargin=45,
                topMargin=40,
                bottomMargin=40,
            )

            story = []
            story.append(self._build_header())
            story.append(Spacer(1, 25))
            story.append(self._build_bill_to_section())
            story.append(Spacer(1, 20))
            story.append(self._build_items_table())
            story.append(Spacer(1, 5))
            story.append(self._build_totals_section())
            story.append(Spacer(1, 30))
            story.append(self._build_payment_info())
            story.append(Spacer(1, 25))
            story.append(HRFlowable(
                width="100%", thickness=0.5,
                color=self.BORDER, spaceAfter=15
            ))
            story.append(self._build_footer())

            doc.build(story)
            self.buffer.seek(0)
            return self.buffer

        except Exception as e:
            from reportlab.lib.styles import getSampleStyleSheet
            self.buffer = BytesIO()
            doc = SimpleDocTemplate(self.buffer, pagesize=A4)
            story = [Paragraph(
                f"PDF Generation Error: {str(e)}",
                getSampleStyleSheet()['Normal']
            )]
            doc.build(story)
            self.buffer.seek(0)
            return self.buffer

    def _build_header(self):
        """INVOICE title on left, business info on right."""
        inv = self.invoice

        left_col = [
            Paragraph(inv.payment_method_label, self.styles['invoice_title']),
        ]

        right_col = [
            Paragraph("TORVIX SUPERMARKET", self.styles['biz_name']),
            Paragraph("Wayanad, Kerala", self.styles['biz_info']),
            Paragraph("Ph: 9876543210", self.styles['biz_info']),
        ]

        data = [[left_col, right_col]]
        table = Table(data, colWidths=[3.5 * inch, 3.5 * inch])
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        return table

    def _build_bill_to_section(self):
        """Customer details on left, invoice meta on right."""
        inv = self.invoice
        customer = inv.customer

        # Left: Bill To
        left_parts = []
        left_parts.append(Paragraph("BILL TO :", self.styles['section_label']))
        left_parts.append(Paragraph(
            getattr(customer, 'name', 'Walk-in Customer'),
            self.styles['customer_name']
        ))

        addr_parts = []
        if hasattr(customer, 'address_line_1') and customer.address_line_1:
            addr_parts.append(str(customer.address_line_1))
        if hasattr(customer, 'city') and customer.city:
            city_state = str(customer.city)
            if hasattr(customer, 'state') and customer.state:
                city_state += f", {customer.state}"
            if hasattr(customer, 'postal_code') and customer.postal_code:
                city_state += f" {customer.postal_code}"
            addr_parts.append(city_state)
        if hasattr(customer, 'phone') and customer.phone:
            addr_parts.append(f"Ph: {customer.phone}")
        if hasattr(customer, 'email') and customer.email:
            addr_parts.append(str(customer.email))

        if addr_parts:
            left_parts.append(Paragraph(
                "<br/>".join(addr_parts),
                self.styles['customer_info']
            ))

        # Right: Invoice details
        right_data = [
            [Paragraph("Invoice Date", self.styles['field_label']),
             Paragraph(inv.invoice_date.strftime('%d %b %Y'), self.styles['field_value'])],
            [Paragraph("Invoice No", self.styles['field_label']),
             Paragraph(str(inv.invoice_number), self.styles['field_value'])],
        ]
        if inv.due_date:
            right_data.append([
                Paragraph("Due Date", self.styles['field_label']),
                Paragraph(inv.due_date.strftime('%d %b %Y'), self.styles['field_value']),
            ])
        if inv.terms:
            right_data.append([
                Paragraph("Terms", self.styles['field_label']),
                Paragraph(str(inv.terms), self.styles['field_value']),
            ])

        right_table = Table(right_data, colWidths=[1.2 * inch, 1.5 * inch])
        right_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))

        # Combine
        data = [[left_parts, right_table]]
        main_table = Table(data, colWidths=[4 * inch, 3 * inch])
        main_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        return main_table

    def _build_items_table(self):
        """Clean product table with proper alignment."""
        s = self.styles

        # Header row
        header = [
            Paragraph("Items", s['table_header']),
            Paragraph("Price", s['table_header']),
            Paragraph("Qty", s['table_header']),
            Paragraph("Total", s['table_header']),
        ]

        data = [header]

        for item in self.invoice.items.all():
            unit_price = float(item.unit_price) if item.unit_price else 0
            line_total = float(item.line_total) if item.line_total else 0
            qty = item.quantity or 0

            row = [
                Paragraph(str(item.product.name), s['table_cell']),
                Paragraph(f"Rs. {unit_price:,.2f}", s['table_cell_right']),
                Paragraph(str(qty), s['table_cell_center']),
                Paragraph(f"Rs. {line_total:,.2f}", s['table_cell_right']),
            ]
            data.append(row)

        col_widths = [3 * inch, 1.3 * inch, 0.8 * inch, 1.5 * inch]
        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), self.LIGHT_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.MEDIUM),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),

            # Data rows
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),

            # Borders
            ('LINEBELOW', (0, 0), (-1, 0), 1, self.BORDER),
            ('LINEBELOW', (0, 1), (-1, -2), 0.5, HexColor('#e5e7eb')),
            ('LINEBELOW', (0, -1), (-1, -1), 1, self.BORDER),

            # Alignment
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),

            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        return table

    def _build_totals_section(self):
        """Right-aligned totals block."""
        s = self.styles
        inv = self.invoice

        subtotal = float(inv.subtotal) if inv.subtotal else 0
        tax = float(inv.tax_amount) if inv.tax_amount else 0
        total = float(inv.total_amount) if inv.total_amount else 0

        data = [
            ['', Paragraph("Sub Total", s['total_label']),
             Paragraph(f"Rs. {subtotal:,.2f}", s['total_value'])],
            ['', Paragraph("Tax (GST)", s['total_label']),
             Paragraph(f"Rs. {tax:,.2f}", s['total_value'])],
            ['', '', ''],  # spacer row
            ['', Paragraph("Total", s['grand_total_label']),
             Paragraph(f"Rs. {total:,.2f}", s['grand_total_value'])],
        ]

        table = Table(data, colWidths=[3 * inch, 2 * inch, 1.6 * inch])
        table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            # Line above grand total
            ('LINEABOVE', (1, 3), (-1, 3), 1.5, self.DARK),
            ('BOTTOMPADDING', (0, 3), (-1, 3), 8),
            ('TOPPADDING', (0, 3), (-1, 3), 8),
        ]))
        return table

    def _build_payment_info(self):
        """Payment method info on the left."""
        inv = self.invoice
        s = self.styles

        # Determine payment info
        payment_method = "Cash"
        payments = inv.payments.all()
        if payments.exists():
            p = payments.first()
            method_map = {
                'cash': 'Cash',
                'upi': 'UPI',
                'card': 'Credit/Debit Card',
                'bank_transfer': 'Bank Transfer',
                'multiple': 'Multiple Methods',
            }
            raw = getattr(p, 'payment_method', 'cash')
            payment_method = method_map.get(raw, str(raw).title())

        paid = float(inv.paid_amount) if inv.paid_amount else 0
        balance = float(inv.remaining_balance) if inv.remaining_balance else 0

        left_data = [
            [Paragraph("<b>Payment</b>", s['section_label']),
             Paragraph(f": {payment_method}", s['customer_info'])],
        ]
        if paid > 0:
            left_data.append([
                Paragraph("<b>Paid</b>", s['section_label']),
                Paragraph(f": Rs. {paid:,.2f}", s['customer_info']),
            ])
        if balance > 0:
            left_data.append([
                Paragraph("<b>Balance</b>", s['section_label']),
                Paragraph(f": Rs. {balance:,.2f}", s['customer_info']),
            ])

        table = Table(left_data, colWidths=[1.2 * inch, 3 * inch])
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        return table

    def _build_footer(self):
        """Terms and thank you message."""
        s = self.styles

        data = [
            [
                [
                    Paragraph("<b>Terms and Conditions Apply</b>", s['footer']),
                    Paragraph(
                        "Goods once sold will not be taken back or exchanged.<br/>"
                        "All disputes subject to local jurisdiction.",
                        s['footer_text']
                    ),
                ],
                Paragraph("Thank You! Visit Again", s['thank_you']),
            ]
        ]
        table = Table(data, colWidths=[4 * inch, 3 * inch])
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        return table


def generate_invoice_pdf(invoice):
    """Generate and return invoice PDF for inline browser viewing."""
    pdf_generator = ProfessionalInvoicePDF(invoice)
    buffer = pdf_generator.generate()
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="invoice_{invoice.invoice_number}.pdf"'
    return response
