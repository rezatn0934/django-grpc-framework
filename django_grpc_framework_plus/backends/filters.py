from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class BaseFilterBackend:
    """
    Base class for gRPC filter backends.
    Similar to DRF's filter backend but adapted for gRPC services.
    """

    def filter_queryset(self, request, queryset, view):
        """
        Filter the queryset based on the request parameters.
        This method should be overridden by subclasses.
        """
        return queryset


class DynamicFilterBackend(BaseFilterBackend):
    """
    A generic, advanced dynamic filter backend for gRPC services.
    Supports:
    - Exact + icontains + all lookups
    - exclude filters (!field)
    - dynamic field lookup (field__lt, field__icontains, field__date, ...)
    - IN and RANGE filters
    - search across multiple fields
    - generic filter_groups with lookup support (advanced)
    """

    # Supported lookup expressions
    LOOKUP_EXPRESSIONS = {
        "exact": "",
        "iexact": "__iexact",
        "contains": "__contains",
        "icontains": "__icontains",
        "in": "__in",
        "gt": "__gt",
        "gte": "__gte",
        "lt": "__lt",
        "lte": "__lte",
        "startswith": "__startswith",
        "istartswith": "__istartswith",
        "endswith": "__endswith",
        "iendswith": "__iendswith",
        "range": "__range",
        "date": "__date",
        "year": "__year",
        "month": "__month",
        "day": "__day",
        "isnull": "__isnull",
    }

    # Reserved keys that should not be applied as filters
    RESERVED_KEYS = {"page", "page_size", "search", "sort"}

    # -----------------------
    # Extract normal filters
    # -----------------------
    def get_basic_filter_kwargs(self, filters):
        """
        Get filter kwargs from request parameters.
        """
        filter_kwargs = {}
        exclude_kwargs = {}

        for key, value in filters.items():
            # Skip RESERVED_KEYS as they're handled separately
            if key in self.RESERVED_KEYS:
                continue

            # Handle exclude filters (prefixed with !)
            is_exclude = key.startswith("!")
            if is_exclude:
                key = key[1:]

            # Split the filter key into field and lookup parts
            # Handle multiple underscores for related fields
            parts = key.split("__")
            if parts[-1] in self.LOOKUP_EXPRESSIONS or parts[-1] in ["in", "range"]:
                field = "__".join(parts[:-1])
                lookup = parts[-1]
            else:
                field = key
                lookup = "exact"

            # Validate lookup expression
            if lookup not in self.LOOKUP_EXPRESSIONS and lookup not in ["in", "range"]:
                continue

            # Handle special cases for value conversion
            if lookup == "in":
                value = value.split(",")
            elif lookup == "range":
                value = value.split(",")
                if len(value) != 2:
                    continue
            elif lookup == "isnull":
                value = str(value).lower() == "true"
            elif lookup in ["gt", "gte", "lt", "lte"]:
                try:
                    value = float(value)
                except (TypeError, ValueError):
                    continue

            # Build the filter key with lookup
            filter_key = f"{field}{self.LOOKUP_EXPRESSIONS.get(lookup, '')}"

            # Add to appropriate dict
            if is_exclude:
                exclude_kwargs[filter_key] = value
            else:
                filter_kwargs[filter_key] = value

        return filter_kwargs, exclude_kwargs

    def apply_search(self, queryset, search_term, search_fields):
        """
        Apply search filter across multiple fields.
        """
        if not search_term or not search_fields:
            return queryset

        q = Q()
        for field in search_fields:
            q |= Q(**{f"{field}__icontains": search_term})
        return queryset.filter(q)

    # -----------------------
    # Advanced grouped filters
    # -----------------------
    def apply_grouped_filters(self, queryset, view, filters):
        """
        filter_groups = {
            "name": ["first_name", "last_name"],
            "location": ["city", "province"],
        }

        supports:
            name="ali"
            name__icontains="ali"
            name__istartswith="a"
        """

        filter_groups = getattr(view, "filter_groups", {})
        if not filter_groups:
            return queryset

        for group_key, fields in filter_groups.items():

            # find filter keys that match this group
            for incoming_key, value in list(filters.items()):

                if not incoming_key.startswith(group_key):
                    continue

                parts = incoming_key.split("__")

                # detect lookup from key, default icontains
                if len(parts) > 1 and parts[-1] in self.LOOKUP_EXPRESSIONS:
                    lookup = parts[-1]
                else:
                    lookup = "icontains"

                lookup_expr = self.LOOKUP_EXPRESSIONS.get(lookup, "")

                q = Q()
                for field in fields:
                    q |= Q(**{f"{field}{lookup_expr}": value})
                queryset = queryset.filter(q)

                # prevent this key from being used in normal filtering
                filters.pop(incoming_key, None)
        return queryset

    # -----------------------
    # Main filter entry
    # -----------------------
    def filter_queryset(self, request, queryset, view):
        """
        Filter the queryset based on the request parameters.
        """
        try:
            filters = dict(request.filters) if hasattr(request, "filters") else {}
            # grouped filters FIRST
            queryset = self.apply_grouped_filters(queryset, view, filters)

            # normal filters
            filter_kwargs, exclude_kwargs = self.get_basic_filter_kwargs(filters)

            if filter_kwargs:
                queryset = queryset.filter(**filter_kwargs)
            if exclude_kwargs:
                queryset = queryset.exclude(**exclude_kwargs)

            # search()
            search_term = filters.get("search")
            search_fields = getattr(view, "search_fields", [])

            if search_term and search_fields:
                queryset = self.apply_search(queryset, search_term, search_fields)

            return queryset.distinct()

        except (ValueError, ValidationError) as e:
            raise ValidationError(
                {"error": _("Invalid filter parameters: {}").format(str(e))}
            )
