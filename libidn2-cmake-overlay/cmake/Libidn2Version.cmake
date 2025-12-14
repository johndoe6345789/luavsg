include_guard(GLOBAL)

function(libidn2_detect_version out_var)
  # Try to match upstream's git-version-gen behavior using available stamp files.
  # Preference order:
  #  1) .tarball-version
  #  2) .version
  #  3) VERSION file
  #  4) fallback to existing PROJECT_VERSION

  set(_candidates
    "${CMAKE_CURRENT_LIST_DIR}/../.tarball-version"
    "${CMAKE_CURRENT_LIST_DIR}/../.version"
    "${CMAKE_CURRENT_LIST_DIR}/../VERSION"
  )

  set(_ver "")
  foreach(p IN LISTS _candidates)
    if(EXISTS "${p}")
      file(READ "${p}" _raw)
      string(STRIP "${_raw}" _raw)
      if(_raw MATCHES "^[0-9]+\\.[0-9]+\\.[0-9]+([.-].+)?$")
        set(_ver "${_raw}")
        break()
      endif()
    endif()
  endforeach()

  if(NOT _ver)
    set(_ver "${PROJECT_VERSION}")
  endif()

  set(${out_var} "${_ver}" PARENT_SCOPE)
endfunction()
