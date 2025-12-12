"""
Management command to initialize BranchStock for all products in all branches.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.inventory.models import Product, BranchStock
from apps.branches.models import Branch


class Command(BaseCommand):
    help = 'Initialize BranchStock records for all products in all active branches'

    def add_arguments(self, parser):
        parser.add_argument(
            '--quantity',
            type=int,
            default=0,
            help='Initial quantity to set for each product (default: 0)'
        )
        parser.add_argument(
            '--branch',
            type=int,
            help='Only initialize for a specific branch ID'
        )
        parser.add_argument(
            '--company',
            type=int,
            help='Only initialize for a specific company ID'
        )

    def handle(self, *args, **options):
        initial_quantity = options['quantity']
        branch_id = options.get('branch')
        company_id = options.get('company')

        # Get branches
        branches = Branch.objects.filter(is_active=True, is_deleted=False)
        if branch_id:
            branches = branches.filter(id=branch_id)
        if company_id:
            branches = branches.filter(company_id=company_id)

        if not branches.exists():
            self.stdout.write(self.style.WARNING('No active branches found'))
            return

        # Get products
        products = Product.active.filter(is_active=True)
        if company_id:
            products = products.filter(company_id=company_id)

        if not products.exists():
            self.stdout.write(self.style.WARNING('No active products found'))
            return

        created_count = 0
        skipped_count = 0

        with transaction.atomic():
            for branch in branches:
                # Filter products by company if branch has a company
                branch_products = products
                if branch.company_id:
                    branch_products = products.filter(company_id=branch.company_id)

                for product in branch_products:
                    branch_stock, created = BranchStock.objects.get_or_create(
                        product=product,
                        branch=branch,
                        defaults={'quantity': initial_quantity}
                    )
                    if created:
                        created_count += 1
                        self.stdout.write(
                            f'  Created: {product.name} -> {branch.name} (qty: {initial_quantity})'
                        )
                    else:
                        skipped_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone! Created {created_count} BranchStock records. '
                f'Skipped {skipped_count} (already existed).'
            )
        )
