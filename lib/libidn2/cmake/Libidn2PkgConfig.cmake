include_guard(GLOBAL)

function(libidn2_write_pc_file)
  set(options)
  set(oneValueArgs OUT_FILE VERSION INCLUDEDIR LIBDIR)
  set(multiValueArgs)
  cmake_parse_arguments(PC "${options}" "${oneValueArgs}"
    "${multiValueArgs}" ${ARGN})

  if(NOT PC_OUT_FILE)
    message(FATAL_ERROR "libidn2_write_pc_file: OUT_FILE is required")
  endif()

  # Using pkg-config requires and libs consistent with our imported deps.
  set(_requires "libunistring")
  set(_libs "-L${PC_LIBDIR} -lidn2")
  set(_cflags "-I${PC_INCLUDEDIR}")

  file(WRITE "${PC_OUT_FILE}" "prefix=@prefix@\n")
  file(APPEND "${PC_OUT_FILE}" "exec_prefix=${prefix}\n")
  file(APPEND "${PC_OUT_FILE}" "libdir=${prefix}/${CMAKE_INSTALL_LIBDIR}\n")
  file(APPEND "${PC_OUT_FILE}" "includedir=${prefix}/${CMAKE_INSTALL_INCLUDEDIR}\n\n")
  file(APPEND "${PC_OUT_FILE}" "Name: libidn2\n")
  file(APPEND "${PC_OUT_FILE}" "Description: Internationalized Domain Names (IDNA2008/TR46) implementation\n")
  file(APPEND "${PC_OUT_FILE}" "Version: ${PC_VERSION}\n")
  file(APPEND "${PC_OUT_FILE}" "Requires: ${_requires}\n")
  file(APPEND "${PC_OUT_FILE}" "Libs: ${_libs}\n")
  file(APPEND "${PC_OUT_FILE}" "Cflags: ${_cflags}\n")
endfunction()
