import account_pb2
from django.contrib.auth.models import User

from django_grpc_framework_plus import proto_serializers


class UserProtoSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = User
        proto_class = account_pb2.User
        fields = ["id", "username", "email", "groups"]
