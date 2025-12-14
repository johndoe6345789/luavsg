# Command-line tools
# Upstream tool sources are in src/. This overlay builds binaries if present.

file(GLOB _src_tools CONFIGURE_DEPENDS
  "${CMAKE_CURRENT_LIST_DIR}/*.c"
)

# Heuristic: build a single 'idn2' tool if idn2.c exists; otherwise skip.
if(EXISTS "${CMAKE_CURRENT_LIST_DIR}/idn2.c")
  add_executable(idn2 "${CMAKE_CURRENT_LIST_DIR}/idn2.c")
  if(TARGET idn2_shared)
    target_link_libraries(idn2 PRIVATE idn2_shared)
  elseif(TARGET idn2_static)
    target_link_libraries(idn2 PRIVATE idn2_static)
  else()
    message(FATAL_ERROR "No libidn2 library target available")
  endif()

  target_include_directories(idn2 PRIVATE "${LIBIDN2_CONFIG_DIR}")

  # gettext for i18n if available
  if(TARGET PkgConfig::GETTEXT)
    target_link_libraries(idn2 PRIVATE PkgConfig::GETTEXT)
  endif()

  install(TARGETS idn2 RUNTIME DESTINATION "${CMAKE_INSTALL_BINDIR}")
endif()
