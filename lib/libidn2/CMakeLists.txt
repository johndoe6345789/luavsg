cmake_minimum_required(VERSION 3.20)

# libidn2 CMake overlay
# This overlay is designed to be copied into the libidn2 source tree root.
# It intentionally prefers system dependencies (libunistring, gettext/iconv)
# because the upstream tree vendors autotools-based subprojects (gnulib,
# unistring) that do not natively support CMake.

project(libidn2
  VERSION 2.3.7  # fallback; overridden by cmake/Libidn2Version.cmake if present
  LANGUAGES C
)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}/cmake")

include(GNUInstallDirs)
include(CMakeDependentOption)
include(CheckIncludeFile)
include(CheckSymbolExists)
include(CheckCSourceCompiles)
include(CheckCCompilerFlag)
include(CTest)

option(LIBIDN2_ENABLE_TESTS "Build tests (requires dependencies present)" ON)
option(LIBIDN2_ENABLE_EXAMPLES "Build examples" ON)
option(LIBIDN2_ENABLE_TOOLS "Build command-line tools" ON)
option(LIBIDN2_ENABLE_FUZZ "Build fuzz targets (requires libFuzzer/ASan toolchain)" OFF)
option(LIBIDN2_ENABLE_GTK_DOC "Build documentation with gtk-doc (unsupported by this overlay)" OFF)

# Match autotools defaults: both shared and static possible
option(LIBIDN2_BUILD_SHARED "Build shared library" ON)
option(LIBIDN2_BUILD_STATIC "Build static library" ON)

# Prefer pkg-config for C deps
find_package(PkgConfig REQUIRED)

include(Libidn2Version)
libidn2_detect_version(PROJECT_VERSION_OUT)

if(PROJECT_VERSION_OUT)
  set(PROJECT_VERSION "${PROJECT_VERSION_OUT}")
endif()

# ---- Dependencies ----
# libunistring is required
pkg_check_modules(UNISTRING REQUIRED IMPORTED_TARGET libunistring)

# iconv: may be in libc on glibc, or in libiconv on others (notably Windows)
# We try pkg-config first, then fallback checks.
set(_LIBIDN2_HAVE_ICONV FALSE)
pkg_check_modules(LIBICONV QUIET IMPORTED_TARGET libiconv)

# gettext is used for internationalization in tools; library itself does not
# strictly require it, but idn2 tool and tests might.
pkg_check_modules(GETTEXT QUIET IMPORTED_TARGET gettext)

# ---- Feature checks ----
check_include_file("langinfo.h" HAVE_LANGINFO_H)
check_symbol_exists(nl_langinfo "langinfo.h" HAVE_NL_LANGINFO)
check_symbol_exists(CODESET "langinfo.h" HAVE_CODESET)

# Toolchain supports aliases and .symver?
set(_symver_test_source "
__attribute__((visibility(\"hidden\")))
int versioned_symbol_internal (void) { return 0; }
__typeof__ (versioned_symbol_internal) versioned_symbol
   __attribute__ ((visibility (\"default\"), alias (\"versioned_symbol_internal\")));
__asm__ (\".symver versioned_symbol, versioned_symbol@IDN2_0.0.0\");
int main(void){ return versioned_symbol(); }
")
check_c_source_compiles("${_symver_test_source}" HAVE_SYMVER_ALIAS_SUPPORT)

# Warnings (subset of upstream's manywarnings)
set(LIBIDN2_WARNINGS
  -Wall -Wextra -Wshadow -Wformat=2 -Wstrict-prototypes -Wmissing-prototypes
  -Wpointer-arith -Wcast-qual -Wwrite-strings
)
foreach(flag IN LISTS LIBIDN2_WARNINGS)
  check_c_compiler_flag("${flag}" _ok_${flag})
  if(_ok_${flag})
    add_compile_options("${flag}")
  endif()
endforeach()

# ---- Configure headers ----
set(LIBIDN2_CONFIG_DIR "${CMAKE_CURRENT_BINARY_DIR}/generated")
file(MAKE_DIRECTORY "${LIBIDN2_CONFIG_DIR}")

configure_file(
  "${CMAKE_CURRENT_LIST_DIR}/cmake/config.h.in"
  "${LIBIDN2_CONFIG_DIR}/config.h"
  @ONLY
)

# idn2.h template handling (upstream uses AC_CONFIG_FILES([lib/idn2.h])).
# If lib/idn2.h.in exists, we configure it; otherwise we use the checked-in header.
if(EXISTS "${CMAKE_CURRENT_LIST_DIR}/lib/idn2.h.in")
  configure_file(
    "${CMAKE_CURRENT_LIST_DIR}/lib/idn2.h.in"
    "${LIBIDN2_CONFIG_DIR}/idn2.h"
    @ONLY
  )
  set(LIBIDN2_PUBLIC_HEADER "${LIBIDN2_CONFIG_DIR}/idn2.h")
else()
  set(LIBIDN2_PUBLIC_HEADER "${CMAKE_CURRENT_LIST_DIR}/lib/idn2.h")
endif()

# ---- Subdirectories ----
add_subdirectory(lib)

if(LIBIDN2_ENABLE_TOOLS)
  add_subdirectory(src)
endif()

if(LIBIDN2_ENABLE_EXAMPLES)
  add_subdirectory(examples)
endif()

if(LIBIDN2_ENABLE_TESTS AND BUILD_TESTING)
  add_subdirectory(tests)
endif()

if(LIBIDN2_ENABLE_FUZZ)
  add_subdirectory(fuzz)
endif()

# ---- Install / Export ----
include(CMakePackageConfigHelpers)

set(_pkg_install_dir "${CMAKE_INSTALL_LIBDIR}/cmake/libidn2")
install(
  FILES "${CMAKE_CURRENT_LIST_DIR}/cmake/libidn2Config.cmake.in"
  DESTINATION "${_pkg_install_dir}"
)

configure_package_config_file(
  "${CMAKE_CURRENT_LIST_DIR}/cmake/libidn2Config.cmake.in"
  "${CMAKE_CURRENT_BINARY_DIR}/libidn2Config.cmake"
  INSTALL_DESTINATION "${_pkg_install_dir}"
)

write_basic_package_version_file(
  "${CMAKE_CURRENT_BINARY_DIR}/libidn2ConfigVersion.cmake"
  VERSION "${PROJECT_VERSION}"
  COMPATIBILITY SameMajorVersion
)

install(FILES
  "${CMAKE_CURRENT_BINARY_DIR}/libidn2Config.cmake"
  "${CMAKE_CURRENT_BINARY_DIR}/libidn2ConfigVersion.cmake"
  DESTINATION "${_pkg_install_dir}"
)

install(EXPORT libidn2Targets
  NAMESPACE libidn2::
  DESTINATION "${_pkg_install_dir}"
)

# pkg-config file (optional; only generated if user installs)
include(Libidn2PkgConfig)
libidn2_write_pc_file(
  OUT_FILE "${CMAKE_CURRENT_BINARY_DIR}/libidn2.pc"
  VERSION "${PROJECT_VERSION}"
  INCLUDEDIR "${CMAKE_INSTALL_FULL_INCLUDEDIR}"
  LIBDIR "${CMAKE_INSTALL_FULL_LIBDIR}"
)

install(FILES "${CMAKE_CURRENT_BINARY_DIR}/libidn2.pc"
  DESTINATION "${CMAKE_INSTALL_LIBDIR}/pkgconfig"
)
