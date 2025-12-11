import django_filters
from .models import Product, StockMovement


class ProductFilter(django_filters.FilterSet):
    """Filter for products with various criteria"""

    name = django_filters.CharFilter(lookup_expr='icontains')
    sku = django_filters.CharFilter(lookup_expr='icontains')
    barcode = django_filters.CharFilter(lookup_expr='exact')
    category = django_filters.NumberFilter(field_name='category_id')
    supplier = django_filters.NumberFilter(field_name='supplier_id')

    min_price = django_filters.NumberFilter(field_name='sale_price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='sale_price', lookup_expr='lte')

    is_active = django_filters.BooleanFilter()
    is_sellable = django_filters.BooleanFilter()

    # Filter by category and all its descendants
    category_tree = django_filters.NumberFilter(method='filter_category_tree')

    class Meta:
        model = Product
        fields = [
            'name', 'sku', 'barcode', 'category', 'supplier',
            'min_price', 'max_price', 'is_active', 'is_sellable',
            'category_tree'
        ]

    def filter_category_tree(self, queryset, name, value):
        """Filter by category and all its descendants"""
        from .models import Category
        try:
            category = Category.objects.get(pk=value)
            descendant_ids = [category.id] + [c.id for c in category.get_descendants()]
            return queryset.filter(category_id__in=descendant_ids)
        except Category.DoesNotExist:
            return queryset.none()


class StockMovementFilter(django_filters.FilterSet):
    """Filter for stock movement history"""

    product = django_filters.NumberFilter(field_name='product_id')
    branch = django_filters.NumberFilter(field_name='branch_id')
    movement_type = django_filters.ChoiceFilter(
        choices=StockMovement.MOVEMENT_TYPES
    )
    created_by = django_filters.NumberFilter(field_name='created_by_id')

    date_from = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte'
    )
    date_to = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte'
    )

    class Meta:
        model = StockMovement
        fields = [
            'product', 'branch', 'movement_type', 'created_by',
            'date_from', 'date_to'
        ]
