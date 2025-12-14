from django.db import close_old_connections, reset_queries
from django.dispatch import Signal

grpc_request_started = Signal()
grpc_request_finished = Signal()


# db connection state managed similarly to the wsgi handler
grpc_request_started.connect(reset_queries)
grpc_request_started.connect(close_old_connections)
grpc_request_finished.connect(close_old_connections)
