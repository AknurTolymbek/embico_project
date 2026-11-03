"""Compatibility import; implementation lives in app.modules.ml.inference.blastocyst."""
import sys
from importlib import import_module
sys.modules[__name__] = import_module("app.modules.ml.inference.blastocyst")
