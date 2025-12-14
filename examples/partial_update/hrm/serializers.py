import hrm_pb2
from hrm.models import Person

from django_grpc_framework_plus import proto_serializers


class PersonProtoSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = Person
        proto_class = hrm_pb2.Person
        fields = "__all__"
