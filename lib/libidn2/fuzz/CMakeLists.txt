# Fuzz targets (best-effort; requires a libFuzzer-capable toolchain)
file(GLOB _fuzz CONFIGURE_DEPENDS
  "${CMAKE_CURRENT_LIST_DIR}/*fuzz*.c"
)

if(NOT _fuzz)
  message(STATUS "No fuzz sources detected")
  return()
endif()

foreach(f ${_fuzz})
  get_filename_component(_name "${f}" NAME_WE)
  add_executable("${_name}" "${f}")
  if(TARGET idn2_shared)
    target_link_libraries("${_name}" PRIVATE idn2_shared)
  elseif(TARGET idn2_static)
    target_link_libraries("${_name}" PRIVATE idn2_static)
  endif()
  target_include_directories("${_name}" PRIVATE "${LIBIDN2_CONFIG_DIR}")
  target_compile_options("${_name}" PRIVATE -fsanitize=fuzzer,address,undefined)
  target_link_options("${_name}" PRIVATE -fsanitize=fuzzer,address,undefined)
endforeach()
