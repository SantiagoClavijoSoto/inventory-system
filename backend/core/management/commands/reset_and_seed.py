"""
Management command to reset the database and seed complete demo data.

This command:
1. Clears ALL data except migrations
2. Recreates companies, users, products, etc.
3. Creates 30+ days of transactional data for charts
4. Creates subscriptions for each company

Usage:
    python manage.py reset_and_seed
    python manage.py reset_and_seed --days=60
"""
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction, connection
import random

from apps.companies.models import Company, Subscription
from apps.branches.models import Branch
from apps.users.models import User, Role, Permission
from apps.inventory.models import Category, Product, BranchStock, StockMovement, StockAlert
from apps.employees.models import Employee, Shift
from apps.sales.models import Sale, SaleItem, DailyCashRegister
from apps.suppliers.models import Supplier, PurchaseOrder, PurchaseOrderItem
from apps.alerts.models import Alert, AlertConfiguration, UserAlertPreference


class Command(BaseCommand):
    help = 'Reset database and seed complete demo data with historical transactions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days of historical data (default: 30)',
        )
        parser.add_argument(
            '--superadmin-email',
            type=str,
            default='superadmin@platform.local',
            help='Email for the platform SuperAdmin account',
        )
        parser.add_argument(
            '--skip-confirm',
            action='store_true',
            help='Skip confirmation prompt',
        )

    def handle(self, *args, **options):
        days = options['days']

        if not options['skip_confirm']:
            self.stdout.write(self.style.WARNING(
                '\n⚠️  WARNING: This will DELETE ALL DATA in the database!\n'
            ))
            confirm = input('Type "RESET" to confirm: ')
            if confirm != 'RESET':
                self.stdout.write(self.style.ERROR('Aborted.'))
                return

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('RESETTING DATABASE')
        self.stdout.write('=' * 60)

        # Step 1: Clear all data
        self._clear_all_data()

        # Step 2: Recreate base data (companies, users, products)
        self.stdout.write('\n📦 Creating base data...')
        call_command('seed_companies', superadmin_email=options['superadmin_email'])

        # Step 3: Create subscriptions
        self.stdout.write('\n💳 Creating subscriptions...')
        self._create_subscriptions()

        # Step 4: Create transactional data
        self.stdout.write(f'\n📊 Creating {days} days of transactional data...')
        call_command('seed_transactions', days=days)

        # Step 5: Create additional varied data for better charts
        self.stdout.write('\n📈 Enhancing data for visualizations...')
        self._enhance_sales_data(days)
        self._create_purchase_orders()

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('✅ DATABASE RESET AND SEEDED SUCCESSFULLY!'))
        self.stdout.write('=' * 60)
        self._print_credentials()
        self._print_summary()

    def _clear_all_data(self):
        """Clear all data from the database."""
        self.stdout.write('🗑️  Clearing all data...')

        with transaction.atomic():
            # First, remove protected FK references by setting owner to None
            Company.objects.update(owner=None)
            self.stdout.write('  ✓ Cleared company owner references')

            # Delete tables that reference User (in correct order)
            # These have FK to User so must be deleted before User
            tables_with_user_fk = [
                UserAlertPreference,
                AlertConfiguration,
                Alert,
                StockAlert,
                SaleItem,
                Sale,
                DailyCashRegister,
                Shift,
                Employee,
                PurchaseOrderItem,
                PurchaseOrder,
                StockMovement,
            ]

            for model in tables_with_user_fk:
                count = model.objects.count()
                if count > 0:
                    model.objects.all().delete()
                    self.stdout.write(f'  ✓ {model.__name__}: {count} records deleted')

            # Now delete remaining tables
            remaining_tables = [
                Supplier,
                BranchStock,
                Product,
                Category,
                User,
                Role,
                Permission,
                Subscription,
                Branch,
                Company,
            ]

            for model in remaining_tables:
                count = model.objects.count()
                if count > 0:
                    model.objects.all().delete()
                    self.stdout.write(f'  ✓ {model.__name__}: {count} records deleted')

        self.stdout.write(self.style.SUCCESS('  All data cleared.'))

    def _create_subscriptions(self):
        """Create subscriptions for all companies."""
        subscription_configs = {
            'tornillo-feliz': {
                'plan': 'basic',
                'status': 'active',
                'billing_cycle': 'monthly',
                'amount': Decimal('499.00'),
                'days_offset': -45,  # Started 45 days ago
            },
            'moda-elegante': {
                'plan': 'professional',
                'status': 'active',
                'billing_cycle': 'quarterly',
                'amount': Decimal('1299.00'),
                'days_offset': -90,
            },
            'salud-total': {
                'plan': 'enterprise',
                'status': 'active',
                'billing_cycle': 'annual',
                'amount': Decimal('9999.00'),
                'days_offset': -180,
            },
        }

        for slug, config in subscription_configs.items():
            try:
                company = Company.objects.get(slug=slug)
                start_date = date.today() + timedelta(days=config['days_offset'])

                # Calculate next payment based on billing cycle
                if config['billing_cycle'] == 'monthly':
                    next_payment = start_date + timedelta(days=30)
                    while next_payment < date.today():
                        next_payment += timedelta(days=30)
                elif config['billing_cycle'] == 'quarterly':
                    next_payment = start_date + timedelta(days=90)
                    while next_payment < date.today():
                        next_payment += timedelta(days=90)
                else:  # annual
                    next_payment = start_date + timedelta(days=365)

                Subscription.objects.create(
                    company=company,
                    plan=config['plan'],
                    status=config['status'],
                    billing_cycle=config['billing_cycle'],
                    start_date=start_date,
                    next_payment_date=next_payment,
                    amount=config['amount'],
                    currency='MXN',
                )
                self.stdout.write(f'  ✓ {company.name}: {config["plan"]} subscription')
            except Company.DoesNotExist:
                pass

    def _enhance_sales_data(self, days: int):
        """Create additional varied sales for better chart visualization."""
        companies = Company.objects.all()

        for company in companies:
            branches = Branch.objects.filter(company=company, is_active=True)

            for branch in branches:
                # Get cashiers
                cashiers = list(User.objects.filter(
                    company=company,
                    is_active=True,
                    role__role_type__in=['cashier', 'supervisor', 'admin']
                ).filter(allowed_branches=branch)[:3])

                if not cashiers:
                    cashiers = list(User.objects.filter(company=company, is_active=True)[:1])

                if not cashiers:
                    continue

                # Get products with stock
                stocks = list(BranchStock.objects.filter(
                    branch=branch,
                    quantity__gt=5
                ).select_related('product')[:15])

                if not stocks:
                    continue

                # Create varied sales patterns
                for day_offset in range(days, 0, -1):
                    target_date = date.today() - timedelta(days=day_offset)

                    # Vary sales by day of week (weekend = more sales)
                    day_of_week = target_date.weekday()
                    base_sales = 8 if day_of_week >= 5 else 5

                    # Add some randomness
                    num_additional_sales = random.randint(base_sales - 2, base_sales + 4)

                    for _ in range(num_additional_sales):
                        self._create_varied_sale(
                            branch, cashiers, stocks, target_date
                        )

                self.stdout.write(f'  ✓ Enhanced sales for {branch.name}')

    def _create_varied_sale(self, branch, cashiers, stocks, target_date):
        """Create a single varied sale."""
        from django.utils import timezone

        cashier = random.choice(cashiers)
        payment_methods = ['cash', 'cash', 'cash', 'card', 'card', 'transfer']
        payment_method = random.choice(payment_methods)

        # Random time during business hours
        hour = random.randint(9, 20)
        minute = random.randint(0, 59)
        sale_time = timezone.make_aware(
            datetime.combine(target_date, datetime.strptime(f'{hour}:{minute:02d}', '%H:%M').time())
        )

        # Create sale
        sale = Sale(
            branch=branch,
            cashier=cashier,
            payment_method=payment_method,
            status='completed',
        )
        sale.sale_number = sale.generate_sale_number(branch.code)
        sale.save()

        # Update created_at
        Sale.objects.filter(id=sale.id).update(created_at=sale_time)

        # Add 1-4 items
        num_items = random.randint(1, 4)
        selected_stocks = random.sample(stocks, min(num_items, len(stocks)))

        for stock in selected_stocks:
            product = stock.product
            quantity = random.randint(1, 3)

            if quantity > stock.quantity:
                quantity = max(1, int(stock.quantity // 2))

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
            stock.quantity = max(0, stock.quantity - quantity)
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

        # Calculate totals
        sale.calculate_totals()

        # Apply tax
        if branch.tax_rate and branch.tax_rate > 0:
            sale.tax_amount = sale.subtotal * (branch.tax_rate / 100)
            sale.total = sale.subtotal + sale.tax_amount

        # Payment details
        if payment_method == 'cash':
            sale.amount_tendered = sale.total + Decimal(random.choice([0, 5, 10, 20, 50, 100]))
            sale.change_amount = sale.amount_tendered - sale.total
        elif payment_method == 'card':
            sale.payment_reference = f'**** {random.randint(1000, 9999)}'
        else:
            sale.payment_reference = f'REF-{random.randint(100000, 999999)}'

        sale.save()

    def _create_purchase_orders(self):
        """Create purchase orders for suppliers."""
        from django.utils import timezone

        companies = Company.objects.all()
        statuses = ['draft', 'pending', 'approved', 'ordered', 'partial', 'received']

        for company in companies:
            suppliers = Supplier.objects.filter(company=company)
            branches = Branch.objects.filter(company=company, is_active=True)
            products = Product.objects.filter(company=company, is_active=True)
            admin = User.objects.filter(company=company, is_company_admin=True).first()

            if not suppliers.exists() or not products.exists():
                continue

            for supplier in suppliers:
                # Create 2-5 POs per supplier with different statuses
                num_orders = random.randint(2, 5)
                supplier_products = list(products[:10])

                for i in range(num_orders):
                    status = random.choice(statuses)
                    order_date = date.today() - timedelta(days=random.randint(1, 60))
                    expected_date = order_date + timedelta(days=random.randint(5, 15))

                    branch = random.choice(list(branches)) if branches.exists() else None
                    if not branch:
                        continue

                    # Generate unique order number
                    order_number = f"PO-{branch.code}-{order_date.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"

                    po = PurchaseOrder.objects.create(
                        order_number=order_number,
                        supplier=supplier,
                        branch=branch,
                        status=status,
                        order_date=order_date if status != 'draft' else None,
                        expected_date=expected_date if status != 'draft' else None,
                        received_date=order_date + timedelta(days=random.randint(5, 10)) if status == 'received' else None,
                        tax=Decimal('16.00'),
                        notes=f'Orden de compra #{i+1}',
                        created_by=admin,
                        approved_by=admin if status in ['approved', 'ordered', 'partial', 'received'] else None,
                        received_by=admin if status == 'received' else None,
                    )

                    # Add items
                    num_items = random.randint(2, 6)
                    selected_products = random.sample(supplier_products, min(num_items, len(supplier_products)))

                    subtotal = Decimal('0.00')
                    for product in selected_products:
                        qty_ordered = random.randint(10, 50)
                        qty_received = qty_ordered if status == 'received' else (
                            random.randint(0, qty_ordered) if status == 'partial' else 0
                        )

                        item = PurchaseOrderItem.objects.create(
                            purchase_order=po,
                            product=product,
                            quantity_ordered=qty_ordered,
                            quantity_received=qty_received,
                            unit_price=product.cost_price,
                        )
                        subtotal += item.subtotal

                    # Update totals
                    po.subtotal = subtotal
                    po.total = subtotal * Decimal('1.16')  # With tax
                    po.save()

                self.stdout.write(f'  ✓ POs for {supplier.name}')

    def _print_credentials(self):
        """Print login credentials."""
        self.stdout.write('\n📋 CREDENCIALES DE ACCESO')
        self.stdout.write('-' * 40)
        self.stdout.write(self.style.WARNING('Platform SuperAdmin:'))
        self.stdout.write('  Email:    superadmin@platform.local')
        self.stdout.write('  Password: SuperAdmin123!')
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('Company Admins (password: demo123):'))
        self.stdout.write('  Ferretería: admin@tornillofeliz.com')
        self.stdout.write('  Boutique:   admin@modaelegante.com')
        self.stdout.write('  Farmacia:   admin@saludtotal.com')
        self.stdout.write('-' * 40)

    def _print_summary(self):
        """Print summary of created data."""
        self.stdout.write('\n📊 RESUMEN DE DATOS')
        self.stdout.write('-' * 40)
        self.stdout.write(f'  Empresas:           {Company.objects.count()}')
        self.stdout.write(f'  Suscripciones:      {Subscription.objects.count()}')
        self.stdout.write(f'  Sucursales:         {Branch.objects.count()}')
        self.stdout.write(f'  Usuarios:           {User.objects.count()}')
        self.stdout.write(f'  Roles:              {Role.objects.count()}')
        self.stdout.write(f'  Empleados:          {Employee.objects.count()}')
        self.stdout.write(f'  Categorías:         {Category.objects.count()}')
        self.stdout.write(f'  Productos:          {Product.objects.count()}')
        self.stdout.write(f'  Proveedores:        {Supplier.objects.count()}')
        self.stdout.write(f'  Órdenes de compra:  {PurchaseOrder.objects.count()}')
        self.stdout.write(f'  Ventas:             {Sale.objects.count()}')
        self.stdout.write(f'  Items de venta:     {SaleItem.objects.count()}')
        self.stdout.write(f'  Registros de caja:  {DailyCashRegister.objects.count()}')
        self.stdout.write(f'  Turnos:             {Shift.objects.count()}')
        self.stdout.write(f'  Mov. de stock:      {StockMovement.objects.count()}')
        self.stdout.write(f'  Alertas:            {Alert.objects.count()}')
        self.stdout.write('-' * 40)
