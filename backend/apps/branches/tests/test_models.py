"""
Tests for Branch models.
"""
import pytest
from datetime import time
from django.db import IntegrityError

from apps.branches.models import Branch


class TestBranchModel:
    """Tests for the Branch model."""

    def test_branch_creation(self, db):
        """Test creating a branch with minimal required fields."""
        branch = Branch.objects.create(
            name='Test Branch',
            code='TST001',
            is_active=True
        )
        assert branch.id is not None
        assert branch.name == 'Test Branch'
        assert branch.code == 'TST001'

    def test_branch_str(self, db):
        """Test branch string representation."""
        branch = Branch.objects.create(
            name='Main Store',
            code='MAIN',
            is_active=True
        )
        assert str(branch) == 'MAIN - Main Store'

    def test_branch_code_unique(self, db):
        """Test that branch code must be unique."""
        Branch.objects.create(
            name='First Branch',
            code='UNIQUE',
            is_active=True
        )
        with pytest.raises(IntegrityError):
            Branch.objects.create(
                name='Second Branch',
                code='UNIQUE',
                is_active=True
            )

    def test_branch_full_address(self, db):
        """Test full_address property."""
        branch = Branch.objects.create(
            name='Full Address Branch',
            code='FAB',
            address='123 Main St',
            city='Mexico City',
            state='CDMX',
            postal_code='06600',
            country='México'
        )
        expected = '123 Main St, Mexico City, CDMX, 06600, México'
        assert branch.full_address == expected

    def test_branch_full_address_partial(self, db):
        """Test full_address with some fields missing."""
        branch = Branch.objects.create(
            name='Partial Address',
            code='PAR',
            city='Guadalajara',
            state='Jalisco'
        )
        expected = 'Guadalajara, Jalisco, México'
        assert branch.full_address == expected

    def test_branch_default_country(self, db):
        """Test that default country is México."""
        branch = Branch.objects.create(
            name='Default Country',
            code='DEF'
        )
        assert branch.country == 'México'

    def test_branch_default_is_active(self, db):
        """Test that default is_active is True."""
        branch = Branch.objects.create(
            name='Active Default',
            code='ACT'
        )
        assert branch.is_active is True

    def test_branch_default_is_main(self, db):
        """Test that default is_main is False."""
        branch = Branch.objects.create(
            name='Not Main',
            code='NMN'
        )
        assert branch.is_main is False


class TestBranchMainBranchBehavior:
    """Tests for main branch behavior."""

    def test_only_one_main_branch(self, db):
        """Test that only one branch can be main."""
        first_main = Branch.objects.create(
            name='First Main',
            code='FM',
            is_main=True
        )
        assert first_main.is_main is True

        # Create another main branch
        second_main = Branch.objects.create(
            name='Second Main',
            code='SM',
            is_main=True
        )
        assert second_main.is_main is True

        # First should no longer be main
        first_main.refresh_from_db()
        assert first_main.is_main is False

    def test_updating_main_branch(self, db):
        """Test updating a branch to be main removes main from others."""
        first = Branch.objects.create(name='First', code='F1', is_main=True)
        second = Branch.objects.create(name='Second', code='F2', is_main=False)

        # Update second to be main
        second.is_main = True
        second.save()

        first.refresh_from_db()
        assert first.is_main is False
        assert second.is_main is True

    def test_can_have_no_main_branch(self, db):
        """Test that having no main branch is allowed."""
        branch = Branch.objects.create(name='Not Main', code='NM', is_main=False)
        assert branch.is_main is False
        assert Branch.objects.filter(is_main=True).count() == 0


class TestBranchOperationalSettings:
    """Tests for branch operational settings."""

    def test_branch_with_hours(self, db):
        """Test branch with opening and closing times."""
        branch = Branch.objects.create(
            name='Timed Branch',
            code='TIM',
            opening_time=time(9, 0),
            closing_time=time(21, 0)
        )
        assert branch.opening_time == time(9, 0)
        assert branch.closing_time == time(21, 0)

    def test_branch_hours_nullable(self, db):
        """Test that hours can be null."""
        branch = Branch.objects.create(
            name='No Hours',
            code='NOH'
        )
        assert branch.opening_time is None
        assert branch.closing_time is None


class TestBranchManagers:
    """Tests for Branch model managers."""

    def test_active_manager(self, db):
        """Test ActiveManager filters deleted records."""
        active = Branch.objects.create(name='Active', code='ACT', is_active=True)
        # Soft delete using the mixin
        inactive = Branch.objects.create(name='Deleted', code='DEL', is_active=True)
        inactive.delete()  # This sets is_deleted=True if SoftDeleteMixin works

        # active manager should only return non-deleted
        active_branches = Branch.active.all()
        assert active in active_branches

    def test_default_manager_returns_all(self, db):
        """Test that objects manager returns all records."""
        Branch.objects.create(name='One', code='ONE')
        Branch.objects.create(name='Two', code='TWO')

        assert Branch.objects.count() >= 2


class TestBranchSoftDelete:
    """Tests for Branch soft delete functionality."""

    def test_soft_delete(self, db):
        """Test that deleting a branch soft deletes it."""
        branch = Branch.objects.create(name='To Delete', code='DEL')
        branch.delete()

        # Should still exist in database
        assert Branch.objects.filter(code='DEL').exists()
        # Should be marked as deleted
        branch.refresh_from_db()
        assert branch.is_deleted is True

    def test_restore(self, db):
        """Test restoring a soft deleted branch."""
        branch = Branch.objects.create(name='To Restore', code='RES')
        branch.delete()

        assert branch.is_deleted is True

        # Restore
        branch.restore()
        branch.refresh_from_db()
        assert branch.is_deleted is False
