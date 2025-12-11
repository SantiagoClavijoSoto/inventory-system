"""
PDF Receipt Generation Service using ReportLab.
Generates thermal printer-compatible receipts (80mm width).
"""
from io import BytesIO
from decimal import Decimal
from reportlab.lib.pagesizes import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

from .models import Sale


# Receipt width for 80mm thermal printer
RECEIPT_WIDTH = 72 * mm
RECEIPT_MARGIN = 4 * mm


class ReceiptPDFService:
    """
    Service for generating PDF receipts for sales.
    Designed for 80mm thermal printer paper.
    """

    @classmethod
    def generate_receipt(cls, sale: Sale) -> BytesIO:
        """
        Generate a PDF receipt for a sale.

        Args:
            sale: Sale instance to generate receipt for

        Returns:
            BytesIO buffer containing the PDF
        """
        buffer = BytesIO()

        # Create document with thermal receipt dimensions
        doc = SimpleDocTemplate(
            buffer,
            pagesize=(RECEIPT_WIDTH, 1000 * mm),  # Variable height
            leftMargin=RECEIPT_MARGIN,
            rightMargin=RECEIPT_MARGIN,
            topMargin=RECEIPT_MARGIN,
            bottomMargin=RECEIPT_MARGIN,
        )

        # Build the receipt content
        elements = cls._build_receipt_content(sale)

        # Generate PDF
        doc.build(elements)
        buffer.seek(0)

        return buffer

    @classmethod
    def _build_receipt_content(cls, sale: Sale) -> list:
        """Build the receipt content elements."""
        elements = []
        styles = cls._get_styles()

        # Header - Business name
        elements.append(Paragraph(sale.branch.name.upper(), styles['header']))
        elements.append(Spacer(1, 2 * mm))

        # Branch info
        if sale.branch.address:
            elements.append(Paragraph(sale.branch.address, styles['small_center']))
        if sale.branch.city:
            city_state = f"{sale.branch.city}"
            if sale.branch.state:
                city_state += f", {sale.branch.state}"
            elements.append(Paragraph(city_state, styles['small_center']))
        if sale.branch.phone:
            elements.append(Paragraph(f"Tel: {sale.branch.phone}", styles['small_center']))

        elements.append(Spacer(1, 3 * mm))

        # Divider
        elements.append(Paragraph("-" * 40, styles['center']))
        elements.append(Spacer(1, 2 * mm))

        # Sale info
        elements.append(Paragraph(f"<b>VENTA #{sale.sale_number}</b>", styles['center']))
        elements.append(Paragraph(
            sale.created_at.strftime('%d/%m/%Y %H:%M'),
            styles['small_center']
        ))
        elements.append(Paragraph(f"Cajero: {sale.cashier.get_full_name()}", styles['small_center']))

        elements.append(Spacer(1, 3 * mm))
        elements.append(Paragraph("-" * 40, styles['center']))
        elements.append(Spacer(1, 2 * mm))

        # Items table
        items_data = [['Producto', 'Cant', 'Precio', 'Total']]
        for item in sale.items.all():
            items_data.append([
                cls._truncate_text(item.product_name, 18),
                str(item.quantity),
                cls._format_currency(item.unit_price),
                cls._format_currency(item.subtotal),
            ])

        items_table = Table(
            items_data,
            colWidths=[28 * mm, 10 * mm, 14 * mm, 14 * mm],
        )
        items_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.black),
        ]))
        elements.append(items_table)

        elements.append(Spacer(1, 3 * mm))
        elements.append(Paragraph("-" * 40, styles['center']))
        elements.append(Spacer(1, 2 * mm))

        # Totals
        totals_data = []
        totals_data.append(['Subtotal:', cls._format_currency(sale.subtotal)])

        if sale.discount_amount > 0:
            totals_data.append(['Descuento:', f"-{cls._format_currency(sale.discount_amount)}"])

        totals_data.append(['IVA (16%):', cls._format_currency(sale.tax_amount)])
        totals_data.append(['<b>TOTAL:</b>', f"<b>{cls._format_currency(sale.total)}</b>"])

        for row in totals_data:
            elements.append(cls._create_total_row(row[0], row[1], styles))

        elements.append(Spacer(1, 3 * mm))

        # Payment info
        elements.append(Paragraph("-" * 40, styles['center']))
        elements.append(Spacer(1, 2 * mm))

        payment_method = sale.get_payment_method_display()
        elements.append(Paragraph(f"Método de pago: {payment_method}", styles['small']))

        if sale.payment_method == 'cash':
            elements.append(Paragraph(
                f"Recibido: {cls._format_currency(sale.amount_tendered)}",
                styles['small']
            ))
            elements.append(Paragraph(
                f"Cambio: {cls._format_currency(sale.change_amount)}",
                styles['small']
            ))
        elif sale.payment_reference:
            elements.append(Paragraph(
                f"Ref: {sale.payment_reference}",
                styles['small']
            ))

        # Customer info if available
        if sale.customer_name:
            elements.append(Spacer(1, 2 * mm))
            elements.append(Paragraph(f"Cliente: {sale.customer_name}", styles['small']))

        elements.append(Spacer(1, 4 * mm))

        # Footer
        elements.append(Paragraph("-" * 40, styles['center']))
        elements.append(Spacer(1, 2 * mm))
        elements.append(Paragraph("¡Gracias por su compra!", styles['center']))
        elements.append(Paragraph("Vuelva pronto", styles['small_center']))

        elements.append(Spacer(1, 4 * mm))

        # Voided indicator if applicable
        if sale.status == 'voided':
            elements.append(Spacer(1, 2 * mm))
            elements.append(Paragraph("*** VENTA ANULADA ***", styles['header']))
            elements.append(Paragraph(
                f"Anulada: {sale.voided_at.strftime('%d/%m/%Y %H:%M')}",
                styles['small_center']
            ))
            if sale.void_reason:
                elements.append(Paragraph(f"Razón: {sale.void_reason}", styles['small_center']))

        return elements

    @classmethod
    def _get_styles(cls) -> dict:
        """Get custom styles for the receipt."""
        styles = getSampleStyleSheet()

        custom_styles = {
            'header': ParagraphStyle(
                'header',
                parent=styles['Normal'],
                fontSize=12,
                fontName='Helvetica-Bold',
                alignment=TA_CENTER,
                spaceAfter=2 * mm,
            ),
            'center': ParagraphStyle(
                'center',
                parent=styles['Normal'],
                fontSize=9,
                alignment=TA_CENTER,
            ),
            'small_center': ParagraphStyle(
                'small_center',
                parent=styles['Normal'],
                fontSize=8,
                alignment=TA_CENTER,
            ),
            'small': ParagraphStyle(
                'small',
                parent=styles['Normal'],
                fontSize=8,
                alignment=TA_LEFT,
            ),
            'small_right': ParagraphStyle(
                'small_right',
                parent=styles['Normal'],
                fontSize=8,
                alignment=TA_RIGHT,
            ),
            'total': ParagraphStyle(
                'total',
                parent=styles['Normal'],
                fontSize=10,
                fontName='Helvetica-Bold',
                alignment=TA_RIGHT,
            ),
        }

        return custom_styles

    @classmethod
    def _create_total_row(cls, label: str, value: str, styles: dict) -> Table:
        """Create a row for the totals section."""
        table = Table(
            [[Paragraph(label, styles['small']), Paragraph(value, styles['small_right'])]],
            colWidths=[40 * mm, 24 * mm],
        )
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        return table

    @staticmethod
    def _format_currency(value: Decimal) -> str:
        """Format a decimal value as currency."""
        return f"${value:,.2f}"

    @staticmethod
    def _truncate_text(text: str, max_length: int) -> str:
        """Truncate text to max length with ellipsis."""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."
