"""
Settings for gRPC framework are all namespaced in the GRPC_FRAMEWORK setting.

Example usage in settings.py:

GRPC_FRAMEWORK = {
    "ROOT_HANDLERS_HOOK": "project.grpc_handlers",
    "SERVER_INTERCEPTORS": [
        "project.grpc.interceptors.AuthInterceptor",
    ],
    "DEFAULT_PAGINATION_CLASS": "project.grpc.pagination.DefaultPagination",
}

This module provides the `grpc_setting` object, that is used to access
gRPC framework settings, checking for user settings first, then falling
back to the defaults.
"""

from django.conf import settings
from django.test.signals import setting_changed
from django.utils.module_loading import import_string

DEFAULTS = {
    # Root grpc handlers hook configuration
    "ROOT_HANDLERS_HOOK": None,
    # gRPC server configuration
    "SERVER_INTERCEPTORS": None,
    # Pagination
    # Should be a class path or None
    "DEFAULT_PAGINATION_CLASS": None,
}


# List of settings that may be in string import notation.
IMPORT_STRINGS = [
    "ROOT_HANDLERS_HOOK",
    "SERVER_INTERCEPTORS",
    "DEFAULT_PAGINATION_CLASS",
]


def perform_import(val, setting_name):
    """
    If the given setting is a string import notation,
    then perform the necessary import or imports.
    """
    if val is None:
        # ROOT_HANDLERS_HOOK defaults to <ROOT_URLCONF>.grpc_handlers
        if setting_name == "ROOT_HANDLERS_HOOK":
            return import_from_string(
                f"{settings.ROOT_URLCONF}.grpc_handlers",
                setting_name,
            )
        return None

    if isinstance(val, str):
        return import_from_string(val, setting_name)

    if isinstance(val, (list, tuple)):
        return [import_from_string(item, setting_name) for item in val]
    return val


def import_from_string(val, setting_name):
    """
    Attempt to import a class from a string representation.
    """
    try:
        return import_string(val)
    except ImportError as exc:
        raise ImportError(
            "Could not import '%s' for GRPC setting '%s'. %s: %s."
            % (val, setting_name, exc.__class__.__name__, exc)
        ) from exc


class GRPCSettings:
    """
    A settings object that allows gRPC Framework settings to be accessed as
    properties. For example:

        from django_grpc_framework_plus.settings import grpc_settings
        print(grpc_settings.ROOT_HANDLERS_HOOK)

    Any setting with string import paths will be automatically resolved
    and return the class, rather than the string literal.
    """

    def __init__(self, user_settings=None, defaults=None, import_strings=None):
        if user_settings is not None:
            self._user_settings = user_settings
        self.defaults = defaults or DEFAULTS
        self.import_strings = import_strings or IMPORT_STRINGS
        self._cached_attrs = set()

    @property
    def user_settings(self):
        if not hasattr(self, "_user_settings"):
            self._user_settings = getattr(settings, "GRPC_FRAMEWORK", {})
        return self._user_settings

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError(f"Invalid gRPC setting: '{attr}'")

        try:
            # Check if present in user settings
            val = self.user_settings[attr]
        except KeyError:
            # Fall back to defaults
            val = self.defaults[attr]

        # Coerce import strings into classes
        if attr in self.import_strings:
            val = perform_import(val, attr)

        # Cache the result
        self._cached_attrs.add(attr)
        setattr(self, attr, val)
        return val

    def reload(self):
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()
        if hasattr(self, "_user_settings"):
            delattr(self, "_user_settings")


grpc_settings = GRPCSettings(None, DEFAULTS, IMPORT_STRINGS)


def reload_grpc_settings(*args, **kwargs):
    setting = kwargs["setting"]
    if setting == "GRPC_FRAMEWORK" or setting == "ROOT_URLCONF":
        grpc_settings.reload()


setting_changed.connect(reload_grpc_settings)
