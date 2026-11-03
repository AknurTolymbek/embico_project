"""Compatibility import; implementation lives in app.modules.users.models."""
import sys
from importlib import import_module
sys.modules[__name__] = import_module("app.modules.users.models")
