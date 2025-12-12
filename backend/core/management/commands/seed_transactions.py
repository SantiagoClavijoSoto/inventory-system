"""
Management command to seed transactional demo data.

Creates:
- Sales with SaleItems for each company/branch
- Daily cash registers
- Stock movements (initial stock, sales)
- Employee shifts
- Alerts (low stock, cash differences)

Run after seed_companies.
"""
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
import random

from apps.companies.models import Company
from apps.branches.models import Branch
from apps.users.models import User
from apps.inventory.models import Product, BranchStock, StockMovement
from apps.employees.models import Employee, Shift
from apps.sales.models import Sale, SaleItem, DailyCashRegister
from apps.alerts.models import Alert


class Command(BaseCommand):
    help = 'Seeds transactional demo data (sales, shifts, alerts)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days of historical data to generate (default: 7)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing transactional data before seeding',
        )

    def handle(self, *args, **options):
        days = options['days']

        if options['clear']:
            self.stdout.write('Clearing existing transactional data...')
            self._clear_data()

        self.stdout.write(f'Creating transactional demo data for {days} days...')

        with transaction.atomic():
            companies = Company.objects.filter(is_deleted=False)

            for company in companies:
                self.stdout.write(f'  Processing {company.name}...')
                self._create_transactions_for_company(company, days)

        self.stdout.write(self.style.SUCCESS('\nSuccessfully created transactional demo data!'))
        self._print_summary()

    def _clear_data(self):
        """Remove existing transactional data."""
        Alert.objects.all().delete()
        Shift.objects.all().delete()
        SaleItem.objects.all().delete()
        Sale.objects.all().delete()
        DailyCashRegister.objects.all().delete()
        StockMovement.objects.all().delete()
        self.stdout.write('  Transactional data cleared.')

    def _create_transactions_for_company(self, company: Company, days: int):
        """Create all transactional data for a company."""
        branches = Branch.objects.filter(company=company, is_active=True, is_deleted=False)

        for branch in branches:
            # Get cashiers for this branch
            cashiers = User.objects.filter(
                company=company,
                is_active=True,
                role__role_type__in=['cashier', 'supervisor', 'admin']
            ).filter(allowed_branches=branch)

            if not cashiers.exists():
                cashiers = User.objects.filter(company=company, is_active=True)[:2]

            # Get employees for shifts
            employees = Employee.objects.filter(
                branch=branch,
                status='active',
                is_deleted=False
            )

            # Create data for each day
            for day_offset in range(days, -1, -1):
                target_date = date.today() - timedelta(days=day_offset)

                # Create shifts for employees
                self._create_shifts(employees, branch, target_date)

                # Create daily cash register
                cash_register = self._create_cash_register(branch, cashiers, target_date)

                # Create sales for the day
                self._create_sales(branch, cashiers, target_date, cash_register)

        # Create some alerts for the company
        self._create_alerts(company, branches)

    def _create_shifts(self, employees, branch: Branch, target_date: date):
        """Create shifts for employees on a given day."""
        for employee in employees[:3]:  # Max 3 employees per day
            # Morning shift
            clock_in = timezone.make_aware(
                datetime.combine(target_date, datetime.strptime('08:00', '%H:%M').time())
            )
            clock_out = timezone.make_aware(
                datetime.combine(target_date, datetime.strptime('16:30', '%H:%M').time())
            )

            # Skip if shift already exists
            if Shift.objects.filter(employee=employee, clock_in__date=target_date).exists():
                continue

            shift = Shift.objects.create(
                employee=employee,
                branch=branch,
                clock_in=clock_in,
                clock_out=clock_out,
                break_start=timezone.make_aware(
                    datetime.combine(target_date, datetime.strptime('13:00', '%H:%M').time())
                ),
                break_end=timezone.make_aware(
                    datetime.combine(target_date, datetime.strptime('14:00', '%H:%M').time())
                ),
                notes=f'Turno regular {target_date}',
            )
            shift.calculate_hours()
            shift.save()

    def _create_cash_register(self, branch: Branch, cashiers, target_date: date) -> DailyCashRegister:
        """Create or get daily cash register."""
        cashier = cashiers.first() if cashiers.exists() else None

        register, created = DailyCashRegister.objects.get_or_create(
            branch=branch,
            date=target_date,
            defaults={
                'opening_amount': Decimal('5000.00'),
                'opened_by': cashier,
                'opened_at': timezone.make_aware(
                    datetime.combine(target_date, datetime.strptime('08:00', '%H:%M').time())
                ),
                'is_closed': target_date < date.today(),
            }
        )

        if created and target_date < date.today():
            # Close the register for past days
            register.closing_amount = register.opening_amount + Decimal(random.randint(2000, 8000))
            register.closed_by = cashier
            register.closed_at = timezone.make_aware(
                datetime.combine(target_date, datetime.strptime('20:00', '%H:%M').time())
            )
            register.is_closed = True
            register.save()

        return register

    def _create_sales(self, branch: Branch, cashiers, target_date: date, cash_register: DailyCashRegister):
        """Create sales for a branch on a given day."""
        # Get products available in this branch
        branch_stocks = BranchStock.objects.filter(
            branch=branch,
            quantity__gt=0
        ).select_related('product')

        if not branch_stocks.exists():
            return

        # Number of sales depends on branch size
        num_sales = random.randint(5, 15)
        payment_methods = ['cash', 'cash', 'cash', 'card', 'card', 'transfer']

        cash_total = Decimal('0.00')
        card_total = Decimal('0.00')
        transfer_total = Decimal('0.00')

        for sale_num in range(num_sales):
            # Skip if we already have sales for this day
            existing_sales = Sale.objects.filter(
                branch=branch,
                created_at__date=target_date
            ).count()
            if existing_sales >= num_sales:
                break

            cashier = random.choice(list(cashiers)) if cashiers.exists() else None
            payment_method = random.choice(payment_methods)

            # Create sale
            sale_time = timezone.make_aware(
                datetime.combine(
                    target_date,
                    datetime.strptime(f'{random.randint(9, 19)}:{random.randint(0, 59):02d}', '%H:%M').time()
                )
            )

            sale = Sale(
                branch=branch,
                cashier=cashier,
                payment_method=payment_method,
                status='completed',
            )
            sale.sale_number = sale.generate_sale_number(branch.code)
            sale.save()

            # Update created_at manually for historical data
            Sale.objects.filter(id=sale.id).update(created_at=sale_time)

            # Add 1-5 items to the sale
            num_items = random.randint(1, 5)
            selected_stocks = random.sample(list(branch_stocks), min(num_items, len(branch_stocks)))

            for stock in selected_stocks:
                product = stock.product
                quantity = random.randint(1, 3)

                # Don't sell more than available
                if quantity > stock.quantity:
                    quantity = max(1, int(stock.quantity))

                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=quantity,
                    unit_price=product.sale_price,
                    cost_price=product.cost_price,
                    product_name=product.name,
                    product_sku=product.sku,
                )

                # Update stock
                stock.quantity -= quantity
                stock.save()

                # Create stock movement
                StockMovement.objects.create(
                    product=product,
                    branch=branch,
                    movement_type='sale',
                    quantity=-quantity,
                    previous_quantity=stock.quantity + quantity,
                    new_quantity=stock.quantity,
                    reference=sale.sale_number,
                    created_by=cashier,
                )

            # Calculate sale totals
            sale.calculate_totals()

            # Apply tax from branch config
            if branch.tax_rate > 0:
                sale.tax_amount = sale.subtotal * (branch.tax_rate / 100)
                sale.total = sale.subtotal + sale.tax_amount

            # Payment details
            if payment_method == 'cash':
                sale.amount_tendered = sale.total + Decimal(random.choice([0, 5, 10, 20, 50]))
                sale.change_amount = sale.amount_tendered - sale.total
                cash_total += sale.total
            elif payment_method == 'card':
                sale.payment_reference = f'**** {random.randint(1000, 9999)}'
                card_total += sale.total
            else:
                sale.payment_reference = f'REF-{random.randint(100000, 999999)}'
                transfer_total += sale.total

            sale.save()

        # Update cash register totals
        if target_date < date.today() and cash_register.is_closed:
            cash_register.cash_sales_total = cash_total
            cash_register.card_sales_total = card_total
            cash_register.transfer_sales_total = transfer_total
            cash_register.expected_amount = cash_register.opening_amount + cash_total
            cash_register.difference = cash_register.closing_amount - cash_register.expected_amount
            cash_register.save()

    def _create_alerts(self, company: Company, branches):
        """Create some demo alerts."""
        # Low stock alerts
        low_stock_products = BranchStock.objects.filter(
            branch__company=company,
            quantity__lt=10
        ).select_related('product', 'branch')[:5]

        for stock in low_stock_products:
            Alert.objects.get_or_create(
                alert_type='low_stock',
                product=stock.product,
                branch=stock.branch,
                defaults={
                    'severity': 'medium' if stock.quantity > 5 else 'high',
                    'title': f'Stock bajo: {stock.product.name}',
                    'message': f'El producto {stock.product.name} tiene solo {stock.quantity} unidades en {stock.branch.name}.',
                    'status': 'active',
                }
            )

        # Cash difference alert (if any)
        registers_with_diff = DailyCashRegister.objects.filter(
            branch__company=company,
            is_closed=True
        ).exclude(difference=Decimal('0.00'))[:2]

        for register in registers_with_diff:
            if abs(register.difference) > 50:
                Alert.objects.get_or_create(
                    alert_type='cash_difference',
                    branch=register.branch,
                    defaults={
                        'severity': 'high' if abs(register.difference) > 200 else 'medium',
                        'title': f'Diferencia de caja: {register.branch.name}',
                        'message': f'Diferencia de ${register.difference} en el cierre del {register.date}.',
                        'status': 'active',
                        'metadata': {'date': str(register.date), 'difference': str(register.difference)},
                    }
                )

    def _print_summary(self):
        """Print summary of created data."""
        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write('RESUMEN DE DATOS TRANSACCIONALES')
        self.stdout.write('=' * 60)
        self.stdout.write(f'  Ventas: {Sale.objects.count()}')
        self.stdout.write(f'  Items de venta: {SaleItem.objects.count()}')
        self.stdout.write(f'  Registros de caja: {DailyCashRegister.objects.count()}')
        self.stdout.write(f'  Turnos: {Shift.objects.count()}')
        self.stdout.write(f'  Movimientos de stock: {StockMovement.objects.count()}')
        self.stdout.write(f'  Alertas: {Alert.objects.count()}')
        self.stdout.write('=' * 60)
