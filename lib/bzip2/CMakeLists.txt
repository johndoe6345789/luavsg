cmake_minimum_required(VERSION 3.20)

# CMake build for upstream bzip2 sources (overlay).
# Intended to be dropped into an existing bzip2 source tree.

project(bzip2
  VERSION 1.0.8
  LANGUAGES C
)

include(GNUInstallDirs)
include(CMakePackageConfigHelpers)

option(BZIP2_BUILD_TOOLS "Build bzip2 command line tools" ON)
option(BZIP2_BUILD_TESTS "Build bzip2 tests (dlltest)" OFF)

set(BZIP2_PUBLIC_HEADERS
  bzlib.h
)

set(BZIP2_SOURCES
  blocksort.c
  huffman.c
  crctable.c
  randtable.c
  compress.c
  decompress.c
  bzlib.c
)

add_library(bz2 ${BZIP2_SOURCES})
add_library(BZip2::BZip2 ALIAS bz2)

target_include_directories(bz2
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
    $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
)

target_compile_definitions(bz2
  PRIVATE
    # Keep consistent with many downstream builds
    _FILE_OFFSET_BITS=64
)

# Export symbols on Windows when building shared library.
if(WIN32 AND BUILD_SHARED_LIBS)
  if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/libbz2.def")
    target_sources(bz2 PRIVATE libbz2.def)
    set_target_properties(bz2 PROPERTIES LINK_FLAGS "/DEF:${CMAKE_CURRENT_SOURCE_DIR}/libbz2.def")
  else()
    set_target_properties(bz2 PROPERTIES WINDOWS_EXPORT_ALL_SYMBOLS ON)
  endif()
endif()

set_target_properties(bz2 PROPERTIES
  OUTPUT_NAME bz2
  VERSION ${PROJECT_VERSION}
  SOVERSION 1
)

# Tools
if(BZIP2_BUILD_TOOLS)
  add_executable(bzip2 bzip2.c)
  target_link_libraries(bzip2 PRIVATE bz2)

  add_executable(bzip2recover bzip2recover.c)

  # Upstream uses bzip2 as the install name; provide a consistent layout.
  install(TARGETS bzip2 bzip2recover
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
  )
endif()

# Basic smoke test binary from upstream (optional)
if(BZIP2_BUILD_TESTS)
  add_executable(dlltest dlltest.c)
  target_link_libraries(dlltest PRIVATE bz2)
endif()

# Install library + headers
install(TARGETS bz2
  EXPORT bzip2Targets
  ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
  LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
  RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
  INCLUDES DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
)

install(FILES ${BZIP2_PUBLIC_HEADERS}
  DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
)

# Package config
set(BZIP2_INSTALL_CMAKEDIR "${CMAKE_INSTALL_LIBDIR}/cmake/bzip2")

configure_package_config_file(
  "${CMAKE_CURRENT_LIST_DIR}/cmake/bzip2Config.cmake.in"
  "${CMAKE_CURRENT_BINARY_DIR}/bzip2Config.cmake"
  INSTALL_DESTINATION "${BZIP2_INSTALL_CMAKEDIR}"
)

write_basic_package_version_file(
  "${CMAKE_CURRENT_BINARY_DIR}/bzip2ConfigVersion.cmake"
  VERSION ${PROJECT_VERSION}
  COMPATIBILITY SameMajorVersion
)

install(EXPORT bzip2Targets
  NAMESPACE BZip2::
  FILE bzip2Targets.cmake
  DESTINATION "${BZIP2_INSTALL_CMAKEDIR}"
)

install(FILES
  "${CMAKE_CURRENT_BINARY_DIR}/bzip2Config.cmake"
  "${CMAKE_CURRENT_BINARY_DIR}/bzip2ConfigVersion.cmake"
  DESTINATION "${BZIP2_INSTALL_CMAKEDIR}"
)

# Provide pkg-config file if desired (off by default to avoid clashing with upstream makefiles)
option(BZIP2_INSTALL_PKGCONFIG "Install bzip2 pkg-config file" OFF)
if(BZIP2_INSTALL_PKGCONFIG)
  configure_file(
    "${CMAKE_CURRENT_LIST_DIR}/cmake/bzip2.pc.in"
    "${CMAKE_CURRENT_BINARY_DIR}/bzip2.pc"
    @ONLY
  )
  install(FILES "${CMAKE_CURRENT_BINARY_DIR}/bzip2.pc"
    DESTINATION "${CMAKE_INSTALL_LIBDIR}/pkgconfig"
  )
endif()
