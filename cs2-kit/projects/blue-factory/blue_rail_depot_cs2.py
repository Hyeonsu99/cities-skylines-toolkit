# -*- coding: utf-8 -*-
"""Preset wrapper: Korean Blue-Roof Rail Maintenance Depot (4x8 lot)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from factory_core import PRESETS, build_and_export  # noqa: E402

if __name__ == "__main__":
    build_and_export(PRESETS["depot"])
