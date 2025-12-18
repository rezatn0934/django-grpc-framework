from google.protobuf import empty_pb2

from django_grpc_framework_plus.protobuf.json_format import parse_dict


class CreateModelMixin:
    def Create(self, request, context):
        """
        Create a model instance.

        The request should be a proto message of ``serializer.Meta.proto_class``.
        If an object is created this returns a proto message of
        ``serializer.Meta.proto_class``.
        """
        serializer = self.get_serializer(message=request)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return serializer.message

    def perform_create(self, serializer):
        """Save a new object instance."""
        serializer.save()


class ListModelMixin:
    def List(self, request, context):
        """
        List a queryset.  This sends a sequence of messages of
        ``serializer.Meta.proto_class`` to the client.

        .. note::

            This is a server streaming RPC.
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        for message in serializer.message:
            yield message


class PaginatedListModelMixin:
    """
    Mixin to provide paginated list responses for ViewSets, returning data as Protobuf messages.

    This mixin assumes the serializer's Meta class defines `list_proto_class` pointing
    to the corresponding Protobuf message for list responses.

    Methods
    -------
        PaginatedList(request, context)
            Returns a paginated list of serialized objects converted to a Protobuf message.

        _get_list_response_proto(serializer)
            Retrieves the Protobuf message class for the list response from the serializer's Meta.
    """

    def PaginatedList(self, request, context):
        """
        Return a paginated list response for the given request.

        Parameters
        ----------
            request : object
                The incoming request object (e.g., gRPC context or HTTP request).
            context : dict
                Context dictionary to pass additional information to the serializer.

        Returns
        -------
            ProtobufMessage
                The paginated response converted into a Protobuf message.

        Raises
        ------
            RuntimeError
                If the serializer's Meta class does not define `list_proto_class`.
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        serializer = self.get_serializer(page or queryset, many=True)

        payload = (
            self.get_paginated_response(serializer.data)
            if page is not None
            else serializer.data
        )

        response_proto = self._get_list_response_proto(serializer)
        return parse_dict(payload, response_proto)

    def _get_list_response_proto(self, serializer):
        """
        Retrieve the Protobuf message class for list responses from the serializer.

        Parameters
        ----------
            serializer : Serializer
            A serializer instance (or ListSerializer) used for the response.

        Returns
        -------
            ProtobufMessage
            An instance of the Protobuf message class for the list response.

        Raises
        ------
            RuntimeError
            If the serializer's Meta does not define `list_proto_class`.
        """
        child = serializer.child
        try:
            return child.Meta.list_proto_class()
        except AttributeError:
            raise RuntimeError(
                "List serializer Meta must define `list_proto_class` "
                "pointing to the List response proto message."
            )


class RetrieveModelMixin:
    def Retrieve(self, request, context):
        """
        Retrieve a model instance.

        The request have to include a field corresponding to
        ``lookup_request_field``.  If an object can be retrieved this returns
        a proto message of ``serializer.Meta.proto_class``.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return serializer.message


class UpdateModelMixin:
    def Update(self, request, context):
        """
        Update a model instance.

        The request should be a proto message of ``serializer.Meta.proto_class``.
        If an object is updated this returns a proto message of
        ``serializer.Meta.proto_class``.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, message=request)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return serializer.message

    def perform_update(self, serializer):
        """Save an existing object instance."""
        serializer.save()


class PartialUpdateModelMixin:
    def PartialUpdate(self, request, context):
        """
        Partial update a model instance.

        The request have to include a field corresponding to
        ``lookup_request_field`` and you need to explicitly set the fields that
        you want to update.  If an object is updated this returns a proto
        message of ``serializer.Meta.proto_class``.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, message=request, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_partial_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return serializer.message

    def perform_partial_update(self, serializer):
        """Save an existing object instance."""
        serializer.save()


class DestroyModelMixin:
    def Destroy(self, request, context):
        """
        Destroy a model instance.

        The request have to include a field corresponding to
        ``lookup_request_field``.  If an object is deleted this returns
        a proto message of ``google.protobuf.empty_pb2.Empty``.
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        return empty_pb2.Empty()

    def perform_destroy(self, instance):
        """Delete an object instance."""
        instance.delete()
