This is a minimal CMake overlay for upstream bzip2 sources.

Drop these files into the root of a bzip2 source tree (next to bzlib.c)
and build with:

  cmake -S . -B build
  cmake --build build
  cmake --install build

Options:
  -DBZIP2_BUILD_TOOLS=ON/OFF
  -DBZIP2_BUILD_TESTS=ON/OFF
  -DBZIP2_INSTALL_PKGCONFIG=ON/OFF
