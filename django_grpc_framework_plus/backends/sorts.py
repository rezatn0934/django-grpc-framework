from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class BaseSortBackend:
    """
    Base class for gRPC sort backends.
    Similar to DRF's ordering but adapted for gRPC services.
    """

    def filter_queryset(self, request, queryset, view):
        """
        Sort the queryset based on the request parameters.
        This method should be overridden by subclasses.
        """
        return queryset


class DynamicSort(BaseSortBackend):
    """
    A dynamic sort backend for gRPC services that provides DRF-like sorting capabilities.
    Supports:
    - Ascending/descending sorting
    - Multiple field sorting
    - Related field sorting
    - Field validation
    """

    def get_sort_fields(self, request, view):
        """
        Get sort fields from request parameters.
        """
        if not hasattr(request, "filters"):
            return []

        sort_param = request.filters.get("sort", "")
        if not sort_param:
            return []

        # Split by comma and handle each field
        fields = []
        for field in sort_param.split(","):
            # Handle descending fields (prefixed with -)
            is_descending = field.startswith("-")
            if is_descending:
                field = field[1:]

            # Validate field
            if not self._is_valid_field(field, view):
                continue

            fields.append({"field": field, "descending": is_descending})

        return fields

    def _is_valid_field(self, field, view):
        """
        Check if the field is allowed for sorting.
        """
        sort_fields = getattr(view, "sort_fields", [])
        if not isinstance(sort_fields, (list, tuple)):
            return True  # If sort_fields is not a list/tuple, allow all fields

        # Handle related fields
        base_field = field.split("__")[0]
        return base_field in sort_fields

    def filter_queryset(self, request, queryset, view):
        """
        Sort the queryset based on the request parameters.
        """
        try:
            sort_fields = self.get_sort_fields(request, view)
            if not sort_fields:
                return queryset

            # Build order_by list
            order_by = []
            for field in sort_fields:
                order_by.append(f"{'-' if field['descending'] else ''}{field['field']}")

            return queryset.order_by(*order_by)

        except Exception as e:
            raise ValidationError(
                {"error": _("Invalid sort parameters: {}").format(str(e))}
            )
