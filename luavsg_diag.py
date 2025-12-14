#!/usr/bin/env python3
"""luavsg_diag.py

Brute-force, tree-walking CMake dependency diagnostic for a vendored luavsg tree.

Goals:
- Prefer facts from the filesystem over assumptions.
- Quickly answer: "Do I have headers? Do I have built artifacts? Do I have
  *Config.cmake? If yes, what -D<PKG>_DIR should I pass?"

Usage:
  python luavsg_diag.py
  python luavsg_diag.py --repo .
  python luavsg_diag.py --repo . --json

Output is intentionally concise:
- Vulkan status
- Missing headers (by name)
- Missing Config.cmake (by name)
- Suggested -D flags (by name)

Notes:
- Some deps are vendored as source only (no Config.cmake) until you build them.
- Some projects ship a config (e.g. KTX has cmake/KtxConfig.cmake) but the
  headers may live in non-obvious include layouts; this script searches.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator


@dataclass(frozen=True)
class Probe:
    name: str
    header_markers: tuple[str, ...]
    config_markers: tuple[str, ...]


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


def _walk_files(root: Path) -> Iterator[Path]:
    # A fast, brute-force walk. Avoids following symlinks.
    for p in root.rglob("*"):
        if p.is_file():
            yield p


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


def _probes() -> list[Probe]:
    # Markers are *filenames* we look for anywhere under repo/lib.
    # Use multiple markers because different projects use different layouts.
    return [
        Probe(
            name="glslang",
            header_markers=("ShaderLang.h",),
            config_markers=(
                "glslangConfig.cmake",
                "glslang-config.cmake",
            ),
        ),
        Probe(
            name="draco",
            header_markers=("encode.h", "draco_features.h"),
            config_markers=("dracoConfig.cmake", "draco-config.cmake"),
        ),
        Probe(
            name="Ktx",
            header_markers=("ktx.h",),
            config_markers=(
                "KtxConfig.cmake",
                "ktxConfig.cmake",
                "KTXConfig.cmake",
                "ktx-config.cmake",
            ),
        ),
        Probe(
            name="CURL",
            header_markers=("curl.h",),
            config_markers=(
                "CURLConfig.cmake",
                "curlConfig.cmake",
                "curl-config.cmake",
            ),
        ),
        Probe(
            name="Freetype",
            header_markers=("freetype.h",),
            config_markers=(
                "FreetypeConfig.cmake",
                "freetypeConfig.cmake",
                "freetype-config.cmake",
            ),
        ),
    ]


def _index_tree(repo: Path) -> tuple[dict[str, list[Path]], dict[str, list[Path]]]:
    # Returns (headers_by_basename, configs_by_basename)
    lib_root = repo / "lib"
    headers: dict[str, list[Path]] = {}
    configs: dict[str, list[Path]] = {}

    if not lib_root.exists():
        return headers, configs

    for f in _walk_files(lib_root):
        name = f.name
        low = name.lower()

        # Header-ish: .h / .hpp
        if low.endswith((".h", ".hpp")):
            headers.setdefault(name, []).append(f)

        # CMake configs: *Config.cmake or *-config.cmake
        if low.endswith("config.cmake") or low.endswith("-config.cmake"):
            configs.setdefault(name, []).append(f)

    # Deterministic ordering
    for d in (headers, configs):
        for k in list(d.keys()):
            d[k] = sorted(_dedupe(d[k]))

    return headers, configs


def _pick_best_config(paths: list[Path]) -> Path | None:
    if not paths:
        return None

    # Prefer x64-ish locations; avoid ARM64 unless that's all we have.
    def score(p: Path) -> tuple[int, int]:
        s = p.as_posix().lower()
        bad = 1 if "arm64" in s else 0
        good = 1 if ("/lib/" in s or "/cmake/" in s) else 0
        # Lower bad is better; higher good is better.
        return (bad, -good)

    return sorted(paths, key=score)[0]


def _flag(pkg: str, config_file: Path) -> str:
    return f"-D{pkg}_DIR=\"{config_file.parent.as_posix()}\""


def diagnose(repo: Path) -> dict[str, object]:
    sdk = _vulkan_sdk(repo)
    vk_h = sdk / "Include" / "vulkan" / "vulkan.h" if sdk else None
    vk_lib = _first_existing(_vk_libs(sdk)) if sdk else None

    hdr_index, cfg_index = _index_tree(repo)

    header_hits: dict[str, list[str]] = {}
    config_hits: dict[str, list[str]] = {}
    suggested_flags: dict[str, str] = {}
    missing_headers: dict[str, str] = {}
    missing_configs: list[str] = []

    for pr in _probes():
        # Header: consider "present" if any marker basename exists anywhere.
        pr_hdr_paths: list[Path] = []
        for m in pr.header_markers:
            pr_hdr_paths.extend(hdr_index.get(m, []))
        pr_hdr_paths = _dedupe(pr_hdr_paths)
        header_hits[pr.name] = [p.as_posix() for p in pr_hdr_paths]
        if not pr_hdr_paths:
            missing_headers[pr.name] = ", ".join(pr.header_markers)

        # Config: pick best config file among marker basenames.
        pr_cfg_paths: list[Path] = []
        for m in pr.config_markers:
            pr_cfg_paths.extend(cfg_index.get(m, []))
        pr_cfg_paths = _dedupe(pr_cfg_paths)
        config_hits[pr.name] = [p.as_posix() for p in pr_cfg_paths]

        best = _pick_best_config(pr_cfg_paths)
        if best is None:
            missing_configs.append(pr.name)
        else:
            suggested_flags[pr.name] = _flag(pr.name, best)

    return {
        "repo": repo.as_posix(),
        "platform": "windows" if _is_win() else os.name,
        "vulkan_sdk": sdk.as_posix() if sdk else None,
        "vulkan_h": vk_h.as_posix() if vk_h and vk_h.exists() else None,
        "vulkan_1_lib": vk_lib.as_posix() if vk_lib else None,
        "header_hits": header_hits,
        "config_hits": config_hits,
        "missing_headers": missing_headers,
        "missing_configs": sorted(missing_configs),
        "suggested_flags": {k: suggested_flags[k] for k in sorted(suggested_flags)},
    }


def _print(report: dict[str, object]) -> None:
    print(f"repo: {report['repo']}")
    print(f"platform: {report['platform']}")
    print(f"VULKAN_SDK: {report['vulkan_sdk'] or 'MISSING'}")
    print(f"vulkan.h: {report['vulkan_h'] or 'MISSING'}")
    print(f"vulkan-1.lib: {report['vulkan_1_lib'] or 'MISSING'}")

    miss_h: dict[str, str] = report["missing_headers"]
    miss_c: list[str] = report["missing_configs"]

    if miss_h:
        print("\nmissing headers (no basename match found under repo/lib):")
        for k in sorted(miss_h):
            print(f"  - {k}: {miss_h[k]}")

    if miss_c:
        print("\nmissing Config.cmake (no config file found under repo/lib):")
        for k in miss_c:
            print(f"  - {k}")

    flags: dict[str, str] = report["suggested_flags"]
    if flags:
        print("\nsuggested -D flags:")
        for k in sorted(flags):
            print(f"  {flags[k]}")


def main() -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--json", action="store_true")
    ap.add_argument(
        "--show-hits",
        action="store_true",
        help="Also print the first few filesystem hits per package",
    )
    args = ap.parse_args()

    repo = Path(args.repo).expanduser().resolve()
    if not repo.exists():
        raise SystemExit(f"repo not found: {repo}")

    report = diagnose(repo)

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    _print(report)

    if args.show_hits:
        print("\n(hits)")
        hh: dict[str, list[str]] = report["header_hits"]
        ch: dict[str, list[str]] = report["config_hits"]
        for pkg in sorted(hh):
            print(f"\n[{pkg}] headers:")
            for p in hh[pkg][:5]:
                print(f"  {p}")
            if len(hh[pkg]) > 5:
                print(f"  ... ({len(hh[pkg]) - 5} more)")

            print(f"[{pkg}] configs:")
            for p in ch[pkg][:5]:
                print(f"  {p}")
            if len(ch[pkg]) > 5:
                print(f"  ... ({len(ch[pkg]) - 5} more)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
