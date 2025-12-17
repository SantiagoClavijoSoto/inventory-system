"""
Seed para base de datos local con datos de demostración.

Crea:
- 1 SuperAdmin de plataforma
- 3 Empresas: Ferretería, Farmacia, Zapatería Deportiva
- 1 Admin por empresa
- Productos con stock variable
- Ventas simuladas del 01/12/2025 al 17/12/2025
"""
import random
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.companies.models import Company, Subscription
from apps.branches.models import Branch
from apps.users.models import User, Role, Permission
from apps.inventory.models import Category, Product, BranchStock
from apps.suppliers.models import Supplier
from apps.employees.models import Employee
from apps.sales.models import Sale, SaleItem


class Command(BaseCommand):
    help = 'Seeds local database with demo data including sales history'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando seed de datos locales...')

        with transaction.atomic():
            # Crear permisos y roles
            self.stdout.write('  Creando permisos y roles...')
            Permission.create_default_permissions()
            Role.create_default_roles()

            # Crear SuperAdmin
            superadmin = self._create_superadmin()

            # Crear empresas
            ferreteria = self._create_ferreteria()
            farmacia = self._create_farmacia()
            zapateria = self._create_zapateria()

            # Fix: El modelo Branch resetea is_main globalmente (bug multi-tenant)
            # Restaurar is_main=True para cada sucursal principal por empresa
            self.stdout.write('  Corrigiendo sucursales principales...')
            for company in [ferreteria, farmacia, zapateria]:
                Branch.objects.filter(company=company).update(is_main=True)

            # Crear ventas simuladas
            self.stdout.write('  Generando ventas simuladas (01/12 - 17/12/2025)...')
            self._create_sales_for_company(ferreteria)
            self._create_sales_for_company(farmacia)
            self._create_sales_for_company(zapateria)

        self.stdout.write(self.style.SUCCESS('\n¡Seed completado exitosamente!'))
        self._print_credentials()

    def _create_superadmin(self) -> User:
        self.stdout.write('  Creando SuperAdmin...')
        superadmin, created = User.objects.get_or_create(
            email='superadmin@platform.local',
            defaults={
                'first_name': 'Super',
                'last_name': 'Administrador',
                'is_superuser': True,
                'is_staff': True,
                'company': None,
            }
        )
        if created:
            superadmin.set_password('SuperAdmin123!')
            superadmin.save()
        return superadmin

    def _create_ferreteria(self) -> Company:
        self.stdout.write('  Creando Ferretería El Tornillo Dorado...')

        company = Company.objects.create(
            name='Ferretería El Tornillo Dorado',
            slug='tornillo-dorado',
            legal_name='El Tornillo Dorado S.A.S.',
            tax_id='900123456-1',
            email='contacto@tornillodorado.com',
            phone='601 234 5678',
            address='Calle 45 #12-34, Bogotá',
            plan='professional',
            max_branches=3,
            max_users=10,
            max_products=500,
            primary_color='#f97316',
            secondary_color='#1e3a5f',
            is_active=True,
        )

        # Subscription
        Subscription.objects.create(
            company=company,
            plan='professional',
            status='active',
            billing_cycle='monthly',
            start_date=date(2025, 1, 1),
            amount=Decimal('150000.00'),
            currency='COP',
        )

        branch = Branch.objects.create(
            company=company,
            name='Sucursal Centro',
            code='FERR-CTR',
            store_name='El Tornillo Dorado',
            address='Calle 45 #12-34',
            city='Bogotá',
            state='Cundinamarca',
            postal_code='110111',
            country='Colombia',
            phone='601 234 5678',
            email='centro@tornillodorado.com',
            manager_name='Carlos Rodríguez',
            is_active=True,
            is_main=True,
            tax_rate=Decimal('19.00'),
            currency='COP',
            currency_symbol='$',
        )

        # Admin
        admin = self._create_admin(
            company, branch,
            'admin@ferreteria.local', 'Carlos', 'Rodríguez',
            'FERR-ADM-001'
        )
        company.owner = admin
        company.save()

        # Categorías
        herramientas_man = Category.objects.create(company=company, name='Herramientas Manuales')
        herramientas_elec = Category.objects.create(company=company, name='Herramientas Eléctricas')
        tornilleria = Category.objects.create(company=company, name='Tornillería')
        pinturas = Category.objects.create(company=company, name='Pinturas')
        plomeria = Category.objects.create(company=company, name='Plomería')

        # Productos con stock variable
        products = [
            ('Martillo de Carpintero', 'FERR-001', herramientas_man, 15000, 28000, 45),
            ('Destornillador Phillips Set x6', 'FERR-002', herramientas_man, 22000, 42000, 120),
            ('Taladro Percutor 750W', 'FERR-003', herramientas_elec, 185000, 320000, 8),
            ('Sierra Circular 7"', 'FERR-004', herramientas_elec, 245000, 420000, 5),
            ('Tornillos Madera 2" (caja x100)', 'FERR-005', tornilleria, 8000, 15000, 200),
            ('Tornillos Drywall 1" (caja x100)', 'FERR-006', tornilleria, 6000, 12000, 180),
            ('Pintura Blanca 1 Galón', 'FERR-007', pinturas, 45000, 78000, 35),
            ('Pintura Vinilo Colores 1/4', 'FERR-008', pinturas, 18000, 32000, 60),
            ('Llave Inglesa 12"', 'FERR-009', herramientas_man, 28000, 52000, 28),
            ('Cinta Métrica 5m', 'FERR-010', herramientas_man, 8000, 15000, 85),
            ('Tubo PVC 1/2" (metro)', 'FERR-011', plomeria, 4500, 8500, 150),
            ('Llave de Paso 1/2"', 'FERR-012', plomeria, 12000, 22000, 60),
        ]

        self._create_products(company, branch, products)

        # Proveedores
        Supplier.objects.create(
            company=company, name='Distribuidora Herramex', code='FERR-HERR-01',
            contact_name='Pedro Gómez', email='ventas@herramex.com', phone='601 555 1234',
            city='Bogotá', state='Cundinamarca', payment_terms=30, credit_limit=Decimal('50000000')
        )
        Supplier.objects.create(
            company=company, name='Pinturas Corona', code='FERR-PINT-01',
            contact_name='María López', email='pedidos@corona.com', phone='601 555 5678',
            city='Medellín', state='Antioquia', payment_terms=45, credit_limit=Decimal('30000000')
        )

        return company

    def _create_farmacia(self) -> Company:
        self.stdout.write('  Creando Farmacia Salud Vital...')

        company = Company.objects.create(
            name='Farmacia Salud Vital',
            slug='salud-vital',
            legal_name='Salud Vital Farmacias S.A.S.',
            tax_id='900987654-2',
            email='contacto@saludvital.com',
            phone='601 876 5432',
            address='Carrera 15 #78-90, Bogotá',
            plan='professional',
            max_branches=3,
            max_users=10,
            max_products=500,
            primary_color='#22c55e',
            secondary_color='#0ea5e9',
            is_active=True,
        )

        Subscription.objects.create(
            company=company,
            plan='professional',
            status='active',
            billing_cycle='monthly',
            start_date=date(2025, 1, 1),
            amount=Decimal('150000.00'),
            currency='COP',
        )

        branch = Branch.objects.create(
            company=company,
            name='Sucursal Centro',
            code='FARM-CTR',
            store_name='Salud Vital',
            address='Carrera 15 #78-90',
            city='Bogotá',
            state='Cundinamarca',
            postal_code='110221',
            country='Colombia',
            phone='601 876 5432',
            email='centro@saludvital.com',
            manager_name='Dra. Ana Martínez',
            is_active=True,
            is_main=True,
            tax_rate=Decimal('0.00'),  # Medicamentos exentos
            currency='COP',
            currency_symbol='$',
        )

        admin = self._create_admin(
            company, branch,
            'admin@farmacia.local', 'Ana', 'Martínez',
            'FARM-ADM-001'
        )
        company.owner = admin
        company.save()

        # Categorías
        genericos = Category.objects.create(company=company, name='Medicamentos Genéricos')
        marca = Category.objects.create(company=company, name='Medicamentos de Marca')
        cuidado = Category.objects.create(company=company, name='Cuidado Personal')
        vitaminas = Category.objects.create(company=company, name='Vitaminas y Suplementos')
        primeros = Category.objects.create(company=company, name='Primeros Auxilios')

        products = [
            ('Acetaminofén 500mg (caja x20)', 'FARM-001', genericos, 3500, 6800, 180),
            ('Ibuprofeno 400mg (caja x10)', 'FARM-002', genericos, 4200, 8500, 95),
            ('Omeprazol 20mg (caja x14)', 'FARM-003', genericos, 8500, 16000, 70),
            ('Loratadina 10mg (caja x10)', 'FARM-004', genericos, 5500, 11000, 85),
            ('Advil 400mg (caja x20)', 'FARM-005', marca, 18000, 32000, 45),
            ('Dolex Forte (caja x16)', 'FARM-006', marca, 12000, 22000, 55),
            ('Vitamina C 1000mg (frasco x30)', 'FARM-007', vitaminas, 25000, 45000, 55),
            ('Multivitamínico (frasco x60)', 'FARM-008', vitaminas, 42000, 75000, 35),
            ('Alcohol 70% 500ml', 'FARM-009', primeros, 6500, 12000, 120),
            ('Gasas Estériles (paq x10)', 'FARM-010', primeros, 4500, 8500, 200),
            ('Crema Hidratante 200ml', 'FARM-011', cuidado, 18000, 32000, 40),
            ('Protector Solar FPS50', 'FARM-012', cuidado, 35000, 62000, 25),
            ('Termómetro Digital', 'FARM-013', primeros, 22000, 38000, 15),
        ]

        self._create_products(company, branch, products)

        Supplier.objects.create(
            company=company, name='Laboratorios Genfar', code='FARM-GENF-01',
            contact_name='Dr. Roberto Sánchez', email='pedidos@genfar.com', phone='601 444 1234',
            city='Cali', state='Valle del Cauca', payment_terms=30, credit_limit=Decimal('80000000')
        )
        Supplier.objects.create(
            company=company, name='Droguería Continental', code='FARM-CONT-01',
            contact_name='Lic. Carmen Ruiz', email='ventas@continental.com', phone='601 444 5678',
            city='Bogotá', state='Cundinamarca', payment_terms=45, credit_limit=Decimal('60000000')
        )

        return company

    def _create_zapateria(self) -> Company:
        self.stdout.write('  Creando Deportes RunFast...')

        company = Company.objects.create(
            name='Deportes RunFast',
            slug='runfast',
            legal_name='RunFast Deportes S.A.S.',
            tax_id='900555666-3',
            email='contacto@runfast.com',
            phone='601 333 4444',
            address='Centro Comercial Andino Local 234, Bogotá',
            plan='professional',
            max_branches=3,
            max_users=10,
            max_products=500,
            primary_color='#ef4444',
            secondary_color='#171717',
            is_active=True,
        )

        Subscription.objects.create(
            company=company,
            plan='professional',
            status='active',
            billing_cycle='monthly',
            start_date=date(2025, 1, 1),
            amount=Decimal('150000.00'),
            currency='COP',
        )

        branch = Branch.objects.create(
            company=company,
            name='Sucursal Centro',
            code='RUN-CTR',
            store_name='RunFast',
            address='CC Andino Local 234',
            city='Bogotá',
            state='Cundinamarca',
            postal_code='110111',
            country='Colombia',
            phone='601 333 4444',
            email='andino@runfast.com',
            manager_name='Diego Fernández',
            is_active=True,
            is_main=True,
            tax_rate=Decimal('19.00'),
            currency='COP',
            currency_symbol='$',
        )

        admin = self._create_admin(
            company, branch,
            'admin@zapateria.local', 'Diego', 'Fernández',
            'RUN-ADM-001'
        )
        company.owner = admin
        company.save()

        # Categorías
        running = Category.objects.create(company=company, name='Running')
        futbol = Category.objects.create(company=company, name='Fútbol')
        basketball = Category.objects.create(company=company, name='Basketball')
        training = Category.objects.create(company=company, name='Training/Gym')
        casual = Category.objects.create(company=company, name='Casual Deportivo')

        products = [
            ('Nike Air Zoom Pegasus 40', 'RUN-001', running, 380000, 620000, 12),
            ('Adidas Ultraboost 23', 'RUN-002', running, 420000, 680000, 8),
            ('New Balance Fresh Foam', 'RUN-003', running, 350000, 550000, 15),
            ('Nike Mercurial Vapor 15', 'RUN-004', futbol, 520000, 850000, 10),
            ('Adidas Predator Edge', 'RUN-005', futbol, 480000, 780000, 12),
            ('Puma Future Ultimate', 'RUN-006', futbol, 420000, 680000, 8),
            ('Jordan Why Not Zer0.6', 'RUN-007', basketball, 450000, 720000, 6),
            ('Nike LeBron 21', 'RUN-008', basketball, 580000, 920000, 4),
            ('Under Armour HOVR Phantom', 'RUN-009', training, 320000, 520000, 18),
            ('Reebok Nano X3', 'RUN-010', training, 280000, 450000, 14),
            ('Puma RS-X', 'RUN-011', casual, 250000, 420000, 22),
            ('New Balance 574', 'RUN-012', casual, 280000, 480000, 30),
        ]

        self._create_products(company, branch, products)

        Supplier.objects.create(
            company=company, name='Nike Colombia', code='RUN-NIKE-01',
            contact_name='Andrés Mejía', email='distribuidores@nike.com.co', phone='601 777 1234',
            city='Bogotá', state='Cundinamarca', payment_terms=60, credit_limit=Decimal('200000000')
        )
        Supplier.objects.create(
            company=company, name='Adidas Distribuciones', code='RUN-ADID-01',
            contact_name='Laura Castro', email='comercial@adidas.com.co', phone='601 777 5678',
            city='Medellín', state='Antioquia', payment_terms=60, credit_limit=Decimal('180000000')
        )

        return company

    def _create_admin(self, company, branch, email, first_name, last_name, emp_code) -> User:
        user = User.objects.create_user(
            email=email,
            password='Admin123!',
            first_name=first_name,
            last_name=last_name,
            company=company,
            is_company_admin=True,
            default_branch=branch,
        )
        role = Role.objects.filter(role_type='admin').first()
        if role:
            user.role = role
            user.save()
        user.allowed_branches.add(branch)

        Employee.objects.create(
            user=user,
            employee_code=emp_code,
            position='Administrador',
            department='Gerencia',
            hire_date=date(2024, 1, 1),
            branch=branch,
            salary=Decimal('5000000'),
            status='active',
        )
        return user

    def _create_products(self, company, branch, products_data):
        for name, sku, category, cost, price, stock in products_data:
            product = Product.objects.create(
                company=company,
                name=name,
                sku=sku,
                category=category,
                cost_price=Decimal(str(cost)),
                sale_price=Decimal(str(price)),
                unit='unit',
                min_stock=5,
                max_stock=100,
                is_active=True,
            )
            # La señal post_save ya crea BranchStock con quantity=0
            # Solo actualizamos la cantidad
            BranchStock.objects.filter(
                branch=branch,
                product=product,
            ).update(quantity=stock)

    def _create_sales_for_company(self, company: Company):
        branch = Branch.objects.filter(company=company, is_main=True).first()
        products = list(Product.objects.filter(company=company))
        admin = User.objects.filter(company=company, is_company_admin=True).first()

        if not branch or not products or not admin:
            return

        # Ventas del 01/12/2025 al 17/12/2025
        start_date = date(2025, 12, 1)
        end_date = date(2025, 12, 17)

        # Patrón de ventas: más ventas en fines de semana
        sales_pattern = {
            0: (3, 5),   # Lunes
            1: (4, 6),   # Martes
            2: (3, 5),   # Miércoles
            3: (5, 7),   # Jueves
            4: (4, 6),   # Viernes
            5: (6, 10),  # Sábado
            6: (8, 12),  # Domingo
        }

        current_date = start_date
        sale_counter = 1

        while current_date <= end_date:
            weekday = current_date.weekday()
            min_sales, max_sales = sales_pattern[weekday]
            num_sales = random.randint(min_sales, max_sales)

            # Día festivo (8 dic)
            if current_date == date(2025, 12, 8):
                num_sales = random.randint(8, 12)

            for _ in range(num_sales):
                sale = self._create_single_sale(
                    company, branch, products, admin,
                    current_date, sale_counter
                )
                if sale:
                    sale_counter += 1

            current_date += timedelta(days=1)

        self.stdout.write(f'    {company.name}: {sale_counter - 1} ventas creadas')

    def _create_single_sale(self, company, branch, products, user, sale_date, counter):
        # 1-4 items por venta
        num_items = random.randint(1, 4)
        selected_products = random.sample(products, min(num_items, len(products)))

        subtotal = Decimal('0')
        items_data = []

        for product in selected_products:
            stock = BranchStock.objects.filter(branch=branch, product=product).first()
            if not stock or stock.quantity < 1:
                continue

            quantity = random.randint(1, min(3, stock.quantity))
            unit_price = product.sale_price
            total_price = unit_price * quantity

            items_data.append({
                'product': product,
                'quantity': quantity,
                'unit_price': unit_price,
                'total_price': total_price,
                'stock': stock,
            })
            subtotal += total_price

        if not items_data:
            return None

        # Calcular impuestos
        tax_rate = branch.tax_rate or Decimal('0')
        tax_amount = (subtotal * tax_rate / 100).quantize(Decimal('0.01'))
        total = subtotal + tax_amount

        # Crear hora aleatoria entre 8am y 8pm
        hour = random.randint(8, 20)
        minute = random.randint(0, 59)
        sale_datetime = datetime.combine(sale_date, datetime.min.time().replace(hour=hour, minute=minute))
        sale_datetime = timezone.make_aware(sale_datetime)

        # Crear venta
        payment_methods = ['cash', 'card', 'transfer']
        payment_method = random.choice(payment_methods)

        sale = Sale.objects.create(
            branch=branch,
            cashier=user,  # El modelo usa 'cashier' no 'user'
            sale_number=f'{company.slug[:3].upper()}-{sale_date.strftime("%Y%m%d")}-{counter:04d}',
            subtotal=subtotal,
            tax_amount=tax_amount,
            total=total,
            payment_method=payment_method,
            amount_tendered=total if payment_method != 'cash' else total + Decimal(random.randint(0, 50) * 1000),
            change_amount=Decimal('0') if payment_method != 'cash' else Decimal(random.randint(0, 50) * 1000),
            status='completed',
        )
        sale.created_at = sale_datetime
        sale.save(update_fields=['created_at'])

        # Crear items y actualizar stock
        for item_data in items_data:
            SaleItem.objects.create(
                sale=sale,
                product=item_data['product'],
                product_name=item_data['product'].name,
                product_sku=item_data['product'].sku,
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                cost_price=item_data['product'].cost_price,
                subtotal=item_data['total_price'],
            )
            # Decrementar stock
            item_data['stock'].quantity -= item_data['quantity']
            item_data['stock'].save()

        return sale

    def _print_credentials(self):
        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write('CREDENCIALES')
        self.stdout.write('=' * 60)
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('SuperAdmin Plataforma:'))
        self.stdout.write('  Email:    superadmin@platform.local')
        self.stdout.write('  Password: SuperAdmin123!')
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('Administradores de Empresa (password: Admin123!):'))
        self.stdout.write('  Ferretería:  admin@ferreteria.local')
        self.stdout.write('  Farmacia:    admin@farmacia.local')
        self.stdout.write('  Zapatería:   admin@zapateria.local')
        self.stdout.write('')
        self.stdout.write('=' * 60)
