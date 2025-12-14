from account.serializers import UserProtoSerializer
from django.contrib.auth.models import User

from django_grpc_framework_plus import generics


class UserService(generics.ModelService):
    """
    gRPC service that allows users to be retrieved or updated.
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserProtoSerializer
