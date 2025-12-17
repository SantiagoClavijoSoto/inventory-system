"""
Seed completo para las 3 empresas existentes.
Crea: Permissions, Roles, Subscriptions, Branches, Categories, Products,
      Suppliers, Employees, Ventas (01/12/2025 - 17/12/2025)
"""
import random
from datetime import date, datetime, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.users.models import User, Role, Permission
from apps.companies.models import Company, Subscription
from apps.branches.models import Branch
from apps.employees.models import Employee, Shift
from apps.inventory.models import Category, Product, BranchStock, StockMovement
from apps.suppliers.models import Supplier, PurchaseOrder, PurchaseOrderItem
from apps.sales.models import Sale, SaleItem, DailyCashRegister


class Command(BaseCommand):
    help = 'Seed full data for existing companies'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-confirm',
            action='store_true',
            help='Skip confirmation prompt',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n=== SEED FULL DATA ===\n'))

        companies = Company.objects.all()
        if companies.count() != 3:
            self.stdout.write(self.style.ERROR(f'Expected 3 companies, found {companies.count()}'))
            return

        self.stdout.write(f'Companies found: {[c.name for c in companies]}')

        if not options['skip_confirm']:
            confirm = input('\nProceed with seeding? Type "yes": ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Cancelled.'))
                return

        try:
            with transaction.atomic():
                self._seed_all(companies)
            self.stdout.write(self.style.SUCCESS('\n=== SEED COMPLETED ===\n'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nERROR: {str(e)}'))
            raise

    def _seed_all(self, companies):
        # 1. Permissions
        self.stdout.write(self.style.WARNING('\n1. Creating Permissions...'))
        permissions = self._create_permissions()
        self.stdout.write(f'   Created {len(permissions)} permissions')

        # 2. Roles por company
        self.stdout.write(self.style.WARNING('\n2. Creating Roles...'))
        roles_by_company = {}
        for company in companies:
            roles_by_company[company.id] = self._create_roles(company, permissions)
        self.stdout.write(f'   Created roles for {len(companies)} companies')

        # 3. Subscriptions
        self.stdout.write(self.style.WARNING('\n3. Creating Subscriptions...'))
        for company in companies:
            self._create_subscription(company)
        self.stdout.write(f'   Created {companies.count()} subscriptions')

        # 4. Branches
        self.stdout.write(self.style.WARNING('\n4. Creating Branches...'))
        branches_by_company = {}
        for company in companies:
            branches_by_company[company.id] = self._create_branches(company)
        total_branches = sum(len(b) for b in branches_by_company.values())
        self.stdout.write(f'   Created {total_branches} branches')

        # 5. Categories y Products
        self.stdout.write(self.style.WARNING('\n5. Creating Categories & Products...'))
        products_by_company = {}
        for company in companies:
            products_by_company[company.id] = self._create_inventory(company, branches_by_company[company.id])
        total_products = sum(len(p) for p in products_by_company.values())
        self.stdout.write(f'   Created {total_products} products')

        # 6. Suppliers
        self.stdout.write(self.style.WARNING('\n6. Creating Suppliers...'))
        for company in companies:
            self._create_suppliers(company)

        # 7. Employees (vincular admins existentes + crear nuevos users)
        self.stdout.write(self.style.WARNING('\n7. Creating Employees...'))
        for company in companies:
            self._create_employees(company, branches_by_company[company.id], roles_by_company[company.id])

        # 8. Ventas 01/12/2025 - 17/12/2025
        self.stdout.write(self.style.WARNING('\n8. Generating Sales (01/12 - 17/12/2025)...'))
        for company in companies:
            self._generate_sales(
                company,
                branches_by_company[company.id],
                products_by_company[company.id]
            )

    def _create_permissions(self):
        """Crear permisos base del sistema"""
        modules = ['inventory', 'sales', 'employees', 'reports', 'settings', 'suppliers']
        actions = ['view', 'create', 'edit', 'delete']

        permissions = []
        for module in modules:
            for action in actions:
                perm, _ = Permission.objects.get_or_create(
                    code=f'{module}.{action}',
                    defaults={
                        'name': f'{action.title()} {module.title()}',
                        'module': module,
                        'action': action,
                    }
                )
                permissions.append(perm)

        # Permisos especiales
        special = [
            ('pos.access', 'Access POS', 'sales', 'view'),
            ('reports.export', 'Export Reports', 'reports', 'view'),
            ('cash_register.manage', 'Manage Cash Register', 'sales', 'edit'),
        ]
        for code, name, module, action in special:
            perm, _ = Permission.objects.get_or_create(
                code=code,
                defaults={'name': name, 'module': module, 'action': action}
            )
            permissions.append(perm)

        return permissions

    def _create_roles(self, company, permissions):
        """Crear roles para una empresa"""
        roles_config = [
            ('admin', 'Administrador', permissions),  # Todos los permisos
            ('supervisor', 'Supervisor', [p for p in permissions if p.action in ['view', 'edit']]),
            ('cashier', 'Cajero', [p for p in permissions if p.module in ['sales'] or p.code == 'pos.access']),
            ('warehouse', 'Almacenista', [p for p in permissions if p.module in ['inventory', 'suppliers']]),
            ('viewer', 'Solo Lectura', [p for p in permissions if p.action == 'view']),
        ]

        roles = {}
        for role_type, name, perms in roles_config:
            role, _ = Role.objects.get_or_create(
                company=company,
                name=name,
                defaults={'role_type': role_type, 'is_active': True}
            )
            role.permissions.set(perms)
            roles[role_type] = role

        return roles

    def _create_subscription(self, company):
        """Crear subscription para empresa"""
        plans = {
            'Ferretería': ('basic', Decimal('299.00')),
            'Boutique': ('professional', Decimal('599.00')),
            'Farmacia': ('enterprise', Decimal('999.00')),
        }

        plan, amount = ('professional', Decimal('499.00'))
        for key, (p, a) in plans.items():
            if key in company.name:
                plan, amount = p, a
                break

        Subscription.objects.get_or_create(
            company=company,
            defaults={
                'plan': plan,
                'status': 'active',
                'start_date': date(2025, 1, 1),
                'billing_cycle': 'monthly',
                'amount': amount,
                'currency': 'COP',
            }
        )

    def _create_branches(self, company):
        """Crear sucursales según tipo de empresa"""
        branches_config = {
            'Ferretería': [
                ('SUC-001', 'Sucursal Centro', True, 'Calle 45 #23-12', 'Bogotá'),
            ],
            'Boutique': [
                ('SUC-001', 'Tienda Centro', True, 'Carrera 7 #72-15', 'Bogotá'),
                ('SUC-002', 'Tienda Norte', False, 'Calle 140 #11-20', 'Bogotá'),
            ],
            'Farmacia': [
                ('SUC-001', 'Sede Principal', True, 'Avenida 68 #13-45', 'Bogotá'),
                ('SUC-002', 'Sede Norte', False, 'Calle 170 #45-30', 'Bogotá'),
                ('SUC-003', 'Sede Sur', False, 'Autopista Sur #65-10', 'Bogotá'),
            ],
        }

        config = [('SUC-001', 'Sucursal Principal', True, 'Calle Principal', 'Bogotá')]
        for key, cfg in branches_config.items():
            if key in company.name:
                config = cfg
                break

        branches = []
        for code, name, is_main, address, city in config:
            branch, _ = Branch.objects.get_or_create(
                company=company,
                code=code,
                defaults={
                    'name': name,
                    'is_main': is_main,
                    'address': address,
                    'city': city,
                    'country': 'Colombia',
                    'currency': 'COP',
                    'currency_symbol': '$',
                    'tax_rate': Decimal('19.00'),
                    'is_active': True,
                }
            )
            branches.append(branch)

        return branches

    def _create_inventory(self, company, branches):
        """Crear categorías y productos según tipo de empresa"""
        inventory_config = {
            'Ferretería': {
                'categories': ['Herramientas', 'Tornillería', 'Pinturas', 'Plomería', 'Electricidad'],
                'products': [
                    ('Martillo', 'Herramientas', 15000, 28000, 'HER-001'),
                    ('Destornillador Phillips', 'Herramientas', 5000, 12000, 'HER-002'),
                    ('Taladro Inalámbrico', 'Herramientas', 185000, 320000, 'HER-003'),
                    ('Sierra Circular', 'Herramientas', 250000, 450000, 'HER-004'),
                    ('Tornillos x100', 'Tornillería', 8000, 15000, 'TOR-001'),
                    ('Clavos x500', 'Tornillería', 12000, 22000, 'TOR-002'),
                    ('Pernos M10 x50', 'Tornillería', 18000, 32000, 'TOR-003'),
                    ('Pintura Blanca 1gal', 'Pinturas', 45000, 75000, 'PIN-001'),
                    ('Pintura Vinilo 1gal', 'Pinturas', 38000, 65000, 'PIN-002'),
                    ('Brocha 3"', 'Pinturas', 8000, 15000, 'PIN-003'),
                    ('Tubo PVC 1/2"', 'Plomería', 4500, 8500, 'PLO-001'),
                    ('Llave de Paso', 'Plomería', 12000, 22000, 'PLO-002'),
                    ('Cable #12 x metro', 'Electricidad', 2500, 4500, 'ELE-001'),
                    ('Tomacorriente Doble', 'Electricidad', 8000, 15000, 'ELE-002'),
                    ('Interruptor Sencillo', 'Electricidad', 5000, 9500, 'ELE-003'),
                ]
            },
            'Boutique': {
                'categories': ['Damas', 'Caballeros', 'Accesorios', 'Calzado'],
                'products': [
                    ('Blusa Elegante', 'Damas', 35000, 75000, 'DAM-001'),
                    ('Vestido Casual', 'Damas', 55000, 120000, 'DAM-002'),
                    ('Pantalón Dama', 'Damas', 45000, 95000, 'DAM-003'),
                    ('Falda Midi', 'Damas', 40000, 85000, 'DAM-004'),
                    ('Camisa Formal', 'Caballeros', 42000, 89000, 'CAB-001'),
                    ('Pantalón Casual', 'Caballeros', 48000, 98000, 'CAB-002'),
                    ('Saco Sport', 'Caballeros', 120000, 250000, 'CAB-003'),
                    ('Corbata Seda', 'Caballeros', 25000, 55000, 'CAB-004'),
                    ('Bolso Cuero', 'Accesorios', 85000, 180000, 'ACC-001'),
                    ('Cinturón Cuero', 'Accesorios', 35000, 75000, 'ACC-002'),
                    ('Bufanda Lana', 'Accesorios', 28000, 60000, 'ACC-003'),
                    ('Zapatos Tacón', 'Calzado', 95000, 195000, 'CAL-001'),
                    ('Mocasines', 'Calzado', 110000, 220000, 'CAL-002'),
                    ('Botas Dama', 'Calzado', 130000, 280000, 'CAL-003'),
                ]
            },
            'Farmacia': {
                'categories': ['Medicamentos', 'Cuidado Personal', 'Vitaminas', 'Primeros Auxilios', 'Bebé'],
                'products': [
                    ('Acetaminofén 500mg x20', 'Medicamentos', 3500, 6500, 'MED-001'),
                    ('Ibuprofeno 400mg x20', 'Medicamentos', 4500, 8500, 'MED-002'),
                    ('Omeprazol 20mg x14', 'Medicamentos', 8000, 15000, 'MED-003'),
                    ('Loratadina 10mg x10', 'Medicamentos', 5500, 10500, 'MED-004'),
                    ('Amoxicilina 500mg x21', 'Medicamentos', 12000, 22000, 'MED-005'),
                    ('Crema Dental 150ml', 'Cuidado Personal', 8500, 15000, 'PER-001'),
                    ('Shampoo 400ml', 'Cuidado Personal', 12000, 22000, 'PER-002'),
                    ('Jabón Líquido 500ml', 'Cuidado Personal', 9500, 18000, 'PER-003'),
                    ('Vitamina C 500mg x60', 'Vitaminas', 18000, 35000, 'VIT-001'),
                    ('Multivitamínico x30', 'Vitaminas', 25000, 48000, 'VIT-002'),
                    ('Omega 3 x60', 'Vitaminas', 32000, 62000, 'VIT-003'),
                    ('Alcohol 350ml', 'Primeros Auxilios', 5500, 9500, 'PRI-001'),
                    ('Gasas Estériles x10', 'Primeros Auxilios', 4500, 8500, 'PRI-002'),
                    ('Curitas x100', 'Primeros Auxilios', 8000, 15000, 'PRI-003'),
                    ('Pañales RN x30', 'Bebé', 28000, 48000, 'BEB-001'),
                    ('Leche Fórmula 400g', 'Bebé', 45000, 75000, 'BEB-002'),
                ]
            },
        }

        config = inventory_config.get('Ferretería', inventory_config['Ferretería'])
        for key, cfg in inventory_config.items():
            if key in company.name:
                config = cfg
                break

        # Crear categorías
        categories = {}
        for cat_name in config['categories']:
            cat, _ = Category.objects.get_or_create(
                company=company,
                name=cat_name,
                defaults={'is_active': True}
            )
            categories[cat_name] = cat

        # Crear productos con stock variado
        products = []
        for name, cat_name, cost, sale, sku in config['products']:
            full_sku = f'{company.slug[:3].upper()}-{sku}'
            product, created = Product.objects.get_or_create(
                sku=full_sku,
                defaults={
                    'company': company,
                    'name': name,
                    'category': categories[cat_name],
                    'cost_price': Decimal(str(cost)),
                    'sale_price': Decimal(str(sale)),
                    'min_stock': random.randint(5, 15),
                    'max_stock': random.randint(80, 150),
                    'is_active': True,
                    'is_sellable': True,
                }
            )
            products.append(product)

            if created:
                # Crear stock variado por branch
                for branch in branches:
                    # Variedad: 20% bajo stock, 30% medio, 50% alto
                    rand = random.random()
                    if rand < 0.2:
                        qty = random.randint(0, 8)  # Bajo o sin stock
                    elif rand < 0.5:
                        qty = random.randint(10, 30)  # Medio
                    else:
                        qty = random.randint(35, 100)  # Alto

                    BranchStock.objects.get_or_create(
                        product=product,
                        branch=branch,
                        defaults={'quantity': qty}
                    )

        return products

    def _create_suppliers(self, company):
        """Crear proveedores según tipo de empresa"""
        suppliers_config = {
            'Ferretería': [
                ('PROV-001', 'Truper Colombia', 'Luis García', '601-555-1234'),
                ('PROV-002', 'Pintuco S.A.', 'Ana Rodríguez', '601-555-5678'),
            ],
            'Boutique': [
                ('PROV-001', 'Textiles Premium', 'Carlos López', '601-555-2345'),
                ('PROV-002', 'Calzado Fino', 'María Santos', '601-555-6789'),
                ('PROV-003', 'Accesorios Elegantes', 'Pedro Ruiz', '601-555-3456'),
            ],
            'Farmacia': [
                ('PROV-001', 'Laboratorios Genfar', 'Dr. Martínez', '601-555-4567'),
                ('PROV-002', 'Droguería La Rebaja', 'Sandra Pérez', '601-555-7890'),
                ('PROV-003', 'Distribuidora Coopidrogas', 'Juan Vargas', '601-555-8901'),
            ],
        }

        config = suppliers_config.get('Ferretería', [])
        for key, cfg in suppliers_config.items():
            if key in company.name:
                config = cfg
                break

        for code, name, contact, phone in config:
            Supplier.objects.get_or_create(
                company=company,
                code=code,
                defaults={
                    'name': name,
                    'contact_name': contact,
                    'phone': phone,
                    'city': 'Bogotá',
                    'country': 'Colombia',
                    'payment_terms': random.choice([15, 30, 45]),
                    'is_active': True,
                }
            )

    def _create_employees(self, company, branches, roles):
        """Crear empleados para los admins existentes y nuevos usuarios"""
        main_branch = branches[0]

        # Vincular admins existentes de esta company
        admins = User.objects.filter(company=company, is_company_admin=True)
        for i, admin in enumerate(admins):
            admin.role = roles.get('admin')
            admin.default_branch = main_branch
            admin.save()
            admin.allowed_branches.set(branches)

            # Crear Employee si no existe
            if not hasattr(admin, 'employee'):
                Employee.objects.create(
                    user=admin,
                    employee_code=f'{company.slug[:3].upper()}-ADM-{i+1:03d}',
                    branch=main_branch,
                    position='Administrador',
                    hire_date=date(2024, 1, 1),
                    salary=Decimal('5000000'),
                    status='active',
                )

        # Crear usuarios adicionales por branch
        positions = [
            ('cashier', 'Cajero', Decimal('1800000')),
            ('warehouse', 'Almacenista', Decimal('2000000')),
        ]

        user_counter = 1
        for branch in branches:
            for role_type, position, salary in positions:
                email = f'{role_type}{user_counter}@{company.slug}.com'
                if User.objects.filter(email=email).exists():
                    user_counter += 1
                    continue

                user = User.objects.create_user(
                    email=email,
                    password='Demo1234',
                    first_name=random.choice(['Juan', 'María', 'Carlos', 'Ana', 'Pedro', 'Laura']),
                    last_name=random.choice(['García', 'López', 'Martínez', 'Rodríguez', 'Hernández']),
                    company=company,
                    role=roles.get(role_type),
                    default_branch=branch,
                )
                user.allowed_branches.add(branch)

                Employee.objects.create(
                    user=user,
                    employee_code=f'{company.slug[:3].upper()}-EMP-{user_counter:03d}',
                    branch=branch,
                    position=position,
                    hire_date=date(2024, 6, 1),
                    salary=salary,
                    status='active',
                )
                user_counter += 1

    def _generate_sales(self, company, branches, products):
        """Generar ventas del 01/12/2025 al 17/12/2025"""
        start_date = date(2025, 12, 1)
        end_date = date(2025, 12, 17)

        # Obtener cashiers de la empresa
        cashiers = list(User.objects.filter(
            company=company,
            role__role_type__in=['admin', 'cashier']
        ))
        if not cashiers:
            self.stdout.write(f'   No cashiers for {company.name}, skipping sales')
            return

        # Patrones de venta por día de semana
        sales_pattern = {
            0: (3, 6),   # Lunes
            1: (4, 7),   # Martes
            2: (3, 6),   # Miércoles
            3: (5, 8),   # Jueves
            4: (5, 9),   # Viernes
            5: (8, 14),  # Sábado
            6: (6, 10),  # Domingo
        }

        sale_counter = 1
        total_sales = 0
        current_date = start_date

        while current_date <= end_date:
            for branch in branches:
                # Número de ventas del día
                day_of_week = current_date.weekday()
                min_sales, max_sales = sales_pattern[day_of_week]

                # Día especial: 8 de diciembre
                if current_date.day == 8:
                    min_sales, max_sales = max_sales, max_sales + 5

                num_sales = random.randint(min_sales, max_sales)

                # Crear caja del día
                cashier = random.choice(cashiers)
                cash_register, _ = DailyCashRegister.objects.get_or_create(
                    branch=branch,
                    date=current_date,
                    defaults={
                        'opened_by': cashier,
                        'opened_at': timezone.make_aware(
                            datetime.combine(current_date, datetime.min.time().replace(hour=8))
                        ),
                        'opening_amount': Decimal('200000'),
                        'is_closed': current_date < end_date,
                    }
                )

                # Generar ventas del día
                for _ in range(num_sales):
                    sale = self._create_single_sale(
                        branch, products, cashiers, current_date, sale_counter
                    )
                    if sale:
                        sale_counter += 1
                        total_sales += 1

                        # Actualizar caja
                        if sale.payment_method == 'cash':
                            cash_register.cash_sales_total += sale.total
                        elif sale.payment_method == 'card':
                            cash_register.card_sales_total += sale.total
                        else:
                            cash_register.transfer_sales_total += sale.total

                # Cerrar caja
                if current_date < end_date:
                    cash_register.closing_amount = (
                        cash_register.opening_amount + cash_register.cash_sales_total
                    )
                    cash_register.expected_amount = cash_register.closing_amount
                    cash_register.closed_at = timezone.make_aware(
                        datetime.combine(current_date, datetime.min.time().replace(hour=20))
                    )
                    cash_register.closed_by = cashier
                    cash_register.save()

            current_date += timedelta(days=1)

        self.stdout.write(f'   {company.name}: {total_sales} sales generated')

    def _create_single_sale(self, branch, products, cashiers, sale_date, counter):
        """Crear una venta individual"""
        # Filtrar productos con stock
        available = []
        for product in products:
            try:
                stock = BranchStock.objects.get(product=product, branch=branch)
                if stock.quantity > 0:
                    available.append((product, stock))
            except BranchStock.DoesNotExist:
                pass

        if not available:
            return None

        # Seleccionar 1-4 productos
        num_items = min(random.randint(1, 4), len(available))
        selected = random.sample(available, num_items)

        # Crear venta
        cashier = random.choice(cashiers)
        payment = random.choices(['cash', 'card', 'transfer'], weights=[50, 35, 15])[0]

        # Hora aleatoria entre 8 AM y 8 PM
        hour = random.randint(8, 20)
        minute = random.randint(0, 59)
        sale_datetime = timezone.make_aware(
            datetime.combine(sale_date, datetime.min.time().replace(hour=hour, minute=minute))
        )

        sale = Sale.objects.create(
            sale_number=f'V-{sale_date.strftime("%Y%m%d")}-{counter:04d}',
            branch=branch,
            cashier=cashier,
            payment_method=payment,
            status='completed',
            created_at=sale_datetime,
        )

        subtotal = Decimal('0')

        for product, stock in selected:
            qty = min(random.randint(1, 3), stock.quantity)
            if qty <= 0:
                continue

            item_subtotal = product.sale_price * qty

            SaleItem.objects.create(
                sale=sale,
                product=product,
                product_name=product.name,
                product_sku=product.sku,
                quantity=qty,
                unit_price=product.sale_price,
                cost_price=product.cost_price,
                subtotal=item_subtotal,
            )

            # Actualizar stock
            stock.quantity -= qty
            stock.save()

            # Movimiento de stock
            StockMovement.objects.create(
                product=product,
                branch=branch,
                movement_type='sale',
                quantity=-qty,
                previous_quantity=stock.quantity + qty,
                new_quantity=stock.quantity,
                reference=sale.sale_number,
                created_by=cashier,
            )

            subtotal += item_subtotal

        # Calcular totales
        tax_rate = branch.tax_rate / 100
        tax = subtotal * tax_rate
        total = subtotal + tax

        sale.subtotal = subtotal
        sale.tax_amount = tax
        sale.total = total
        sale.amount_tendered = total if payment != 'cash' else total + Decimal(random.randint(0, 50) * 1000)
        sale.change_amount = max(Decimal('0'), sale.amount_tendered - total)
        sale.save()

        return sale
