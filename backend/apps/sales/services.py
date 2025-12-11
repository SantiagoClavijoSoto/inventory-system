"""
Sales processing service.
Handles business logic for sale transactions with atomic operations.
"""
from decimal import Decimal
from typing import List, Dict, Any, Optional
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.inventory.models import Product, BranchStock
from apps.inventory.services import StockService
from apps.branches.models import Branch
from apps.users.models import User
from .models import Sale, SaleItem, DailyCashRegister


class SaleService:
    """
    Service for processing sales with stock management integration.
    All operations are atomic to ensure data consistency.
    """

    @classmethod
    @transaction.atomic
    def create_sale(
        cls,
        branch: Branch,
        cashier: User,
        items: List[Dict[str, Any]],
        payment_method: str,
        amount_tendered: Decimal = Decimal('0.00'),
        discount_percent: Decimal = Decimal('0.00'),
        discount_amount: Decimal = Decimal('0.00'),
        customer_name: str = '',
        customer_phone: str = '',
        customer_email: str = '',
        payment_reference: str = '',
        notes: str = ''
    ) -> Sale:
        """
        Create a complete sale with stock deduction.

        Args:
            branch: Branch where sale occurs
            cashier: User processing the sale
            items: List of dicts with 'product_id', 'quantity', optional 'discount'
            payment_method: cash, card, transfer, or mixed
            amount_tendered: Amount given by customer (for cash)
            discount_percent: Global discount percentage
            discount_amount: Fixed discount amount
            customer_name: Optional customer name
            customer_phone: Optional customer phone
            customer_email: Optional customer email
            payment_reference: Reference for card/transfer payments
            notes: Additional notes

        Returns:
            Created Sale instance

        Raises:
            ValidationError: If validation fails
            InsufficientStockError: If not enough stock
        """
        # Validate items
        if not items:
            raise ValidationError("La venta debe tener al menos un producto")

        # Generate sale number
        sale_number = Sale.generate_sale_number(branch.code)

        # Create sale header
        sale = Sale.objects.create(
            sale_number=sale_number,
            branch=branch,
            cashier=cashier,
            payment_method=payment_method,
            amount_tendered=amount_tendered,
            discount_percent=discount_percent,
            discount_amount=discount_amount,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            payment_reference=payment_reference,
            notes=notes,
            status='completed'
        )

        # Process each item
        for item_data in items:
            cls._add_sale_item(sale, item_data, branch, cashier)

        # Calculate totals
        sale.calculate_totals()
        sale.save()

        return sale

    @classmethod
    def _add_sale_item(
        cls,
        sale: Sale,
        item_data: Dict[str, Any],
        branch: Branch,
        user: User
    ) -> SaleItem:
        """
        Add an item to the sale and deduct stock.
        """
        product_id = item_data.get('product_id')
        quantity = item_data.get('quantity', 1)
        item_discount = Decimal(str(item_data.get('discount', '0.00')))
        custom_price = item_data.get('custom_price')  # For price overrides

        # Get product
        try:
            product = Product.objects.select_for_update().get(
                id=product_id,
                is_deleted=False,
                is_active=True,
                is_sellable=True
            )
        except Product.DoesNotExist:
            raise ValidationError(f"Producto con ID {product_id} no encontrado o no disponible")

        # Check stock availability
        try:
            branch_stock = BranchStock.objects.select_for_update().get(
                product=product,
                branch=branch
            )
        except BranchStock.DoesNotExist:
            raise ValidationError(f"Producto '{product.name}' no tiene stock en esta sucursal")

        if branch_stock.available_quantity < quantity:
            raise ValidationError(
                f"Stock insuficiente para '{product.name}'. "
                f"Disponible: {branch_stock.available_quantity}, Solicitado: {quantity}"
            )

        # Use custom price if provided and authorized, otherwise use sale price
        unit_price = Decimal(str(custom_price)) if custom_price else product.sale_price

        # Create sale item
        sale_item = SaleItem.objects.create(
            sale=sale,
            product=product,
            quantity=quantity,
            unit_price=unit_price,
            cost_price=product.cost_price,
            discount_amount=item_discount,
            product_name=product.name,
            product_sku=product.sku,
            subtotal=Decimal('0.00')  # Will be calculated in save()
        )

        # Deduct stock using StockService
        StockService.record_sale(
            product=product,
            branch=branch,
            quantity=quantity,
            reference=sale.sale_number,
            user=user
        )

        return sale_item

    @classmethod
    @transaction.atomic
    def void_sale(
        cls,
        sale: Sale,
        user: User,
        reason: str
    ) -> Sale:
        """
        Void a sale and restore stock.

        Args:
            sale: Sale to void
            user: User voiding the sale
            reason: Reason for voiding

        Returns:
            Updated Sale instance
        """
        if sale.status == 'voided':
            raise ValidationError("Esta venta ya fue anulada")

        # Restore stock for each item
        for item in sale.items.all():
            StockService.record_return_customer(
                product=item.product,
                branch=sale.branch,
                quantity=item.quantity,
                reference=f"ANULACION-{sale.sale_number}",
                user=user,
                notes=f"Anulación de venta: {reason}"
            )

        # Update sale status
        sale.status = 'voided'
        sale.voided_at = timezone.now()
        sale.voided_by = user
        sale.void_reason = reason
        sale.save()

        return sale

    @classmethod
    @transaction.atomic
    def refund_items(
        cls,
        sale: Sale,
        items_to_refund: List[Dict[str, Any]],
        user: User,
        reason: str
    ) -> 'Sale':
        """
        Create a partial refund for specific items.

        Args:
            sale: Original sale
            items_to_refund: List of dicts with 'sale_item_id' and 'quantity'
            user: User processing refund
            reason: Reason for refund

        Returns:
            New refund Sale instance
        """
        # Create refund sale (negative amounts)
        refund = Sale.objects.create(
            sale_number=f"REF-{sale.sale_number}",
            branch=sale.branch,
            cashier=user,
            payment_method=sale.payment_method,
            status='refunded',
            notes=f"Reembolso de venta {sale.sale_number}: {reason}"
        )

        total_refund = Decimal('0.00')

        for item_data in items_to_refund:
            sale_item_id = item_data.get('sale_item_id')
            refund_qty = item_data.get('quantity')

            try:
                original_item = SaleItem.objects.get(id=sale_item_id, sale=sale)
            except SaleItem.DoesNotExist:
                raise ValidationError(f"Item {sale_item_id} no encontrado en la venta")

            if refund_qty > original_item.quantity:
                raise ValidationError(
                    f"Cantidad a reembolsar ({refund_qty}) excede la cantidad original ({original_item.quantity})"
                )

            # Create refund item
            refund_subtotal = original_item.unit_price * refund_qty
            SaleItem.objects.create(
                sale=refund,
                product=original_item.product,
                quantity=refund_qty,
                unit_price=-original_item.unit_price,  # Negative for refund
                cost_price=original_item.cost_price,
                discount_amount=Decimal('0.00'),
                product_name=original_item.product_name,
                product_sku=original_item.product_sku,
                subtotal=-refund_subtotal
            )

            # Restore stock
            StockService.record_return_customer(
                product=original_item.product,
                branch=sale.branch,
                quantity=refund_qty,
                reference=refund.sale_number,
                user=user,
                notes=f"Reembolso: {reason}"
            )

            total_refund += refund_subtotal

        # Set refund totals (negative)
        refund.subtotal = -total_refund
        refund.total = -total_refund
        refund.save()

        return refund

    @classmethod
    def get_daily_summary(
        cls,
        branch: Branch,
        date: Optional['timezone.datetime'] = None
    ) -> Dict[str, Any]:
        """
        Get sales summary for a specific day.

        Args:
            branch: Branch to get summary for
            date: Date to query (defaults to today)

        Returns:
            Dictionary with sales statistics
        """
        from django.db.models import Sum, Count, Avg

        if date is None:
            date = timezone.now().date()

        sales = Sale.objects.filter(
            branch=branch,
            created_at__date=date,
            status='completed'
        )

        summary = sales.aggregate(
            total_sales=Sum('total'),
            total_items=Sum('items__quantity'),
            sale_count=Count('id'),
            avg_sale=Avg('total'),
            total_discount=Sum('discount_amount')
        )

        # Get breakdown by payment method
        cash_total = sales.filter(payment_method='cash').aggregate(
            total=Sum('total'))['total'] or Decimal('0.00')
        card_total = sales.filter(payment_method='card').aggregate(
            total=Sum('total'))['total'] or Decimal('0.00')
        transfer_total = sales.filter(payment_method='transfer').aggregate(
            total=Sum('total'))['total'] or Decimal('0.00')

        # Get voided sales
        voided_count = Sale.objects.filter(
            branch=branch,
            voided_at__date=date,
            status='voided'
        ).count()

        return {
            'date': date,
            'branch': branch.name,
            'total_sales': summary['total_sales'] or Decimal('0.00'),
            'total_items_sold': summary['total_items'] or 0,
            'sale_count': summary['sale_count'] or 0,
            'average_sale': summary['avg_sale'] or Decimal('0.00'),
            'total_discounts': summary['total_discount'] or Decimal('0.00'),
            'cash_total': cash_total,
            'card_total': card_total,
            'transfer_total': transfer_total,
            'voided_count': voided_count,
        }

    @classmethod
    def get_top_products(
        cls,
        branch: Branch,
        date_from: Optional['timezone.datetime'] = None,
        date_to: Optional['timezone.datetime'] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get top selling products for a date range.
        """
        from django.db.models import Sum, F

        queryset = SaleItem.objects.filter(
            sale__branch=branch,
            sale__status='completed'
        )

        if date_from:
            queryset = queryset.filter(sale__created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(sale__created_at__lte=date_to)

        top_products = queryset.values(
            'product_id',
            'product_name',
            'product_sku'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum('subtotal'),
            total_profit=Sum(F('subtotal') - (F('cost_price') * F('quantity')))
        ).order_by('-total_quantity')[:limit]

        return list(top_products)


class CashRegisterService:
    """
    Service for managing daily cash register operations.
    """

    @classmethod
    @transaction.atomic
    def open_register(
        cls,
        branch: Branch,
        user: User,
        opening_amount: Decimal,
        date: Optional['timezone.datetime'] = None
    ) -> DailyCashRegister:
        """
        Open a new cash register for the day.
        """
        if date is None:
            date = timezone.now().date()

        # Check if register already exists
        existing = DailyCashRegister.objects.filter(
            branch=branch,
            date=date
        ).first()

        if existing:
            if not existing.is_closed:
                raise ValidationError("Ya existe una caja abierta para hoy")
            raise ValidationError("Ya existe un registro de caja para hoy")

        register = DailyCashRegister.objects.create(
            branch=branch,
            date=date,
            opening_amount=opening_amount,
            opened_by=user,
            opened_at=timezone.now(),
            expected_amount=opening_amount
        )

        return register

    @classmethod
    @transaction.atomic
    def close_register(
        cls,
        register: DailyCashRegister,
        user: User,
        closing_amount: Decimal,
        notes: str = ''
    ) -> DailyCashRegister:
        """
        Close a cash register and calculate differences.
        """
        if register.is_closed:
            raise ValidationError("Esta caja ya fue cerrada")

        # Calculate totals from sales
        register.calculate_totals()

        # Set closing info
        register.closing_amount = closing_amount
        register.closed_by = user
        register.closed_at = timezone.now()
        register.difference = closing_amount - register.expected_amount
        register.is_closed = True
        register.notes = notes
        register.save()

        return register

    @classmethod
    def get_current_register(cls, branch: Branch) -> Optional[DailyCashRegister]:
        """
        Get the current open register for a branch.
        """
        today = timezone.now().date()
        return DailyCashRegister.objects.filter(
            branch=branch,
            date=today,
            is_closed=False
        ).first()
