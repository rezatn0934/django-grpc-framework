Django gRPC Framework Plus
==========================

.. image:: https://img.shields.io/pypi/v/django-grpc-framework-plus.svg
   :target: https://pypi.org/project/django-grpc-framework-plus/

.. image:: https://readthedocs.org/projects/django-grpc-framework-plus/badge/?version=latest
   :target: https://django-grpc-framework-plus.readthedocs.io/en/latest/

.. image:: https://img.shields.io/pypi/pyversions/django-grpc-framework-plus
   :target: https://pypi.org/project/django-grpc-framework-plus/

.. image:: https://img.shields.io/pypi/l/django-grpc-framework-plus
   :target: https://pypi.org/project/django-grpc-framework-plus/


⚠️ **Note:** Django gRPC Framework Plus is a **fork** of
[Django gRPC Framework](https://github.com/fengsp/django-grpc-framework)
with additional features such as advanced filtering for gRPC.
Some new features may be experimental and documentation may be incomplete.

Overview
--------

**Django gRPC Framework Plus** allows building gRPC services in Django while providing better support for client-server interactions.

### Additional Features

- Advanced gRPC filtering support (**experimental**)
- Pagination support for gRPC responses
- Extended authentication options
- Client-focused enhancements

Requirements
------------

- Python (3.6, 3.7, 3.8, 3.9, 3.10)
- Django (2.2, 3.x), Django REST Framework (3.10.x, 3.11.x)
- gRPC, gRPC tools, proto3

Installation
------------

.. code-block:: bash

    $ pip install django-grpc-framework-plus

Add ``django_grpc_framework_plus`` to your ``INSTALLED_APPS``:

.. code-block:: python

    INSTALLED_APPS = [
        ...
        'django_grpc_framework_plus',
    ]

Demo
----

Create a new Django project:

.. code-block:: bash

    $ django-admin startproject demo
    $ python manage.py migrate

Generate a `.proto` file (`demo.proto`):

.. code-block:: bash

    $ python manage.py generateproto --model django.contrib.auth.models.User --fields id,username,email --file demo.proto

Generate gRPC code:

.. code-block:: bash

    $ python -m grpc_tools.protoc --proto_path=./ --python_out=./ --grpc_python_out=./ ./demo.proto

Edit `demo/urls.py`:

.. code-block:: python

    from django.contrib.auth.models import User
    from django_grpc_framework_plus import generics, proto_serializers
    import demo_pb2
    import demo_pb2_grpc

    class UserProtoSerializer(proto_serializers.ModelProtoSerializer):
        class Meta:
            model = User
            proto_class = demo_pb2.User
            fields = ['id', 'username', 'email']

    class UserService(generics.ModelService):
        queryset = User.objects.all()
        serializer_class = UserProtoSerializer

    urlpatterns = []

    def grpc_handlers(server):
        demo_pb2_grpc.add_UserControllerServicer_to_server(UserService.as_servicer(), server)

Run the gRPC server:

.. code-block:: bash

    $ python manage.py grpcrunserver --dev

Run a gRPC client:

.. code-block:: python

    import grpc
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = demo_pb2_grpc.UserControllerStub(channel)
        for user in stub.List(demo_pb2.UserListRequest()):
            print(user, end='')

.. note::

    The gRPC filtering feature is experimental. The API may change in future releases.

Release Notes
-------------

- Fork of Django gRPC Framework
- Added experimental gRPC filtering, pagination, and client-focused enhancements
- Some features are experimental and may be updated in future releases
