# -*- coding: utf-8 -*-
"""Parametric Korean Blue-Roof Factory Generator entrypoint.

Usage:
  python blue_factory_cs2.py --out output                  # builds default 'mid' preset
  python blue_factory_cs2.py --preset small --out output   # small | mid | large | depot | all
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from factory_core import PRESETS, build_and_export  # noqa: E402
import cs2kit as K  # noqa: E402


def main():
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--preset", default="mid", choices=list(PRESETS.keys()) + ["all"])
    args, _ = p.parse_known_args()
    out_root = K.out_dir_from_argv("output")
    targets = list(PRESETS.keys()) if args.preset == "all" else [args.preset]
    for key in targets:
        build_and_export(PRESETS[key], out_root=out_root)


if __name__ == "__main__":
    main()
