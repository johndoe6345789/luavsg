# Examples (best-effort)
file(GLOB _examples CONFIGURE_DEPENDS
  "${CMAKE_CURRENT_LIST_DIR}/*.c"
)

foreach(ex ${_examples})
  get_filename_component(_name "${ex}" NAME_WE)
  add_executable("example_${_name}" "${ex}")
  if(TARGET idn2_shared)
    target_link_libraries("example_${_name}" PRIVATE idn2_shared)
  elseif(TARGET idn2_static)
    target_link_libraries("example_${_name}" PRIVATE idn2_static)
  endif()
  target_include_directories("example_${_name}" PRIVATE "${LIBIDN2_CONFIG_DIR}")
endforeach()
