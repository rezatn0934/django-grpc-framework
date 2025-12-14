import snippets_pb2_grpc
from django.contrib import admin
from django.urls import path
from snippets.services import SnippetService

urlpatterns = [
    path("admin/", admin.site.urls),
]


def grpc_handlers(server):
    snippets_pb2_grpc.add_SnippetControllerServicer_to_server(
        SnippetService.as_servicer(), server
    )
