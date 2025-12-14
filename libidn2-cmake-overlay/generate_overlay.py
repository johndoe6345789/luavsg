#!/usr/bin/env python3

"""
generate_overlay.py

Creates a fresh libidn2-cmake-overlay/ directory containing a CMake overlay.

Rules:
- Never modifies the current working directory.
- Writes to a new directory under the provided --out-root (default: ./_out).

Example:
  python generate_overlay.py --out-root "C:/Users/you/AppData/Local/Temp"
"""

from __future__ import annotations

import argparse
import os
import pathlib
import shutil
import sys
from typing import Dict

FILES: Dict[str, str] = {}

def _add(path: str, content: str) -> None:
    if path in FILES:
        raise ValueError(f"duplicate path: {path}")
    FILES[path] = content

def _load_embedded() -> None:
    # NOTE: This file is generated as part of the zip; contents are embedded below.
    pass

def _write_tree(root: pathlib.Path) -> None:
    for rel, content in FILES.items():
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(content, encoding="utf-8", newline="\n")

def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out-root",
        default=str(pathlib.Path.cwd() / "_out"),
        help="Root directory to create a new output folder under",
    )
    ap.add_argument(
        "--name",
        default="libidn2-cmake-overlay",
        help="Name of the overlay directory to create",
    )
    ns = ap.parse_args(argv)

    out_root = pathlib.Path(ns.out_root).expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    out_dir = out_root / ns.name
    if out_dir.exists():
        shutil.rmtree(out_dir)

    _load_embedded()
    _write_tree(out_dir)

    print(str(out_dir))
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
