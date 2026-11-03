"""Compatibility import; implementation lives in app.modules.patients.router."""
import sys
from importlib import import_module
sys.modules[__name__] = import_module("app.modules.patients.router")
