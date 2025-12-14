"""Minimal pkg-config shim for CMake configure-time discovery.

Implements enough for FindPkgConfig.cmake and common project checks:
  --version
  --exists <pkg>
  --modversion <pkg>
  --cflags <pkg...>
  --libs <pkg...>

Search strategy:
  1) PKG_CONFIG_PATH entries (directories; searched recursively)
  2) <repo>/lib (searched recursively)

This is intentionally minimal and permissive: it is designed to unblock
configuration when vendoring deps.
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


_VERSION = "0.0.0-luavsg"


@dataclass(frozen=True)
class PcFile:
    name: str
    path: Path
    vars: Dict[str, str]
    fields: Dict[str, str]


_VAR_RE = re.compile(r"\$\{([^}]+)\}")


def _split_path_list(raw: str) -> List[Path]:
    if not raw:
        return []
    return [Path(p) for p in raw.split(os.pathsep) if p.strip()]


def _repo_root() -> Path:
    # shim dir is <build>/luavsg_cmake_shims; repo root is CMAKE_SOURCE_DIR
    # passed via env var for robustness.
    env = os.environ.get("LUAVSG_REPO_ROOT", "")
    if env:
        return Path(env)
    return Path.cwd()


def _candidate_roots() -> List[Path]:
    roots: List[Path] = []
    roots.extend(_split_path_list(os.environ.get("PKG_CONFIG_PATH", "")))
    roots.append(_repo_root() / "lib")
    # Common extra pc locations
    roots.append(_repo_root() / "lib" / "zstd_build")
    roots.append(_repo_root() / "lib" / "zstd_build" / "lib")
    return [r for r in roots if r.exists()]


def _find_pc_files(roots: Iterable[Path]) -> Dict[str, Path]:
    out: Dict[str, Path] = {}
    for root in roots:
        try:
            for pc in root.rglob("*.pc"):
                name = pc.stem
                out.setdefault(name, pc)
        except Exception:
            continue
    return out


def _parse_pc(path: Path) -> PcFile:
    vars_: Dict[str, str] = {}
    fields: Dict[str, str] = {}

    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line and not line.split(":", 1)[0].strip().endswith("="):
            k, v = line.split(":", 1)
            fields[k.strip()] = v.strip()
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            vars_[k.strip()] = v.strip()

    name = fields.get("Name", path.stem)
    return PcFile(name=name, path=path, vars=vars_, fields=fields)


def _expand(s: str, vars_: Dict[str, str]) -> str:
    def repl(m: re.Match[str]) -> str:
        key = m.group(1)
        return vars_.get(key, "")

    prev = None
    cur = s
    for _ in range(10):
        if prev == cur:
            break
        prev = cur
        cur = _VAR_RE.sub(repl, cur)
    return cur


def _collect(pkgs: List[str]) -> Tuple[List[str], List[str]]:
    roots = _candidate_roots()
    index = _find_pc_files(roots)

    cflags: List[str] = []
    libs: List[str] = []

    for pkg in pkgs:
        pc_path = index.get(pkg)
        if not pc_path:
            raise FileNotFoundError(pkg)
        pc = _parse_pc(pc_path)
        vars_ = dict(pc.vars)

        # seed a few common vars
        if "pcfiledir" not in vars_:
            vars_["pcfiledir"] = str(pc_path.parent)

        c = pc.fields.get("Cflags", "")
        l = pc.fields.get("Libs", "")
        cflags.extend(_expand(c, vars_).split())
        # Keep this shim conservative: avoid Libs.private by default.
        libs.extend(_expand(l, vars_).split())

    return cflags, libs


def _main(argv: List[str]) -> int:
    if "--version" in argv:
        sys.stdout.write(_VERSION)
        return 0

    # Normalize: FindPkgConfig passes flags first, then pkg names.
    want_exists = "--exists" in argv
    want_mod = "--modversion" in argv
    want_cflags = "--cflags" in argv
    want_libs = "--libs" in argv

    pkgs = [a for a in argv if a and not a.startswith("-")]

    if want_exists or want_mod or want_cflags or want_libs:
        if not pkgs:
            return 1

    roots = _candidate_roots()
    index = _find_pc_files(roots)

    if want_exists:
        for p in pkgs:
            if p not in index:
                return 1
        return 0

    if want_mod:
        p = pkgs[0]
        pc_path = index.get(p)
        if not pc_path:
            return 1
        pc = _parse_pc(pc_path)
        sys.stdout.write(pc.fields.get("Version", "0"))
        return 0

    if want_cflags or want_libs:
        try:
            cflags, libs = _collect(pkgs)
        except FileNotFoundError:
            return 1
        if want_cflags:
            sys.stdout.write(" ".join(cflags))
        elif want_libs:
            sys.stdout.write(" ".join(libs))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
