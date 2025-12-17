from django.db import transaction
from django.db.models import F
from typing import Optional

from core.exceptions import InsufficientStockError, ValidationError
from .models import Product, BranchStock, StockMovement


class StockService:
    """
    Service class for stock management operations.
    Handles stock adjustments, transfers, and movement logging.
    """

    @staticmethod
    @transaction.atomic
    def adjust_stock(
        product: Product,
        branch_id: int,
        quantity: int,
        movement_type: str,
        user,
        reference: str = '',
        notes: str = '',
        related_branch_id: Optional[int] = None
    ) -> StockMovement:
        """
        Adjust stock for a product at a branch.
        Creates a stock movement record for audit trail.

        Args:
            product: Product instance
            branch_id: Branch ID
            quantity: Amount to adjust (positive for add, negative for subtract)
            movement_type: Type of movement (from StockMovement.MOVEMENT_TYPES)
            user: User performing the action
            reference: Optional reference (invoice number, etc.)
            notes: Optional notes
            related_branch_id: For transfers, the other branch involved

        Returns:
            StockMovement record
        """
        # Get or create branch stock record
        branch_stock, created = BranchStock.objects.select_for_update().get_or_create(
            product=product,
            branch_id=branch_id,
            defaults={'quantity': 0}
        )

        previous_quantity = branch_stock.quantity
        new_quantity = previous_quantity + quantity

        # Prevent negative stock
        if new_quantity < 0:
            raise InsufficientStockError(
                f"Stock insuficiente. Disponible: {previous_quantity}, "
                f"Solicitado: {abs(quantity)}"
            )

        # Update stock
        branch_stock.quantity = new_quantity
        branch_stock.save()

        # Create movement record
        movement = StockMovement.objects.create(
            product=product,
            branch_id=branch_id,
            movement_type=movement_type,
            quantity=quantity,
            previous_quantity=previous_quantity,
            new_quantity=new_quantity,
            reference=reference,
            related_branch_id=related_branch_id,
            notes=notes,
            created_by=user
        )

        return movement

    @classmethod
    @transaction.atomic
    def transfer_stock(
        cls,
        product: Product,
        from_branch_id: int,
        to_branch_id: int,
        quantity: int,
        user,
        notes: str = ''
    ) -> tuple[StockMovement, StockMovement]:
        """
        Transfer stock between branches.
        Creates two movement records (out and in).

        Args:
            product: Product instance
            from_branch_id: Source branch ID
            to_branch_id: Destination branch ID
            quantity: Amount to transfer (must be positive)
            user: User performing the transfer
            notes: Optional notes

        Returns:
            Tuple of (outgoing_movement, incoming_movement)
        """
        if quantity <= 0:
            raise ValidationError("La cantidad a transferir debe ser positiva")

        if from_branch_id == to_branch_id:
            raise ValidationError("Las sucursales de origen y destino deben ser diferentes")

        # Check source stock availability
        try:
            source_stock = BranchStock.objects.get(
                product=product,
                branch_id=from_branch_id
            )
            if source_stock.available_quantity < quantity:
                raise InsufficientStockError(
                    f"Stock insuficiente en sucursal origen. "
                    f"Disponible: {source_stock.available_quantity}, Solicitado: {quantity}"
                )
        except BranchStock.DoesNotExist:
            raise InsufficientStockError("No hay stock del producto en la sucursal origen")

        # Perform transfer - subtract from source
        outgoing_movement = cls.adjust_stock(
            product=product,
            branch_id=from_branch_id,
            quantity=-quantity,
            movement_type='transfer_out',
            user=user,
            related_branch_id=to_branch_id,
            notes=notes
        )

        # Add to destination
        incoming_movement = cls.adjust_stock(
            product=product,
            branch_id=to_branch_id,
            quantity=quantity,
            movement_type='transfer_in',
            user=user,
            related_branch_id=from_branch_id,
            notes=notes
        )

        return outgoing_movement, incoming_movement

    @classmethod
    @transaction.atomic
    def process_sale(
        cls,
        product: Product,
        branch_id: int,
        quantity: int,
        user,
        sale_reference: str
    ) -> StockMovement:
        """
        Process a sale - reduce stock.

        Args:
            product: Product instance
            branch_id: Branch ID where sale occurred
            quantity: Quantity sold (must be positive)
            user: User processing the sale
            sale_reference: Sale/invoice reference

        Returns:
            StockMovement record
        """
        if quantity <= 0:
            raise ValidationError("La cantidad vendida debe ser positiva")

        # Check stock availability
        try:
            branch_stock = BranchStock.objects.get(
                product=product,
                branch_id=branch_id
            )
            if branch_stock.available_quantity < quantity:
                raise InsufficientStockError(
                    f"Stock insuficiente. "
                    f"Disponible: {branch_stock.available_quantity}, Solicitado: {quantity}"
                )
        except BranchStock.DoesNotExist:
            raise InsufficientStockError("No hay stock del producto en esta sucursal")

        return cls.adjust_stock(
            product=product,
            branch_id=branch_id,
            quantity=-quantity,
            movement_type='sale',
            user=user,
            reference=sale_reference
        )

    @classmethod
    @transaction.atomic
    def process_purchase(
        cls,
        product: Product,
        branch_id: int,
        quantity: int,
        user,
        purchase_reference: str
    ) -> StockMovement:
        """
        Process a purchase - increase stock.

        Args:
            product: Product instance
            branch_id: Branch ID receiving the stock
            quantity: Quantity received (must be positive)
            user: User processing the purchase
            purchase_reference: Purchase order/invoice reference

        Returns:
            StockMovement record
        """
        if quantity <= 0:
            raise ValidationError("La cantidad recibida debe ser positiva")

        return cls.adjust_stock(
            product=product,
            branch_id=branch_id,
            quantity=quantity,
            movement_type='purchase',
            user=user,
            reference=purchase_reference
        )

    @classmethod
    @transaction.atomic
    def manual_adjustment(
        cls,
        product: Product,
        branch_id: int,
        adjustment_type: str,
        quantity: int,
        user,
        reason: str,
        notes: str = ''
    ) -> StockMovement:
        """
        Manual stock adjustment (inventory count, damage, etc.).

        Args:
            product: Product instance
            branch_id: Branch ID
            adjustment_type: 'add', 'subtract', or 'set'
            quantity: Amount (for 'set', this is the new total)
            user: User performing the adjustment
            reason: Required reason for adjustment
            notes: Optional additional notes

        Returns:
            StockMovement record
        """
        # Use select_for_update to prevent race conditions when calculating 'set' adjustment
        branch_stock, _ = BranchStock.objects.select_for_update().get_or_create(
            product=product,
            branch_id=branch_id,
            defaults={'quantity': 0}
        )

        if adjustment_type == 'add':
            change = quantity
            movement_type = 'adjustment_in'
        elif adjustment_type == 'subtract':
            change = -quantity
            movement_type = 'adjustment_out'
        elif adjustment_type == 'set':
            change = quantity - branch_stock.quantity
            movement_type = 'adjustment_in' if change >= 0 else 'adjustment_out'
        else:
            raise ValidationError(f"Tipo de ajuste inválido: {adjustment_type}")

        full_notes = f"Razón: {reason}"
        if notes:
            full_notes += f"\n{notes}"

        return cls.adjust_stock(
            product=product,
            branch_id=branch_id,
            quantity=change,
            movement_type=movement_type,
            user=user,
            notes=full_notes
        )

    @staticmethod
    def reserve_stock(
        product: Product,
        branch_id: int,
        quantity: int
    ) -> bool:
        """
        Reserve stock for a pending order.

        Args:
            product: Product instance
            branch_id: Branch ID
            quantity: Amount to reserve

        Returns:
            True if reservation successful, False otherwise
        """
        try:
            branch_stock = BranchStock.objects.select_for_update().get(
                product=product,
                branch_id=branch_id
            )
            if branch_stock.available_quantity >= quantity:
                branch_stock.reserved_quantity = F('reserved_quantity') + quantity
                branch_stock.save()
                return True
            return False
        except BranchStock.DoesNotExist:
            return False

    @staticmethod
    def release_reservation(
        product: Product,
        branch_id: int,
        quantity: int
    ) -> bool:
        """
        Release previously reserved stock.

        Args:
            product: Product instance
            branch_id: Branch ID
            quantity: Amount to release

        Returns:
            True if release successful
        """
        try:
            updated = BranchStock.objects.filter(
                product=product,
                branch_id=branch_id,
                reserved_quantity__gte=quantity
            ).update(
                reserved_quantity=F('reserved_quantity') - quantity
            )
            return updated > 0
        except Exception:
            return False

    @classmethod
    def record_sale(
        cls,
        product: Product,
        branch,
        quantity: int,
        reference: str,
        user,
        notes: str = ''
    ) -> StockMovement:
        """
        Record a sale transaction - reduces stock.
        Alias for process_sale with branch object support.
        """
        branch_id = branch.id if hasattr(branch, 'id') else branch
        return cls.process_sale(
            product=product,
            branch_id=branch_id,
            quantity=quantity,
            user=user,
            sale_reference=reference
        )

    @classmethod
    @transaction.atomic
    def record_return_customer(
        cls,
        product: Product,
        branch,
        quantity: int,
        reference: str,
        user,
        notes: str = ''
    ) -> StockMovement:
        """
        Record a customer return - increases stock.

        Args:
            product: Product instance
            branch: Branch instance or ID
            quantity: Quantity returned (must be positive)
            reference: Return/refund reference
            user: User processing the return
            notes: Optional notes

        Returns:
            StockMovement record
        """
        if quantity <= 0:
            raise ValidationError("La cantidad devuelta debe ser positiva")

        branch_id = branch.id if hasattr(branch, 'id') else branch

        return cls.adjust_stock(
            product=product,
            branch_id=branch_id,
            quantity=quantity,
            movement_type='return_customer',
            user=user,
            reference=reference,
            notes=notes
        )
