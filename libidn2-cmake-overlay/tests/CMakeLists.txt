# Tests (best-effort)
# Upstream uses Automake test harness; here we build any *test*.c sources.
file(GLOB _tests CONFIGURE_DEPENDS
  "${CMAKE_CURRENT_LIST_DIR}/*.c"
)

foreach(t ${_tests})
  get_filename_component(_name "${t}" NAME_WE)
  add_executable("${_name}" "${t}")
  if(TARGET idn2_shared)
    target_link_libraries("${_name}" PRIVATE idn2_shared)
  elseif(TARGET idn2_static)
    target_link_libraries("${_name}" PRIVATE idn2_static)
  endif()
  target_include_directories("${_name}" PRIVATE "${LIBIDN2_CONFIG_DIR}")
  add_test(NAME "${_name}" COMMAND "${_name}")
endforeach()
