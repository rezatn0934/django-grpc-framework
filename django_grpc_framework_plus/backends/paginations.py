from typing import Any, Iterable, Optional

from django.core.exceptions import ValidationError
from django.core.paginator import EmptyPage, PageNotAnInteger
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _


class BasePaginationBackend:
    """
    Base class for gRPC pagination backends.
    Similar to DRF pagination but adapted for gRPC services.
    """

    def paginate_queryset(
        self, queryset: QuerySet, request: Any, view: Any = None
    ) -> Optional[Iterable]:
        """
        Paginate the queryset based on the request parameters.
        Must be overridden by subclasses.
        """
        return queryset

    def get_paginated_response(self, data) -> dict:
        """
        Return a paginated response.
        This method should be overridden by subclasses.
        """
        return data


class PageNumberPagination(BasePaginationBackend):
    """
    Pagination backend using page numbers.
    """

    page_size: int = 10
    page_size_query_param: str = "page_size"
    max_page_size: int = 1000
    page_query_param: str = "page"

    def paginate_queryset(
        self, queryset: QuerySet, request: Any, view: Any = None
    ) -> list:
        self.request = request
        page_size = self.get_page_size(request)
        paginator = self.get_paginator(queryset, page_size)
        page_number = self.get_page_number(request)

        try:
            self.page = paginator.page(page_number)
        except (PageNotAnInteger, EmptyPage) as e:
            raise ValidationError(
                {"error": _("Invalid page number: {}").format(str(e))}
            )

        self.display_page_controls = (
            paginator.num_pages > 1 and self.page.has_other_pages()
        )
        return list(self.page)

    def get_paginated_response(self, data: list) -> dict:
        return {
            "data": data,
            "pagination": {
                "page": str(self.page.number),
                "next_page": (
                    str(self.page.next_page_number()) if self.page.has_next() else ""
                ),
                "previous_page": (
                    str(self.page.previous_page_number())
                    if self.page.has_previous()
                    else ""
                ),
                "total_data_count": str(self.page.paginator.count),
                "total_page_count": str(self.page.paginator.num_pages),
            },
        }

    def get_page_size(self, request: Any) -> int:
        page_size = getattr(request, "filters", {}).get(self.page_size_query_param)
        if page_size is not None:
            try:
                page_size = int(page_size)
                if page_size > 0:
                    return min(page_size, self.max_page_size)
            except (TypeError, ValueError):
                pass
        return self.page_size if self.page_size is not None else 10

    def get_page_number(self, request: Any) -> int:
        page = getattr(request, "filters", {}).get(self.page_query_param)
        if page is not None:
            try:
                return int(page)
            except (TypeError, ValueError):
                pass
        return 1

    def get_paginator(self, queryset, page_size):
        """
        Get the paginator instance.
        """
        from django.core.paginator import Paginator

        return Paginator(queryset, page_size)
