from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from apps.users.models import User, Role, Permission
from apps.companies.models import Company, Subscription
from apps.branches.models import Branch
from apps.employees.models import Employee, Shift
from apps.inventory.models import Category, Product, BranchStock, StockMovement, StockAlert
from apps.suppliers.models import Supplier, PurchaseOrder, PurchaseOrderItem
from apps.sales.models import Sale, SaleItem, DailyCashRegister
from apps.alerts.models import Alert, AlertConfiguration, UserAlertPreference


class Command(BaseCommand):
    help = 'Clean database for reseeding while preserving superusers, company admins, and companies'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-confirm',
            action='store_true',
            help='Skip confirmation prompt',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n=== DATABASE CLEANUP FOR RESEED ===\n'))

        # Get admin user IDs to preserve
        admin_ids = list(
            User.objects.filter(Q(is_superuser=True) | Q(is_company_admin=True))
            .values_list('id', flat=True)
        )

        admin_count = len(admin_ids)
        company_count = Company.objects.count()

        # Calculate what will be deleted
        counts = self._calculate_deletion_counts(admin_ids)

        # Show what will be deleted
        self.stdout.write(self.style.SUCCESS(f'\nWILL PRESERVE:'))
        self.stdout.write(f'  - {admin_count} admin users (superusers + company admins)')
        self.stdout.write(f'  - {company_count} companies\n')

        self.stdout.write(self.style.WARNING('WILL DELETE:'))
        self.stdout.write(f'\nPhase 1 - User Dependencies:')
        self.stdout.write(f'  - {counts["user_alert_preferences"]} UserAlertPreferences')
        self.stdout.write(f'  - {counts["alert_configurations"]} AlertConfigurations')
        self.stdout.write(f'  - {counts["alerts"]} Alerts')
        self.stdout.write(f'  - {counts["stock_alerts"]} StockAlerts')
        self.stdout.write(f'  - {counts["sale_items"]} SaleItems')
        self.stdout.write(f'  - {counts["sales"]} Sales')
        self.stdout.write(f'  - {counts["daily_cash_registers"]} DailyCashRegisters')
        self.stdout.write(f'  - {counts["shifts"]} Shifts')
        self.stdout.write(f'  - {counts["employees"]} Employees')
        self.stdout.write(f'  - {counts["purchase_order_items"]} PurchaseOrderItems')
        self.stdout.write(f'  - {counts["purchase_orders"]} PurchaseOrders')
        self.stdout.write(f'  - {counts["stock_movements"]} StockMovements')

        self.stdout.write(f'\nPhase 2 - Inventory:')
        self.stdout.write(f'  - {counts["branch_stocks"]} BranchStocks')
        self.stdout.write(f'  - {counts["products"]} Products')
        self.stdout.write(f'  - {counts["categories"]} Categories')
        self.stdout.write(f'  - {counts["suppliers"]} Suppliers')

        self.stdout.write(f'\nPhase 3 - Structure:')
        self.stdout.write(f'  - {counts["branches"]} Branches')
        self.stdout.write(f'  - {counts["subscriptions"]} Subscriptions')
        self.stdout.write(f'  - {counts["roles"]} Roles')
        self.stdout.write(f'  - {counts["permissions"]} Permissions')

        self.stdout.write(f'\nPhase 4 - Non-admin Users:')
        self.stdout.write(f'  - {counts["users"]} Users\n')

        total = sum(counts.values())
        self.stdout.write(self.style.ERROR(f'TOTAL RECORDS TO DELETE: {total}\n'))

        # Confirmation
        if not options['skip_confirm']:
            confirm = input('Are you sure you want to proceed? Type "yes" to continue: ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Operation cancelled.'))
                return

        # Execute cleanup
        try:
            with transaction.atomic():
                self._execute_cleanup(admin_ids)

            self.stdout.write(self.style.SUCCESS('\n=== CLEANUP COMPLETED SUCCESSFULLY ===\n'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nERROR during cleanup: {str(e)}'))
            raise

    def _calculate_deletion_counts(self, admin_ids):
        """Calculate how many records will be deleted"""
        return {
            # Phase 1
            'user_alert_preferences': UserAlertPreference.objects.count(),
            'alert_configurations': AlertConfiguration.objects.count(),
            'alerts': Alert.objects.count(),
            'stock_alerts': StockAlert.objects.count(),
            'sale_items': SaleItem.objects.count(),
            'sales': Sale.objects.count(),
            'daily_cash_registers': DailyCashRegister.objects.count(),
            'shifts': Shift.objects.count(),
            'employees': Employee.objects.count(),  # ALL employees (admins lose employee profile)
            'purchase_order_items': PurchaseOrderItem.objects.count(),
            'purchase_orders': PurchaseOrder.objects.count(),
            'stock_movements': StockMovement.objects.count(),

            # Phase 2
            'branch_stocks': BranchStock.objects.count(),
            'products': Product.objects.count(),
            'categories': Category.objects.count(),
            'suppliers': Supplier.objects.count(),

            # Phase 3
            'branches': Branch.objects.count(),
            'subscriptions': Subscription.objects.count(),
            'roles': Role.objects.count(),
            'permissions': Permission.objects.count(),

            # Phase 4
            'users': User.objects.exclude(id__in=admin_ids).count(),
        }

    def _execute_cleanup(self, admin_ids):
        """Execute the cleanup in proper order"""

        # Prepare companies (remove owner FK to avoid circular dependency)
        self.stdout.write('\nPreparing companies...')
        Company.objects.update(owner=None)

        # Phase 1 - User Dependencies
        self.stdout.write(self.style.WARNING('\nPhase 1: Deleting user dependencies...'))

        self.stdout.write('  - UserAlertPreferences...')
        UserAlertPreference.objects.all().delete()

        self.stdout.write('  - AlertConfigurations...')
        AlertConfiguration.objects.all().delete()

        self.stdout.write('  - Alerts...')
        Alert.objects.all().delete()

        self.stdout.write('  - StockAlerts...')
        StockAlert.objects.all().delete()

        self.stdout.write('  - SaleItems...')
        SaleItem.objects.all().delete()

        self.stdout.write('  - Sales...')
        Sale.objects.all().delete()

        self.stdout.write('  - DailyCashRegisters...')
        DailyCashRegister.objects.all().delete()

        self.stdout.write('  - Shifts...')
        Shift.objects.all().delete()

        self.stdout.write('  - Employees (ALL - admins will lose employee profile)...')
        Employee.objects.all().delete()

        self.stdout.write('  - PurchaseOrderItems...')
        PurchaseOrderItem.objects.all().delete()

        self.stdout.write('  - PurchaseOrders...')
        PurchaseOrder.objects.all().delete()

        self.stdout.write('  - StockMovements...')
        StockMovement.objects.all().delete()

        # Phase 2 - Inventory
        self.stdout.write(self.style.WARNING('\nPhase 2: Deleting inventory...'))

        self.stdout.write('  - BranchStocks...')
        BranchStock.objects.all().delete()

        self.stdout.write('  - Products...')
        Product.objects.all().delete()

        self.stdout.write('  - Categories...')
        Category.objects.all().delete()

        self.stdout.write('  - Suppliers...')
        Supplier.objects.all().delete()

        # Phase 3 - Structure
        self.stdout.write(self.style.WARNING('\nPhase 3: Deleting structure...'))

        self.stdout.write('  - Branches...')
        Branch.objects.all().delete()

        self.stdout.write('  - Subscriptions...')
        Subscription.objects.all().delete()

        self.stdout.write('  - Roles...')
        Role.objects.all().delete()

        self.stdout.write('  - Permissions...')
        Permission.objects.all().delete()

        # Phase 4 - Non-admin Users
        self.stdout.write(self.style.WARNING('\nPhase 4: Deleting non-admin users...'))
        deleted_count = User.objects.exclude(id__in=admin_ids).delete()
        self.stdout.write(f'  - Deleted {deleted_count[0]} users')

        # Clean up admin user relations
        self.stdout.write(self.style.WARNING('\nCleaning admin user relations...'))
        admin_users = User.objects.filter(id__in=admin_ids)
        for user in admin_users:
            user.default_branch = None
            user.role = None
            user.save()
            user.allowed_branches.clear()

        self.stdout.write(self.style.SUCCESS(f'  - Cleaned {admin_users.count()} admin users'))
