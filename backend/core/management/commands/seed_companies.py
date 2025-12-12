"""
Management command to seed multi-tenant demo data.

Creates:
- Platform SuperAdmin
- 3 demo companies with isolated data:
  1. Ferretería "El Tornillo Feliz" (PEQUEÑA) - 1 branch, 3 users
  2. Boutique "Moda Elegante" (MEDIANA) - 2 branches, 6 users
  3. Farmacia "Salud Total" (GRANDE) - 4 branches, 12 users

Each company has its own:
- Users with proper roles
- Employees linked to User accounts
- Branches
- Products and Categories
- Suppliers
- Stock data
"""
from decimal import Decimal
from datetime import date
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.companies.models import Company
from apps.branches.models import Branch
from apps.users.models import User, Role, Permission
from apps.inventory.models import Category, Product, BranchStock
from apps.suppliers.models import Supplier
from apps.employees.models import Employee


class Command(BaseCommand):
    help = 'Seeds the database with multi-tenant demo data (3 companies)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing demo data before seeding',
        )
        parser.add_argument(
            '--superadmin-email',
            type=str,
            default='superadmin@platform.local',
            help='Email for the platform SuperAdmin account',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing demo data...')
            self._clear_demo_data()

        self.stdout.write('Creating multi-tenant demo data...')

        with transaction.atomic():
            # Create default permissions and roles first
            Permission.create_default_permissions()
            Role.create_default_roles()

            # Create SuperAdmin
            superadmin = self._create_superadmin(options['superadmin_email'])

            # Create the 3 demo companies
            ferreteria = self._create_ferreteria()
            boutique = self._create_boutique()
            farmacia = self._create_farmacia()

        self.stdout.write(self.style.SUCCESS('\nSuccessfully created multi-tenant demo data!'))
        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write('CREDENTIALS')
        self.stdout.write('=' * 60)
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('Platform SuperAdmin:'))
        self.stdout.write(f'  Email:    {options["superadmin_email"]}')
        self.stdout.write(f'  Password: SuperAdmin123!')
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('Company Admins (password: demo123):'))
        self.stdout.write(f'  Ferretería: admin@tornillofeliz.com')
        self.stdout.write(f'  Boutique:   admin@modaelegante.com')
        self.stdout.write(f'  Farmacia:   admin@saludtotal.com')
        self.stdout.write('')
        self.stdout.write('=' * 60)

    def _clear_demo_data(self):
        """Remove demo companies and all associated data (cascades)."""
        demo_slugs = ['tornillo-feliz', 'moda-elegante', 'salud-total']

        # Delete companies (will cascade to all related data)
        Company.objects.filter(slug__in=demo_slugs).delete()

        # Delete SuperAdmin
        User.objects.filter(is_superuser=True, email__contains='@platform.local').delete()

        # Clean up any orphaned demo data
        User.objects.filter(email__endswith='@tornillofeliz.com').delete()
        User.objects.filter(email__endswith='@modaelegante.com').delete()
        User.objects.filter(email__endswith='@saludtotal.com').delete()

        self.stdout.write('  Demo data cleared.')

    def _create_superadmin(self, email: str) -> User:
        """Create platform SuperAdmin (no company, sees everything)."""
        self.stdout.write('  Creating Platform SuperAdmin...')

        superadmin, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': 'Super',
                'last_name': 'Admin',
                'is_superuser': True,
                'is_staff': True,
                'company': None,  # Platform admin has no company
            }
        )

        if created:
            superadmin.set_password('SuperAdmin123!')
            superadmin.save()

        return superadmin

    def _create_user_with_employee(
        self,
        company: Company,
        branch: Branch,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        role_type: str,
        is_company_admin: bool,
        position: str,
        employee_code: str,
        hire_date: date,
        employment_type: str = 'full_time',
        salary: Decimal = Decimal('0.00'),
    ) -> tuple[User, Employee]:
        """Create a user with linked employee profile."""
        # Create User
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            company=company,
            is_company_admin=is_company_admin,
            default_branch=branch,
        )

        # Assign role
        role = Role.objects.filter(role_type=role_type).first()
        if role:
            user.role = role
            user.save()

        user.allowed_branches.add(branch)

        # Create Employee linked to User
        employee = Employee.objects.create(
            user=user,
            employee_code=employee_code,
            position=position,
            department='',
            hire_date=hire_date,
            branch=branch,
            salary=salary,
            hourly_rate=Decimal('0.00'),
            employment_type=employment_type,
            status='active',
        )

        return user, employee

    def _create_ferreteria(self) -> Company:
        """Create Ferretería El Tornillo Feliz (small company - 1 branch)."""
        self.stdout.write('  Creating Ferretería El Tornillo Feliz...')

        # Create Company
        company = Company.objects.create(
            name='Ferretería El Tornillo Feliz',
            slug='tornillo-feliz',
            legal_name='El Tornillo Feliz S.A. de C.V.',
            tax_id='TFE123456ABC',
            email='contacto@tornillofeliz.com',
            phone='55 1234 5678',
            address='Av. Insurgentes Sur 1234, CDMX',
            plan='basic',
            max_branches=1,
            max_users=5,
            max_products=100,
            primary_color='#2563eb',
            secondary_color='#f97316',
            is_active=True,
        )

        # Create Branch
        branch = Branch.objects.create(
            company=company,
            name='Matriz Centro',
            code='FERR-MAT',
            store_name='El Tornillo Feliz',
            address='Av. Insurgentes Sur 1234',
            city='Ciudad de México',
            state='CDMX',
            postal_code='03100',
            country='México',
            phone='55 1234 5678',
            email='matriz@tornillofeliz.com',
            manager_name='Roberto Hernández',
            is_active=True,
            is_main=True,
            opening_time='08:00',
            closing_time='20:00',
            primary_color='#2563eb',
            secondary_color='#64748b',
            accent_color='#f97316',
            tax_rate=Decimal('16.00'),
            currency='MXN',
            currency_symbol='$',
            receipt_header='FERRETERÍA EL TORNILLO FELIZ\nAv. Insurgentes Sur 1234\nTel: 55 1234 5678',
            receipt_footer='¡Gracias por su compra!',
        )

        # Set company owner after creating first admin
        admin_user, admin_emp = self._create_user_with_employee(
            company=company,
            branch=branch,
            email='admin@tornillofeliz.com',
            password='demo123',
            first_name='Roberto',
            last_name='Hernández',
            role_type='admin',
            is_company_admin=True,
            position='Gerente General',
            employee_code='FERR-EMP-001',
            hire_date=date(2020, 1, 1),
            salary=Decimal('35000.00'),
        )
        company.owner = admin_user
        company.save()

        # Create Cajero
        self._create_user_with_employee(
            company=company,
            branch=branch,
            email='cajero@tornillofeliz.com',
            password='demo123',
            first_name='Carlos',
            last_name='Mendoza',
            role_type='cashier',
            is_company_admin=False,
            position='Cajero',
            employee_code='FERR-EMP-002',
            hire_date=date(2023, 1, 15),
            salary=Decimal('12000.00'),
        )

        # Create Almacenista
        self._create_user_with_employee(
            company=company,
            branch=branch,
            email='almacen@tornillofeliz.com',
            password='demo123',
            first_name='Ana',
            last_name='López',
            role_type='warehouse',
            is_company_admin=False,
            position='Almacenista',
            employee_code='FERR-EMP-003',
            hire_date=date(2023, 6, 1),
            salary=Decimal('11000.00'),
        )

        # Create Categories (with company)
        herramientas = Category.objects.create(company=company, name='Herramientas', description='Herramientas manuales y eléctricas')
        electricidad = Category.objects.create(company=company, name='Electricidad', description='Material eléctrico')
        plomeria = Category.objects.create(company=company, name='Plomería', description='Material de plomería')
        pinturas = Category.objects.create(company=company, name='Pinturas', description='Pinturas y accesorios')

        # Create Products
        products_data = [
            {'name': 'Martillo de carpintero 16oz', 'sku': 'FERR-MART-001', 'category': herramientas, 'cost': 89, 'price': 149},
            {'name': 'Desarmador Phillips #2', 'sku': 'FERR-DESA-001', 'category': herramientas, 'cost': 25, 'price': 45},
            {'name': 'Pinzas de electricista', 'sku': 'FERR-PINZ-001', 'category': herramientas, 'cost': 65, 'price': 110},
            {'name': 'Llave inglesa 10"', 'sku': 'FERR-LLAV-001', 'category': herramientas, 'cost': 120, 'price': 199},
            {'name': 'Taladro inalámbrico 12V', 'sku': 'FERR-TALA-001', 'category': herramientas, 'cost': 650, 'price': 1099},
            {'name': 'Cable calibre 12 (metro)', 'sku': 'FERR-CABL-001', 'category': electricidad, 'cost': 12, 'price': 22},
            {'name': 'Foco LED 9W', 'sku': 'FERR-FOCO-001', 'category': electricidad, 'cost': 35, 'price': 59},
            {'name': 'Apagador sencillo', 'sku': 'FERR-APAG-001', 'category': electricidad, 'cost': 18, 'price': 35},
            {'name': 'Tubo PVC 2" (metro)', 'sku': 'FERR-TUBO-001', 'category': plomeria, 'cost': 45, 'price': 75},
            {'name': 'Llave de paso 1/2"', 'sku': 'FERR-LLAVE-001', 'category': plomeria, 'cost': 85, 'price': 145},
            {'name': 'Cinta teflón', 'sku': 'FERR-TEFL-001', 'category': plomeria, 'cost': 8, 'price': 15},
            {'name': 'Pintura vinílica blanca 4L', 'sku': 'FERR-PINT-001', 'category': pinturas, 'cost': 280, 'price': 450},
            {'name': 'Brocha 3"', 'sku': 'FERR-BROC-001', 'category': pinturas, 'cost': 35, 'price': 65},
            {'name': 'Rodillo 9"', 'sku': 'FERR-RODI-001', 'category': pinturas, 'cost': 55, 'price': 95},
        ]

        for p in products_data:
            product = Product.objects.create(
                company=company,
                name=p['name'],
                sku=p['sku'],
                category=p['category'],
                cost_price=Decimal(str(p['cost'])),
                sale_price=Decimal(str(p['price'])),
                unit='unit',
                min_stock=10,
                max_stock=100,
                is_active=True,
            )
            BranchStock.objects.create(branch=branch, product=product, quantity=50)

        # Create Suppliers
        Supplier.objects.create(
            company=company,
            name='Truper S.A. de C.V.',
            code='FERR-TRUP-01',
            contact_name='Juan Pérez',
            email='ventas@truper.com',
            phone='800 123 4567',
            city='Toluca',
            state='Estado de México',
            payment_terms=30,
            credit_limit=Decimal('50000.00'),
        )
        Supplier.objects.create(
            company=company,
            name='Volteck Distribución',
            code='FERR-VOLT-01',
            contact_name='María García',
            email='comercial@volteck.com',
            phone='800 234 5678',
            city='Guadalajara',
            state='Jalisco',
            payment_terms=15,
            credit_limit=Decimal('30000.00'),
        )

        return company

    def _create_boutique(self) -> Company:
        """Create Boutique Moda Elegante (medium company - 2 branches)."""
        self.stdout.write('  Creating Boutique Moda Elegante...')

        # Create Company
        company = Company.objects.create(
            name='Boutique Moda Elegante',
            slug='moda-elegante',
            legal_name='Moda Elegante S.A. de C.V.',
            tax_id='MEL987654XYZ',
            email='contacto@modaelegante.com',
            phone='55 5555 6666',
            address='Plaza Satélite, Naucalpan',
            plan='professional',
            max_branches=5,
            max_users=20,
            max_products=500,
            primary_color='#ec4899',
            secondary_color='#a855f7',
            is_active=True,
        )

        # Create Branches
        branch_matriz = Branch.objects.create(
            company=company,
            name='Plaza Satélite (Matriz)',
            code='BOUT-SAT',
            store_name='Moda Elegante',
            address='Centro Comercial Plaza Satélite, Local 234',
            city='Naucalpan',
            state='Estado de México',
            postal_code='53100',
            country='México',
            phone='55 5555 6666',
            email='satelite@modaelegante.com',
            manager_name='Sofía Martínez',
            is_active=True,
            is_main=True,
            opening_time='10:00',
            closing_time='21:00',
            primary_color='#ec4899',
            secondary_color='#6b7280',
            accent_color='#a855f7',
            tax_rate=Decimal('16.00'),
            currency='MXN',
            currency_symbol='$',
            receipt_header='BOUTIQUE MODA ELEGANTE\nPlaza Satélite Local 234',
            receipt_footer='¡Gracias por elegirnos!',
        )

        branch_norte = Branch.objects.create(
            company=company,
            name='Plaza Norte',
            code='BOUT-NOR',
            store_name='Moda Elegante',
            address='Centro Comercial Plaza Norte, Local 112',
            city='Ciudad de México',
            state='CDMX',
            postal_code='07300',
            country='México',
            phone='55 6666 7777',
            email='norte@modaelegante.com',
            manager_name='Laura Vega',
            is_active=True,
            is_main=False,
            opening_time='10:00',
            closing_time='21:00',
            primary_color='#ec4899',
            secondary_color='#6b7280',
            accent_color='#a855f7',
            tax_rate=Decimal('16.00'),
            currency='MXN',
            currency_symbol='$',
            receipt_header='BOUTIQUE MODA ELEGANTE\nPlaza Norte Local 112',
            receipt_footer='¡Gracias por elegirnos!',
        )

        # Create Company Admin
        admin_user, admin_emp = self._create_user_with_employee(
            company=company,
            branch=branch_matriz,
            email='admin@modaelegante.com',
            password='demo123',
            first_name='Sofía',
            last_name='Martínez',
            role_type='admin',
            is_company_admin=True,
            position='Directora General',
            employee_code='BOUT-EMP-001',
            hire_date=date(2019, 6, 1),
            salary=Decimal('55000.00'),
        )
        admin_user.allowed_branches.add(branch_norte)
        company.owner = admin_user
        company.save()

        # Supervisor Matriz
        sup_matriz, _ = self._create_user_with_employee(
            company=company,
            branch=branch_matriz,
            email='supervisor.matriz@modaelegante.com',
            password='demo123',
            first_name='Gabriela',
            last_name='Torres',
            role_type='supervisor',
            is_company_admin=False,
            position='Supervisora de Tienda',
            employee_code='BOUT-EMP-002',
            hire_date=date(2020, 9, 1),
            salary=Decimal('25000.00'),
        )

        # Supervisor Norte
        sup_norte, _ = self._create_user_with_employee(
            company=company,
            branch=branch_norte,
            email='supervisor.norte@modaelegante.com',
            password='demo123',
            first_name='Laura',
            last_name='Vega',
            role_type='supervisor',
            is_company_admin=False,
            position='Supervisora de Tienda',
            employee_code='BOUT-EMP-003',
            hire_date=date(2021, 3, 15),
            salary=Decimal('25000.00'),
        )

        # Cajero Matriz
        self._create_user_with_employee(
            company=company,
            branch=branch_matriz,
            email='cajero.matriz@modaelegante.com',
            password='demo123',
            first_name='Miguel',
            last_name='Ángel',
            role_type='cashier',
            is_company_admin=False,
            position='Cajero',
            employee_code='BOUT-EMP-004',
            hire_date=date(2023, 3, 15),
            salary=Decimal('13000.00'),
        )

        # Cajero Norte
        self._create_user_with_employee(
            company=company,
            branch=branch_norte,
            email='cajero.norte@modaelegante.com',
            password='demo123',
            first_name='Patricia',
            last_name='Vega',
            role_type='cashier',
            is_company_admin=False,
            position='Cajera',
            employee_code='BOUT-EMP-005',
            hire_date=date(2024, 1, 10),
            salary=Decimal('13000.00'),
            employment_type='part_time',
        )

        # Almacenista (all branches)
        almacen_user, _ = self._create_user_with_employee(
            company=company,
            branch=branch_matriz,
            email='almacen@modaelegante.com',
            password='demo123',
            first_name='Ricardo',
            last_name='Luna',
            role_type='warehouse',
            is_company_admin=False,
            position='Jefe de Almacén',
            employee_code='BOUT-EMP-006',
            hire_date=date(2022, 5, 1),
            salary=Decimal('18000.00'),
        )
        almacen_user.allowed_branches.add(branch_norte)

        # Create Categories
        damas = Category.objects.create(company=company, name='Damas', description='Ropa para dama')
        caballeros = Category.objects.create(company=company, name='Caballeros', description='Ropa para caballero')
        accesorios = Category.objects.create(company=company, name='Accesorios', description='Accesorios y complementos')
        calzado = Category.objects.create(company=company, name='Calzado', description='Zapatos y calzado')

        # Create Products
        products_data = [
            {'name': 'Blusa manga corta floral', 'sku': 'BOUT-BLUS-001', 'category': damas, 'cost': 180, 'price': 349},
            {'name': 'Pantalón de vestir negro', 'sku': 'BOUT-PANT-001', 'category': damas, 'cost': 250, 'price': 499},
            {'name': 'Vestido casual verano', 'sku': 'BOUT-VEST-001', 'category': damas, 'cost': 320, 'price': 649},
            {'name': 'Falda midi plisada', 'sku': 'BOUT-FALD-001', 'category': damas, 'cost': 200, 'price': 399},
            {'name': 'Camisa formal azul', 'sku': 'BOUT-CAMI-001', 'category': caballeros, 'cost': 280, 'price': 549},
            {'name': 'Pantalón chino beige', 'sku': 'BOUT-CHIN-001', 'category': caballeros, 'cost': 320, 'price': 599},
            {'name': 'Polo básico blanco', 'sku': 'BOUT-POLO-001', 'category': caballeros, 'cost': 150, 'price': 299},
            {'name': 'Saco sport gris', 'sku': 'BOUT-SACO-001', 'category': caballeros, 'cost': 650, 'price': 1299},
            {'name': 'Bolso tote café', 'sku': 'BOUT-BOLS-001', 'category': accesorios, 'cost': 400, 'price': 799},
            {'name': 'Cinturón piel negro', 'sku': 'BOUT-CINT-001', 'category': accesorios, 'cost': 180, 'price': 349},
            {'name': 'Bufanda lana gris', 'sku': 'BOUT-BUFA-001', 'category': accesorios, 'cost': 120, 'price': 249},
            {'name': 'Zapatillas tacón bajo', 'sku': 'BOUT-ZAPA-001', 'category': calzado, 'cost': 450, 'price': 899},
            {'name': 'Mocasines cuero café', 'sku': 'BOUT-MOCA-001', 'category': calzado, 'cost': 520, 'price': 999},
            {'name': 'Sandalias verano', 'sku': 'BOUT-SAND-001', 'category': calzado, 'cost': 280, 'price': 549},
        ]

        for p in products_data:
            product = Product.objects.create(
                company=company,
                name=p['name'],
                sku=p['sku'],
                category=p['category'],
                cost_price=Decimal(str(p['cost'])),
                sale_price=Decimal(str(p['price'])),
                unit='unit',
                min_stock=5,
                max_stock=50,
                is_active=True,
            )
            # Add stock to both branches
            BranchStock.objects.create(branch=branch_matriz, product=product, quantity=25)
            BranchStock.objects.create(branch=branch_norte, product=product, quantity=20)

        # Create Suppliers
        Supplier.objects.create(
            company=company,
            name='Textiles Premium S.A.',
            code='BOUT-TEXT-01',
            contact_name='Laura Ruiz',
            email='ventas@textilespremium.com',
            phone='33 1234 5678',
            city='Guadalajara',
            state='Jalisco',
            payment_terms=45,
            credit_limit=Decimal('100000.00'),
        )
        Supplier.objects.create(
            company=company,
            name='Calzado Fino de León',
            code='BOUT-CALZ-01',
            contact_name='Pedro Sánchez',
            email='pedidos@calzadofino.com',
            phone='477 123 4567',
            city='León',
            state='Guanajuato',
            payment_terms=30,
            credit_limit=Decimal('80000.00'),
        )
        Supplier.objects.create(
            company=company,
            name='Accesorios de Moda MX',
            code='BOUT-ACCE-01',
            contact_name='Carmen López',
            email='ventas@accesoriosmx.com',
            phone='55 8888 9999',
            city='Ciudad de México',
            state='CDMX',
            payment_terms=30,
            credit_limit=Decimal('50000.00'),
        )

        return company

    def _create_farmacia(self) -> Company:
        """Create Farmacia Salud Total (large company - 4 branches)."""
        self.stdout.write('  Creating Farmacia Salud Total...')

        # Create Company
        company = Company.objects.create(
            name='Farmacia Salud Total',
            slug='salud-total',
            legal_name='Salud Total Farmacias S.A. de C.V.',
            tax_id='STF456789DEF',
            email='atencion@saludtotal.com',
            phone='55 8888 9999',
            address='Corporativo Roma, CDMX',
            plan='enterprise',
            max_branches=20,
            max_users=100,
            max_products=5000,
            primary_color='#22c55e',
            secondary_color='#14b8a6',
            is_active=True,
        )

        # Create 4 Branches
        branches = {}
        branch_data = [
            {'name': 'Roma (Matriz)', 'code': 'FARM-ROM', 'is_main': True, 'manager': 'Dra. Elena Ramírez'},
            {'name': 'Condesa', 'code': 'FARM-CON', 'is_main': False, 'manager': 'Dr. Hugo Silva'},
            {'name': 'Polanco', 'code': 'FARM-POL', 'is_main': False, 'manager': 'Dra. María Flores'},
            {'name': 'Coyoacán', 'code': 'FARM-COY', 'is_main': False, 'manager': 'Dr. Arturo Vega'},
        ]

        for bd in branch_data:
            branches[bd['code']] = Branch.objects.create(
                company=company,
                name=f"Sucursal {bd['name']}",
                code=bd['code'],
                store_name='Salud Total',
                address=f"Colonia {bd['name'].split()[0]}, CDMX",
                city='Ciudad de México',
                state='CDMX',
                postal_code='06700',
                country='México',
                phone='55 8888 9999',
                email=f"{bd['code'].lower().replace('-', '')}@saludtotal.com",
                manager_name=bd['manager'],
                is_active=True,
                is_main=bd['is_main'],
                opening_time='07:00',
                closing_time='22:00',
                primary_color='#22c55e',
                secondary_color='#64748b',
                accent_color='#14b8a6',
                tax_rate=Decimal('0.00'),  # Medicamentos exentos
                currency='MXN',
                currency_symbol='$',
                receipt_header=f'FARMACIA SALUD TOTAL\nSucursal {bd["name"]}',
                receipt_footer='Consulte a su médico.',
            )

        branch_roma = branches['FARM-ROM']
        branch_condesa = branches['FARM-CON']
        branch_polanco = branches['FARM-POL']
        branch_coyoacan = branches['FARM-COY']

        # Create Company Admins (2)
        admin1, _ = self._create_user_with_employee(
            company=company,
            branch=branch_roma,
            email='admin@saludtotal.com',
            password='demo123',
            first_name='Fernando',
            last_name='Reyes',
            role_type='admin',
            is_company_admin=True,
            position='Director General',
            employee_code='FARM-EMP-001',
            hire_date=date(2018, 1, 1),
            salary=Decimal('80000.00'),
        )
        for b in branches.values():
            admin1.allowed_branches.add(b)
        company.owner = admin1
        company.save()

        admin2, _ = self._create_user_with_employee(
            company=company,
            branch=branch_roma,
            email='admin2@saludtotal.com',
            password='demo123',
            first_name='Carolina',
            last_name='Méndez',
            role_type='admin',
            is_company_admin=True,
            position='Subdirectora',
            employee_code='FARM-EMP-002',
            hire_date=date(2019, 3, 1),
            salary=Decimal('65000.00'),
        )
        for b in branches.values():
            admin2.allowed_branches.add(b)

        # Create Supervisors (1 per branch)
        emp_num = 3
        for code, branch in branches.items():
            branch_short = code.split('-')[1].lower().capitalize()
            self._create_user_with_employee(
                company=company,
                branch=branch,
                email=f'gerente.{branch_short.lower()}@saludtotal.com',
                password='demo123',
                first_name=f'Gerente {branch_short}',
                last_name='Farmacia',
                role_type='supervisor',
                is_company_admin=False,
                position='Gerente de Sucursal',
                employee_code=f'FARM-EMP-{emp_num:03d}',
                hire_date=date(2020, 1, 1),
                salary=Decimal('35000.00'),
            )
            emp_num += 1

        # Create Pharmacists/Cashiers (1 per branch)
        for code, branch in branches.items():
            branch_short = code.split('-')[1].lower().capitalize()
            self._create_user_with_employee(
                company=company,
                branch=branch,
                email=f'farmaceutico.{branch_short.lower()}@saludtotal.com',
                password='demo123',
                first_name=f'Farm. {branch_short}',
                last_name='Responsable',
                role_type='cashier',
                is_company_admin=False,
                position='Farmacéutico Responsable',
                employee_code=f'FARM-EMP-{emp_num:03d}',
                hire_date=date(2021, 6, 1),
                salary=Decimal('28000.00'),
            )
            emp_num += 1

        # Create Warehouse Manager (all branches)
        almacen_user, _ = self._create_user_with_employee(
            company=company,
            branch=branch_roma,
            email='almacen.central@saludtotal.com',
            password='demo123',
            first_name='Ricardo',
            last_name='Almacén',
            role_type='warehouse',
            is_company_admin=False,
            position='Jefe de Almacén Central',
            employee_code=f'FARM-EMP-{emp_num:03d}',
            hire_date=date(2019, 8, 1),
            salary=Decimal('25000.00'),
        )
        for b in branches.values():
            almacen_user.allowed_branches.add(b)
        emp_num += 1

        # Create Viewer (reports)
        viewer_user, _ = self._create_user_with_employee(
            company=company,
            branch=branch_roma,
            email='reportes@saludtotal.com',
            password='demo123',
            first_name='Ana',
            last_name='Reportes',
            role_type='viewer',
            is_company_admin=False,
            position='Analista de Reportes',
            employee_code=f'FARM-EMP-{emp_num:03d}',
            hire_date=date(2022, 2, 1),
            salary=Decimal('20000.00'),
        )
        for b in branches.values():
            viewer_user.allowed_branches.add(b)

        # Create Categories
        medicamentos = Category.objects.create(company=company, name='Medicamentos', description='Medicamentos de venta libre')
        cuidado = Category.objects.create(company=company, name='Cuidado Personal', description='Productos de higiene y cuidado')
        vitaminas = Category.objects.create(company=company, name='Vitaminas', description='Vitaminas y suplementos')
        equipo = Category.objects.create(company=company, name='Equipo Médico', description='Equipo médico básico')

        # Create Products
        products_data = [
            {'name': 'Paracetamol 500mg (20 tab)', 'sku': 'FARM-PARA-001', 'category': medicamentos, 'cost': 15, 'price': 35},
            {'name': 'Ibuprofeno 400mg (10 tab)', 'sku': 'FARM-IBUP-001', 'category': medicamentos, 'cost': 25, 'price': 55},
            {'name': 'Omeprazol 20mg (14 cap)', 'sku': 'FARM-OMEP-001', 'category': medicamentos, 'cost': 45, 'price': 89},
            {'name': 'Loratadina 10mg (10 tab)', 'sku': 'FARM-LORA-001', 'category': medicamentos, 'cost': 35, 'price': 75},
            {'name': 'Jarabe para la tos 120ml', 'sku': 'FARM-JARA-001', 'category': medicamentos, 'cost': 55, 'price': 110},
            {'name': 'Aspirina 500mg (20 tab)', 'sku': 'FARM-ASPI-001', 'category': medicamentos, 'cost': 20, 'price': 45},
            {'name': 'Shampoo anticaspa 400ml', 'sku': 'FARM-SHAM-001', 'category': cuidado, 'cost': 65, 'price': 120},
            {'name': 'Pasta dental 150g', 'sku': 'FARM-PAST-001', 'category': cuidado, 'cost': 25, 'price': 48},
            {'name': 'Jabón antibacterial 3pack', 'sku': 'FARM-JABO-001', 'category': cuidado, 'cost': 35, 'price': 65},
            {'name': 'Crema humectante 200ml', 'sku': 'FARM-CREM-001', 'category': cuidado, 'cost': 85, 'price': 159},
            {'name': 'Vitamina C 1000mg (30 tab)', 'sku': 'FARM-VITC-001', 'category': vitaminas, 'cost': 120, 'price': 229},
            {'name': 'Multivitamínico (60 tab)', 'sku': 'FARM-MULT-001', 'category': vitaminas, 'cost': 180, 'price': 349},
            {'name': 'Omega 3 (60 cap)', 'sku': 'FARM-OMEG-001', 'category': vitaminas, 'cost': 150, 'price': 289},
            {'name': 'Vitamina D3 (30 cap)', 'sku': 'FARM-VITD-001', 'category': vitaminas, 'cost': 95, 'price': 179},
            {'name': 'Termómetro digital', 'sku': 'FARM-TERM-001', 'category': equipo, 'cost': 85, 'price': 159},
            {'name': 'Baumanómetro digital', 'sku': 'FARM-BAUM-001', 'category': equipo, 'cost': 350, 'price': 649},
            {'name': 'Oxímetro de pulso', 'sku': 'FARM-OXIM-001', 'category': equipo, 'cost': 280, 'price': 499},
            {'name': 'Caja de cubrebocas (50pz)', 'sku': 'FARM-CUBR-001', 'category': equipo, 'cost': 45, 'price': 89},
        ]

        for p in products_data:
            product = Product.objects.create(
                company=company,
                name=p['name'],
                sku=p['sku'],
                category=p['category'],
                cost_price=Decimal(str(p['cost'])),
                sale_price=Decimal(str(p['price'])),
                unit='unit',
                min_stock=20,
                max_stock=200,
                is_active=True,
            )
            # Add stock to all branches
            for branch in branches.values():
                BranchStock.objects.create(branch=branch, product=product, quantity=100)

        # Create Suppliers
        Supplier.objects.create(
            company=company,
            name='Farmacéutica Nacional',
            code='FARM-FARN-01',
            contact_name='Dr. Alberto Gómez',
            email='pedidos@farmanacional.com',
            phone='800 555 1234',
            city='Ciudad de México',
            state='CDMX',
            payment_terms=30,
            credit_limit=Decimal('500000.00'),
        )
        Supplier.objects.create(
            company=company,
            name='Distribuidora Médica Plus',
            code='FARM-MEDC-01',
            contact_name='Lic. Carmen Díaz',
            email='ventas@medicaplus.com',
            phone='800 666 5678',
            city='Monterrey',
            state='Nuevo León',
            payment_terms=45,
            credit_limit=Decimal('300000.00'),
        )
        Supplier.objects.create(
            company=company,
            name='Vitaminas y Suplementos SA',
            code='FARM-VITA-01',
            contact_name='Ing. Ricardo Luna',
            email='contacto@vitamex.com',
            phone='800 777 9012',
            city='Guadalajara',
            state='Jalisco',
            payment_terms=30,
            credit_limit=Decimal('150000.00'),
        )
        Supplier.objects.create(
            company=company,
            name='Equipo Médico del Norte',
            code='FARM-EQMD-01',
            contact_name='Dr. Martín Salazar',
            email='ventas@equiponorte.com',
            phone='800 888 1234',
            city='Monterrey',
            state='Nuevo León',
            payment_terms=60,
            credit_limit=Decimal('200000.00'),
        )

        return company
