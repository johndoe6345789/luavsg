#!/usr/bin/env python3
"""luavsg_diag.py

Concise CMake dependency diagnostic for a vendored luavsg tree.

Usage:
  python luavsg_diag.py
  python luavsg_diag.py --repo .
  python luavsg_diag.py --json

What it does:
- Detects vendored VulkanSDK and checks vulkan.h + vulkan-1.lib.
- Checks for key headers in vendored dependency source trees.
- Searches for *Config.cmake files to suggest -D<PKG>_DIR flags.
- Prints only the essentials (missing items + suggested flags).

Notes:
- A "header present" but "Config.cmake missing" usually means "source only";
  that dependency still needs to be built/installed (or the plugin disabled).
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Pkg:
    name: str
    roots: tuple[Path, ...]
    patterns: tuple[str, ...]


def _is_win() -> bool:
    return os.name == "nt"


def _dedupe(paths: Iterable[Path]) -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for p in paths:
        r = p.resolve()
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


def _glob_any(roots: Iterable[Path], pats: Iterable[str]) -> list[Path]:
    hits: list[Path] = []
    for r in roots:
        if r.exists():
            for pat in pats:
                hits.extend(r.glob(pat))
    return _dedupe(sorted(hits))


def _vendored_latest(dirpath: Path) -> Path | None:
    if not dirpath.exists():
        return None
    kids = sorted([p for p in dirpath.iterdir() if p.is_dir()])
    return kids[-1] if kids else None


def _vulkan_sdk(repo: Path) -> Path | None:
    env = os.environ.get("VULKAN_SDK", "").strip()
    if env:
        p = Path(env)
        return p if p.exists() else None
    return _vendored_latest(repo / "lib" / "VulkanSDK")


def _vk_libs(sdk: Path) -> list[Path]:
    if not _is_win():
        return []
    return [
        sdk / "Lib" / "vulkan-1.lib",
        sdk / "Lib" / "x64" / "vulkan-1.lib",
        sdk / "Lib-ARM64" / "vulkan-1.lib",
        sdk / "Lib-ARM64" / "arm64" / "vulkan-1.lib",
    ]


def _first_existing(paths: Iterable[Path]) -> Path | None:
    for p in paths:
        if p.exists():
            return p
    return None


def _pkgs(repo: Path) -> list[Pkg]:
    return [
        Pkg(
            "glslang",
            (repo / "lib" / "glslang", repo / "lib"),
            (
                "**/glslangConfig.cmake",
                "**/glslang-config.cmake",
                "**/glslangConfigVersion.cmake",
            ),
        ),
        Pkg(
            "draco",
            (repo / "lib" / "draco", repo / "lib"),
            ("**/dracoConfig.cmake", "**/draco-config.cmake"),
        ),
        Pkg(
            "Ktx",
            (repo / "lib" / "KTX", repo / "lib"),
            (
                "**/KtxConfig.cmake",
                "**/ktx-config.cmake",
                "**/ktxConfig.cmake",
                "**/KTXConfig.cmake",
            ),
        ),
        Pkg(
            "CURL",
            (repo / "lib" / "curl", repo / "lib"),
            ("**/CURLConfig.cmake", "**/curlConfig.cmake", "**/curl-config.cmake"),
        ),
        Pkg(
            "Freetype",
            (repo / "lib" / "freetype", repo / "lib"),
            (
                "**/FreetypeConfig.cmake",
                "**/freetypeConfig.cmake",
                "**/freetype-config.cmake",
            ),
        ),
    ]


def _headers(repo: Path) -> dict[str, Path]:
    return {
        "glslang": repo / "lib" / "glslang" / "glslang" / "Public" / "ShaderLang.h",
        "draco": repo / "lib" / "draco" / "src" / "draco" / "compression" / "encode.h",
        "freetype": repo / "lib" / "freetype" / "include" / "freetype" / "freetype.h",
        "KTX": repo / "lib" / "KTX" / "include" / "KHR" / "ktx.h",
        "curl": repo / "lib" / "curl" / "include" / "curl" / "curl.h",
    }


def _flag(pkg: str, config: Path) -> str:
    return f"-D{pkg}_DIR=\"{config.parent.as_posix()}\""


def diagnose(repo: Path) -> dict[str, object]:
    sdk = _vulkan_sdk(repo)
    vk_h = sdk / "Include" / "vulkan" / "vulkan.h" if sdk else None
    vk_lib = _first_existing(_vk_libs(sdk)) if sdk else None

    header_map = _headers(repo)
    headers_ok = {k: v.as_posix() for k, v in header_map.items() if v.exists()}
    headers_missing = {k: v.as_posix() for k, v in header_map.items() if not v.exists()}

    configs: dict[str, list[str]] = {}
    flags: dict[str, str] = {}
    missing_cfg: list[str] = []

    for pkg in _pkgs(repo):
        hits = _glob_any(pkg.roots, pkg.patterns)
        configs[pkg.name] = [h.as_posix() for h in hits]
        if hits:
            flags[pkg.name] = _flag(pkg.name, hits[0])
        else:
            missing_cfg.append(pkg.name)

    return {
        "repo": repo.as_posix(),
        "platform": "windows" if _is_win() else os.name,
        "vulkan_sdk": sdk.as_posix() if sdk else None,
        "vulkan_h": vk_h.as_posix() if vk_h and vk_h.exists() else None,
        "vulkan_1_lib": vk_lib.as_posix() if vk_lib else None,
        "headers_ok": headers_ok,
        "headers_missing": headers_missing,
        "configs": configs,
        "missing_configs": missing_cfg,
        "suggest_flags": flags,
    }


def _print(report: dict[str, object]) -> None:
    print(f"repo: {report['repo']}")
    print(f"platform: {report['platform']}")
    print(f"VULKAN_SDK: {report['vulkan_sdk'] or 'MISSING'}")
    print(f"vulkan.h: {report['vulkan_h'] or 'MISSING'}")
    print(f"vulkan-1.lib: {report['vulkan_1_lib'] or 'MISSING'}")

    miss_h = report["headers_missing"]
    miss_c = report["missing_configs"]

    if miss_h:
        print("\nmissing headers:")
        for k, v in miss_h.items():
            print(f"  - {k}: {v}")

    if miss_c:
        print("\nmissing Config.cmake:")
        for k in miss_c:
            print(f"  - {k}")

    flags = report["suggest_flags"]
    if flags:
        print("\nsuggested -D flags:")
        for k in sorted(flags.keys()):
            print(f"  {flags[k]}")


def main() -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo).expanduser().resolve()
    if not repo.exists():
        raise SystemExit(f"repo not found: {repo}")

    report = diagnose(repo)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        _print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
