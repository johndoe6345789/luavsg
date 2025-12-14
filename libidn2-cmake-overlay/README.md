libidn2 CMake overlay
====================

This is a *non-upstream* CMake build overlay intended for older/autotools-only
libidn2 source trees.

Key points
----------
- Prefers *system* dependencies via pkg-config:
  - libunistring (required)
  - libiconv (optional)
  - gettext (optional; tools/tests)
- Generates a minimal config.h and (if present) configures lib/idn2.h.in.

Usage (copy into libidn2 repo)
------------------------------
1) Copy these files into the *root* of the libidn2 source tree (alongside
   configure.ac / Makefile.am).
2) Configure/build:

   cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
   cmake --build build
   ctest --test-dir build

Notes
-----
- Upstream's vendored gnulib/unistring directories are not built by this overlay.
- If your lib sources live outside lib/*.c, set:
  -DLIBIDN2_EXTRA_SOURCES="path/to/file1.c;path/to/file2.c"

