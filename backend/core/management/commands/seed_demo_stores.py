"""
Management command to seed demo stores with sample data.

Creates 3 demo stores with different branding, categories, products,
employees, and suppliers to demonstrate the white-label capabilities.
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.branches.models import Branch
from apps.users.models import User, Role, Permission
from apps.inventory.models import Category, Product, BranchStock
from apps.suppliers.models import Supplier
from apps.employees.models import Employee


class Command(BaseCommand):
    help = 'Seeds the database with 3 demo stores for white-label demonstration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing demo data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing demo data...')
            self._clear_demo_data()

        self.stdout.write('Creating demo stores...')

        with transaction.atomic():
            # Create default permissions and roles first
            Permission.create_default_permissions()
            Role.create_default_roles()

            # Create the 3 demo stores
            self._create_ferreteria()
            self._create_boutique()
            self._create_farmacia()

        self.stdout.write(self.style.SUCCESS('Successfully created 3 demo stores!'))
        self.stdout.write('')
        self.stdout.write('Demo credentials:')
        self.stdout.write('  Ferretería: admin@tornillofeliz.com / demo123')
        self.stdout.write('  Boutique:   admin@modaelegante.com / demo123')
        self.stdout.write('  Farmacia:   admin@saludtotal.com / demo123')

    def _clear_demo_data(self):
        """Remove demo stores and associated data."""
        demo_codes = ['FERR01', 'BOUT01', 'FARM01']
        demo_emails = [
            'admin@tornillofeliz.com', 'admin@modaelegante.com', 'admin@saludtotal.com'
        ]

        # Delete branches (will cascade to stock)
        Branch.objects.filter(code__in=demo_codes).delete()

        # Delete users
        User.objects.filter(email__in=demo_emails).delete()

        # Delete demo employees
        Employee.objects.filter(employee_code__startswith='DEMO').delete()

        # Delete demo suppliers
        Supplier.objects.filter(code__startswith='DEMO').delete()

        # Delete demo categories
        Category.objects.filter(name__in=[
            'Herramientas', 'Electricidad', 'Plomería', 'Pinturas',
            'Damas', 'Caballeros', 'Accesorios', 'Calzado',
            'Medicamentos', 'Cuidado Personal', 'Vitaminas', 'Equipo Médico'
        ]).delete()

        self.stdout.write('  Demo data cleared.')

    def _create_ferreteria(self):
        """Create Ferretería El Tornillo Feliz demo store."""
        self.stdout.write('  Creating Ferretería El Tornillo Feliz...')

        # Create branch
        branch = Branch.objects.create(
            name='Matriz Centro',
            code='FERR01',
            store_name='El Tornillo Feliz',
            address='Av. Insurgentes Sur 1234',
            city='Ciudad de México',
            state='CDMX',
            postal_code='03100',
            country='México',
            phone='55 1234 5678',
            email='contacto@tornillofeliz.com',
            manager_name='Roberto Hernández',
            manager_phone='55 9876 5432',
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
            receipt_footer='¡Gracias por su compra!\nCambios y devoluciones dentro de 15 días con ticket.',
        )

        # Create admin user
        admin = User.objects.create_user(
            email='admin@tornillofeliz.com',
            password='demo123',
            first_name='Roberto',
            last_name='Hernández',
            is_staff=True,
            default_branch=branch,
        )
        admin_role = Role.objects.filter(role_type='admin').first()
        if admin_role:
            admin.role = admin_role
            admin.save()
        admin.allowed_branches.add(branch)

        # Create categories
        herramientas = Category.objects.create(name='Herramientas', description='Herramientas manuales y eléctricas')
        electricidad = Category.objects.create(name='Electricidad', description='Material eléctrico')
        plomeria = Category.objects.create(name='Plomería', description='Material de plomería')
        pinturas = Category.objects.create(name='Pinturas', description='Pinturas y accesorios')

        # Create products
        products_data = [
            # Herramientas
            {'name': 'Martillo de carpintero 16oz', 'sku': 'FERR-MART-001', 'category': herramientas, 'cost': 89, 'price': 149},
            {'name': 'Desarmador Phillips #2', 'sku': 'FERR-DESA-001', 'category': herramientas, 'cost': 25, 'price': 45},
            {'name': 'Pinzas de electricista', 'sku': 'FERR-PINZ-001', 'category': herramientas, 'cost': 65, 'price': 110},
            {'name': 'Llave inglesa 10"', 'sku': 'FERR-LLAV-001', 'category': herramientas, 'cost': 120, 'price': 199},
            {'name': 'Taladro inalámbrico 12V', 'sku': 'FERR-TALA-001', 'category': herramientas, 'cost': 650, 'price': 1099},
            # Electricidad
            {'name': 'Cable calibre 12 (metro)', 'sku': 'FERR-CABL-001', 'category': electricidad, 'cost': 12, 'price': 22},
            {'name': 'Foco LED 9W', 'sku': 'FERR-FOCO-001', 'category': electricidad, 'cost': 35, 'price': 59},
            {'name': 'Apagador sencillo', 'sku': 'FERR-APAG-001', 'category': electricidad, 'cost': 18, 'price': 35},
            {'name': 'Contacto doble', 'sku': 'FERR-CONT-001', 'category': electricidad, 'cost': 25, 'price': 45},
            # Plomería
            {'name': 'Tubo PVC 2" (metro)', 'sku': 'FERR-TUBO-001', 'category': plomeria, 'cost': 45, 'price': 75},
            {'name': 'Llave de paso 1/2"', 'sku': 'FERR-LLAVE-001', 'category': plomeria, 'cost': 85, 'price': 145},
            {'name': 'Cinta teflón', 'sku': 'FERR-TEFL-001', 'category': plomeria, 'cost': 8, 'price': 15},
            # Pinturas
            {'name': 'Pintura vinílica blanca 4L', 'sku': 'FERR-PINT-001', 'category': pinturas, 'cost': 280, 'price': 450},
            {'name': 'Brocha 3"', 'sku': 'FERR-BROC-001', 'category': pinturas, 'cost': 35, 'price': 65},
            {'name': 'Rodillo 9"', 'sku': 'FERR-RODI-001', 'category': pinturas, 'cost': 55, 'price': 95},
        ]

        for p in products_data:
            # Prices multiplied by 100 to convert to COP (Colombian Pesos)
            product = Product.objects.create(
                name=p['name'],
                sku=p['sku'],
                category=p['category'],
                cost_price=Decimal(str(p['cost'])) * 100,
                sale_price=Decimal(str(p['price'])) * 100,
                unit='unit',
                is_active=True,
            )
            BranchStock.objects.create(
                branch=branch,
                product=product,
                quantity=50,
                min_stock=10,
                max_stock=100,
            )

        # Create suppliers
        Supplier.objects.create(
            name='Truper S.A. de C.V.',
            code='DEMO-TRUP-01',
            contact_name='Juan Pérez',
            email='ventas@truper.com',
            phone='800 123 4567',
            city='Toluca',
            state='Estado de México',
            payment_terms=30,
            credit_limit=Decimal('50000.00'),
        )
        Supplier.objects.create(
            name='Volteck Distribución',
            code='DEMO-VOLT-01',
            contact_name='María García',
            email='comercial@volteck.com',
            phone='800 234 5678',
            city='Guadalajara',
            state='Jalisco',
            payment_terms=15,
            credit_limit=Decimal('30000.00'),
        )

        # Create employees
        Employee.objects.create(
            employee_code='DEMO-FERR-001',
            first_name='Carlos',
            last_name='Mendoza',
            email='carlos@tornillofeliz.com',
            phone='55 1111 2222',
            hire_date='2023-01-15',
            position='Vendedor',
            employment_type='full_time',
            status='active',
            branch=branch,
        )
        Employee.objects.create(
            employee_code='DEMO-FERR-002',
            first_name='Ana',
            last_name='López',
            email='ana@tornillofeliz.com',
            phone='55 3333 4444',
            hire_date='2023-06-01',
            position='Cajera',
            employment_type='full_time',
            status='active',
            branch=branch,
        )

    def _create_boutique(self):
        """Create Boutique Moda Elegante demo store."""
        self.stdout.write('  Creating Boutique Moda Elegante...')

        # Create branch
        branch = Branch.objects.create(
            name='Plaza Satélite',
            code='BOUT01',
            store_name='Moda Elegante',
            address='Centro Comercial Plaza Satélite, Local 234',
            city='Naucalpan',
            state='Estado de México',
            postal_code='53100',
            country='México',
            phone='55 5555 6666',
            email='contacto@modaelegante.com',
            manager_name='Sofía Martínez',
            manager_phone='55 7777 8888',
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
            receipt_header='BOUTIQUE MODA ELEGANTE\nPlaza Satélite Local 234\nTel: 55 5555 6666',
            receipt_footer='¡Gracias por elegirnos!\nCambios dentro de 7 días con ticket.',
        )

        # Create admin user
        admin = User.objects.create_user(
            email='admin@modaelegante.com',
            password='demo123',
            first_name='Sofía',
            last_name='Martínez',
            is_staff=True,
            default_branch=branch,
        )
        admin_role = Role.objects.filter(role_type='admin').first()
        if admin_role:
            admin.role = admin_role
            admin.save()
        admin.allowed_branches.add(branch)

        # Create categories
        damas = Category.objects.create(name='Damas', description='Ropa para dama')
        caballeros = Category.objects.create(name='Caballeros', description='Ropa para caballero')
        accesorios = Category.objects.create(name='Accesorios', description='Accesorios y complementos')
        calzado = Category.objects.create(name='Calzado', description='Zapatos y calzado')

        # Create products
        products_data = [
            # Damas
            {'name': 'Blusa manga corta floral', 'sku': 'BOUT-BLUS-001', 'category': damas, 'cost': 180, 'price': 349},
            {'name': 'Pantalón de vestir negro', 'sku': 'BOUT-PANT-001', 'category': damas, 'cost': 250, 'price': 499},
            {'name': 'Vestido casual verano', 'sku': 'BOUT-VEST-001', 'category': damas, 'cost': 320, 'price': 649},
            {'name': 'Falda midi plisada', 'sku': 'BOUT-FALD-001', 'category': damas, 'cost': 200, 'price': 399},
            # Caballeros
            {'name': 'Camisa formal azul', 'sku': 'BOUT-CAMI-001', 'category': caballeros, 'cost': 280, 'price': 549},
            {'name': 'Pantalón chino beige', 'sku': 'BOUT-CHIN-001', 'category': caballeros, 'cost': 320, 'price': 599},
            {'name': 'Polo básico blanco', 'sku': 'BOUT-POLO-001', 'category': caballeros, 'cost': 150, 'price': 299},
            {'name': 'Saco sport gris', 'sku': 'BOUT-SACO-001', 'category': caballeros, 'cost': 650, 'price': 1299},
            # Accesorios
            {'name': 'Bolso tote café', 'sku': 'BOUT-BOLS-001', 'category': accesorios, 'cost': 400, 'price': 799},
            {'name': 'Cinturón piel negro', 'sku': 'BOUT-CINT-001', 'category': accesorios, 'cost': 180, 'price': 349},
            {'name': 'Bufanda lana gris', 'sku': 'BOUT-BUFA-001', 'category': accesorios, 'cost': 120, 'price': 249},
            # Calzado
            {'name': 'Zapatillas tacón bajo', 'sku': 'BOUT-ZAPA-001', 'category': calzado, 'cost': 450, 'price': 899},
            {'name': 'Mocasines cuero café', 'sku': 'BOUT-MOCA-001', 'category': calzado, 'cost': 520, 'price': 999},
            {'name': 'Sandalias verano', 'sku': 'BOUT-SAND-001', 'category': calzado, 'cost': 280, 'price': 549},
        ]

        for p in products_data:
            # Prices multiplied by 100 to convert to COP (Colombian Pesos)
            product = Product.objects.create(
                name=p['name'],
                sku=p['sku'],
                category=p['category'],
                cost_price=Decimal(str(p['cost'])) * 100,
                sale_price=Decimal(str(p['price'])) * 100,
                unit='unit',
                is_active=True,
            )
            BranchStock.objects.create(
                branch=branch,
                product=product,
                quantity=25,
                min_stock=5,
                max_stock=50,
            )

        # Create suppliers
        Supplier.objects.create(
            name='Textiles Premium S.A.',
            code='DEMO-TEXT-01',
            contact_name='Laura Ruiz',
            email='ventas@textilespremium.com',
            phone='33 1234 5678',
            city='Guadalajara',
            state='Jalisco',
            payment_terms=45,
            credit_limit=Decimal('100000.00'),
        )
        Supplier.objects.create(
            name='Calzado Fino de León',
            code='DEMO-CALZ-01',
            contact_name='Pedro Sánchez',
            email='pedidos@calzadofino.com',
            phone='477 123 4567',
            city='León',
            state='Guanajuato',
            payment_terms=30,
            credit_limit=Decimal('80000.00'),
        )

        # Create employees
        Employee.objects.create(
            employee_code='DEMO-BOUT-001',
            first_name='Gabriela',
            last_name='Torres',
            email='gabriela@modaelegante.com',
            phone='55 2222 3333',
            hire_date='2022-09-01',
            position='Asesora de imagen',
            employment_type='full_time',
            status='active',
            branch=branch,
        )
        Employee.objects.create(
            employee_code='DEMO-BOUT-002',
            first_name='Miguel',
            last_name='Ángel',
            email='miguel@modaelegante.com',
            phone='55 4444 5555',
            hire_date='2023-03-15',
            position='Encargado de tienda',
            employment_type='full_time',
            status='active',
            branch=branch,
        )
        Employee.objects.create(
            employee_code='DEMO-BOUT-003',
            first_name='Patricia',
            last_name='Vega',
            email='patricia@modaelegante.com',
            phone='55 6666 7777',
            hire_date='2024-01-10',
            position='Vendedora',
            employment_type='part_time',
            status='active',
            branch=branch,
        )

    def _create_farmacia(self):
        """Create Farmacia Salud Total demo store."""
        self.stdout.write('  Creating Farmacia Salud Total...')

        # Create branch
        branch = Branch.objects.create(
            name='Sucursal Roma',
            code='FARM01',
            store_name='Salud Total',
            address='Av. Álvaro Obregón 145',
            city='Ciudad de México',
            state='CDMX',
            postal_code='06700',
            country='México',
            phone='55 8888 9999',
            email='atencion@saludtotal.com',
            manager_name='Dr. Fernando Reyes',
            manager_phone='55 1212 3434',
            is_active=True,
            is_main=False,
            opening_time='07:00',
            closing_time='22:00',
            primary_color='#22c55e',
            secondary_color='#64748b',
            accent_color='#14b8a6',
            tax_rate=Decimal('0.00'),  # Medicamentos exentos de IVA
            currency='MXN',
            currency_symbol='$',
            receipt_header='FARMACIA SALUD TOTAL\nAv. Álvaro Obregón 145, Col. Roma\nTel: 55 8888 9999',
            receipt_footer='Medicamentos de venta libre.\nConsulte a su médico.',
        )

        # Create admin user
        admin = User.objects.create_user(
            email='admin@saludtotal.com',
            password='demo123',
            first_name='Fernando',
            last_name='Reyes',
            is_staff=True,
            default_branch=branch,
        )
        admin_role = Role.objects.filter(role_type='admin').first()
        if admin_role:
            admin.role = admin_role
            admin.save()
        admin.allowed_branches.add(branch)

        # Create categories
        medicamentos = Category.objects.create(name='Medicamentos', description='Medicamentos de venta libre')
        cuidado = Category.objects.create(name='Cuidado Personal', description='Productos de higiene y cuidado')
        vitaminas = Category.objects.create(name='Vitaminas', description='Vitaminas y suplementos')
        equipo = Category.objects.create(name='Equipo Médico', description='Equipo médico básico')

        # Create products
        products_data = [
            # Medicamentos
            {'name': 'Paracetamol 500mg (20 tab)', 'sku': 'FARM-PARA-001', 'category': medicamentos, 'cost': 15, 'price': 35},
            {'name': 'Ibuprofeno 400mg (10 tab)', 'sku': 'FARM-IBUP-001', 'category': medicamentos, 'cost': 25, 'price': 55},
            {'name': 'Omeprazol 20mg (14 cap)', 'sku': 'FARM-OMEP-001', 'category': medicamentos, 'cost': 45, 'price': 89},
            {'name': 'Loratadina 10mg (10 tab)', 'sku': 'FARM-LORA-001', 'category': medicamentos, 'cost': 35, 'price': 75},
            {'name': 'Jarabe para la tos 120ml', 'sku': 'FARM-JARA-001', 'category': medicamentos, 'cost': 55, 'price': 110},
            # Cuidado Personal
            {'name': 'Shampoo anticaspa 400ml', 'sku': 'FARM-SHAM-001', 'category': cuidado, 'cost': 65, 'price': 120},
            {'name': 'Pasta dental 150g', 'sku': 'FARM-PAST-001', 'category': cuidado, 'cost': 25, 'price': 48},
            {'name': 'Jabón antibacterial 3pack', 'sku': 'FARM-JABO-001', 'category': cuidado, 'cost': 35, 'price': 65},
            {'name': 'Crema humectante 200ml', 'sku': 'FARM-CREM-001', 'category': cuidado, 'cost': 85, 'price': 159},
            # Vitaminas
            {'name': 'Vitamina C 1000mg (30 tab)', 'sku': 'FARM-VITC-001', 'category': vitaminas, 'cost': 120, 'price': 229},
            {'name': 'Multivitamínico (60 tab)', 'sku': 'FARM-MULT-001', 'category': vitaminas, 'cost': 180, 'price': 349},
            {'name': 'Omega 3 (60 cap)', 'sku': 'FARM-OMEG-001', 'category': vitaminas, 'cost': 150, 'price': 289},
            {'name': 'Vitamina D3 (30 cap)', 'sku': 'FARM-VITD-001', 'category': vitaminas, 'cost': 95, 'price': 179},
            # Equipo médico
            {'name': 'Termómetro digital', 'sku': 'FARM-TERM-001', 'category': equipo, 'cost': 85, 'price': 159},
            {'name': 'Baumanómetro digital', 'sku': 'FARM-BAUM-001', 'category': equipo, 'cost': 350, 'price': 649},
            {'name': 'Oxímetro de pulso', 'sku': 'FARM-OXIM-001', 'category': equipo, 'cost': 280, 'price': 499},
            {'name': 'Caja de cubrebocas (50pz)', 'sku': 'FARM-CUBR-001', 'category': equipo, 'cost': 45, 'price': 89},
        ]

        for p in products_data:
            # Prices multiplied by 100 to convert to COP (Colombian Pesos)
            product = Product.objects.create(
                name=p['name'],
                sku=p['sku'],
                category=p['category'],
                cost_price=Decimal(str(p['cost'])) * 100,
                sale_price=Decimal(str(p['price'])) * 100,
                unit='unit',
                is_active=True,
            )
            BranchStock.objects.create(
                branch=branch,
                product=product,
                quantity=100,
                min_stock=20,
                max_stock=200,
            )

        # Create suppliers
        Supplier.objects.create(
            name='Farmacéutica Nacional',
            code='DEMO-FARN-01',
            contact_name='Dr. Alberto Gómez',
            email='pedidos@farmanacional.com',
            phone='800 555 1234',
            city='Ciudad de México',
            state='CDMX',
            payment_terms=30,
            credit_limit=Decimal('200000.00'),
        )
        Supplier.objects.create(
            name='Distribuidora Médica Plus',
            code='DEMO-MEDC-01',
            contact_name='Lic. Carmen Díaz',
            email='ventas@medicaplus.com',
            phone='800 666 5678',
            city='Monterrey',
            state='Nuevo León',
            payment_terms=45,
            credit_limit=Decimal('150000.00'),
        )
        Supplier.objects.create(
            name='Vitaminas y Suplementos SA',
            code='DEMO-VITA-01',
            contact_name='Ing. Ricardo Luna',
            email='contacto@vitamex.com',
            phone='800 777 9012',
            city='Guadalajara',
            state='Jalisco',
            payment_terms=30,
            credit_limit=Decimal('80000.00'),
        )

        # Create employees (pharmacists)
        Employee.objects.create(
            employee_code='DEMO-FARM-001',
            first_name='Dra. Elena',
            last_name='Ramírez',
            email='elena@saludtotal.com',
            phone='55 1313 1414',
            hire_date='2021-05-01',
            position='Farmacéutica titular',
            employment_type='full_time',
            status='active',
            branch=branch,
        )
        Employee.objects.create(
            employee_code='DEMO-FARM-002',
            first_name='Jorge',
            last_name='Castillo',
            email='jorge@saludtotal.com',
            phone='55 1515 1616',
            hire_date='2022-08-15',
            position='Auxiliar de farmacia',
            employment_type='full_time',
            status='active',
            branch=branch,
        )
