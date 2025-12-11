"""
Tests for PDF receipt generation.
"""
import pytest
from decimal import Decimal
from io import BytesIO

from apps.sales.models import Sale, SaleItem
from apps.sales.pdf_service import ReceiptPDFService


@pytest.mark.django_db
class TestReceiptPDFService:
    """Tests for the PDF receipt generation service."""

    def test_generate_receipt_returns_buffer(
        self, branch, cashier_user, product
    ):
        """Test that generate_receipt returns a BytesIO buffer."""
        sale = Sale.objects.create(
            sale_number='TST-20241211-0001',
            branch=branch,
            cashier=cashier_user,
            subtotal=Decimal('100.00'),
            tax_amount=Decimal('16.00'),
            total=Decimal('116.00'),
            payment_method='cash',
            amount_tendered=Decimal('150.00'),
            change_amount=Decimal('34.00'),
        )

        SaleItem.objects.create(
            sale=sale,
            product=product,
            quantity=1,
            unit_price=Decimal('100.00'),
            cost_price=Decimal('50.00'),
            product_name='Producto Test',
            product_sku='PRD-001',
        )

        pdf_buffer = ReceiptPDFService.generate_receipt(sale)

        assert isinstance(pdf_buffer, BytesIO)
        assert pdf_buffer.tell() == 0  # Should be at start after seek(0)

    def test_generate_receipt_has_pdf_content(
        self, branch, cashier_user, product
    ):
        """Test that the generated buffer contains PDF content."""
        sale = Sale.objects.create(
            sale_number='TST-20241211-0001',
            branch=branch,
            cashier=cashier_user,
            subtotal=Decimal('100.00'),
            tax_amount=Decimal('16.00'),
            total=Decimal('116.00'),
            payment_method='cash',
        )

        SaleItem.objects.create(
            sale=sale,
            product=product,
            quantity=1,
            unit_price=Decimal('100.00'),
            cost_price=Decimal('50.00'),
            product_name='Producto Test',
            product_sku='PRD-001',
        )

        pdf_buffer = ReceiptPDFService.generate_receipt(sale)
        content = pdf_buffer.getvalue()

        # PDF files start with %PDF
        assert content[:4] == b'%PDF'

    def test_generate_receipt_multiple_items(
        self, branch, cashier_user, product, second_product
    ):
        """Test receipt generation with multiple items."""
        sale = Sale.objects.create(
            sale_number='TST-20241211-0001',
            branch=branch,
            cashier=cashier_user,
            subtotal=Decimal('200.00'),
            tax_amount=Decimal('32.00'),
            total=Decimal('232.00'),
            payment_method='card',
            payment_reference='****1234',
        )

        SaleItem.objects.create(
            sale=sale,
            product=product,
            quantity=1,
            unit_price=Decimal('100.00'),
            cost_price=Decimal('50.00'),
            product_name='Producto Uno',
            product_sku='PRD-001',
        )

        SaleItem.objects.create(
            sale=sale,
            product=second_product,
            quantity=2,
            unit_price=Decimal('50.00'),
            cost_price=Decimal('25.00'),
            product_name='Producto Dos',
            product_sku='PRD-002',
        )

        pdf_buffer = ReceiptPDFService.generate_receipt(sale)
        content = pdf_buffer.getvalue()

        assert len(content) > 0
        assert content[:4] == b'%PDF'

    def test_generate_receipt_with_discount(
        self, branch, cashier_user, product
    ):
        """Test receipt with discount applied."""
        sale = Sale.objects.create(
            sale_number='TST-20241211-0001',
            branch=branch,
            cashier=cashier_user,
            subtotal=Decimal('100.00'),
            discount_amount=Decimal('10.00'),
            tax_amount=Decimal('14.40'),
            total=Decimal('104.40'),
            payment_method='cash',
            amount_tendered=Decimal('110.00'),
            change_amount=Decimal('5.60'),
        )

        SaleItem.objects.create(
            sale=sale,
            product=product,
            quantity=1,
            unit_price=Decimal('100.00'),
            cost_price=Decimal('50.00'),
            product_name='Producto Test',
            product_sku='PRD-001',
        )

        pdf_buffer = ReceiptPDFService.generate_receipt(sale)
        content = pdf_buffer.getvalue()

        assert len(content) > 0

    def test_generate_receipt_voided_sale(
        self, branch, cashier_user, product
    ):
        """Test receipt for voided sale shows voided indicator."""
        from django.utils import timezone

        sale = Sale.objects.create(
            sale_number='TST-20241211-0001',
            branch=branch,
            cashier=cashier_user,
            subtotal=Decimal('100.00'),
            total=Decimal('116.00'),
            payment_method='cash',
            status='voided',
            voided_at=timezone.now(),
            void_reason='Error en el pedido',
        )

        SaleItem.objects.create(
            sale=sale,
            product=product,
            quantity=1,
            unit_price=Decimal('100.00'),
            cost_price=Decimal('50.00'),
            product_name='Producto Test',
            product_sku='PRD-001',
        )

        pdf_buffer = ReceiptPDFService.generate_receipt(sale)
        content = pdf_buffer.getvalue()

        assert len(content) > 0
        assert content[:4] == b'%PDF'

    def test_format_currency(self):
        """Test currency formatting helper."""
        assert ReceiptPDFService._format_currency(Decimal('100.00')) == '$100.00'
        assert ReceiptPDFService._format_currency(Decimal('1234.56')) == '$1,234.56'
        assert ReceiptPDFService._format_currency(Decimal('0.99')) == '$0.99'

    def test_truncate_text(self):
        """Test text truncation helper."""
        assert ReceiptPDFService._truncate_text('Short', 20) == 'Short'
        assert ReceiptPDFService._truncate_text('This is a very long text', 10) == 'This is...'
        assert len(ReceiptPDFService._truncate_text('x' * 100, 20)) == 20
