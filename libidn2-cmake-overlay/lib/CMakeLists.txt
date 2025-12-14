# Build libidn2 library

file(GLOB LIBIDN2_SOURCES CONFIGURE_DEPENDS
  "${CMAKE_CURRENT_LIST_DIR}/*.c"
)

# Some upstream dirs contain helper sources; we include only this directory by default.
# If the upstream layout differs, set LIBIDN2_EXTRA_SOURCES from the parent project.
set(LIBIDN2_EXTRA_SOURCES "" CACHE STRING "Additional libidn2 sources (semicolon-separated)")
if(LIBIDN2_EXTRA_SOURCES)
  list(APPEND LIBIDN2_SOURCES ${LIBIDN2_EXTRA_SOURCES})
endif()

# Public header: configured or checked-in
set(LIBIDN2_PUBLIC_HEADER "${LIBIDN2_PUBLIC_HEADER}")

set(_common_includes
  "${LIBIDN2_CONFIG_DIR}"
  "${CMAKE_CURRENT_LIST_DIR}"
)

set(_common_libs
  PkgConfig::UNISTRING
)

# iconv linkage (optional)
if(TARGET PkgConfig::LIBICONV)
  list(APPEND _common_libs PkgConfig::LIBICONV)
endif()

# Shared
if(LIBIDN2_BUILD_SHARED)
  add_library(idn2_shared SHARED ${LIBIDN2_SOURCES})
  set_target_properties(idn2_shared PROPERTIES
    OUTPUT_NAME idn2
    VERSION "${PROJECT_VERSION}"
    SOVERSION "0"
    PUBLIC_HEADER "${LIBIDN2_PUBLIC_HEADER}"
  )
  target_include_directories(idn2_shared
    PUBLIC
      $<BUILD_INTERFACE:${_common_includes}>
      $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
  )
  target_link_libraries(idn2_shared PUBLIC ${_common_libs})
  target_compile_definitions(idn2_shared PRIVATE HAVE_CONFIG_H=1)
  install(TARGETS idn2_shared
    EXPORT libidn2Targets
    RUNTIME DESTINATION "${CMAKE_INSTALL_BINDIR}"
    LIBRARY DESTINATION "${CMAKE_INSTALL_LIBDIR}"
    ARCHIVE DESTINATION "${CMAKE_INSTALL_LIBDIR}"
    PUBLIC_HEADER DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}"
  )
  add_library(libidn2::idn2 ALIAS idn2_shared)
endif()

# Static
if(LIBIDN2_BUILD_STATIC)
  add_library(idn2_static STATIC ${LIBIDN2_SOURCES})
  set_target_properties(idn2_static PROPERTIES
    OUTPUT_NAME idn2
    POSITION_INDEPENDENT_CODE ON
    PUBLIC_HEADER "${LIBIDN2_PUBLIC_HEADER}"
  )
  target_include_directories(idn2_static
    PUBLIC
      $<BUILD_INTERFACE:${_common_includes}>
      $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
  )
  target_link_libraries(idn2_static PUBLIC ${_common_libs})
  target_compile_definitions(idn2_static PRIVATE HAVE_CONFIG_H=1)
  install(TARGETS idn2_static
    EXPORT libidn2Targets
    ARCHIVE DESTINATION "${CMAKE_INSTALL_LIBDIR}"
    PUBLIC_HEADER DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}"
  )
endif()
