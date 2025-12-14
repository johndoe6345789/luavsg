cmake_minimum_required(VERSION 3.16)

project(libunistring
    VERSION 1.4.1
    LANGUAGES C
)

option(BUILD_SHARED_LIBS "Build shared libraries" OFF)

set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)

add_library(unistring)

# Core sources
file(GLOB_RECURSE UNISTRING_SOURCES
    lib/*.c
)

# Exclude test / tool files
list(FILTER UNISTRING_SOURCES EXCLUDE REGEX ".*/tests?/.*")
list(FILTER UNISTRING_SOURCES EXCLUDE REGEX ".*/test-.*")

target_sources(unistring PRIVATE ${UNISTRING_SOURCES})

target_include_directories(unistring
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/lib>
        $<INSTALL_INTERFACE:include>
)

# Required compile definitions normally provided by config.h
target_compile_definitions(unistring PRIVATE
    HAVE_STDINT_H=1
    HAVE_STDLIB_H=1
    HAVE_STRING_H=1
    HAVE_WCHAR_H=1
)

# Windows specifics
if (WIN32)
    target_compile_definitions(unistring PRIVATE
        _CRT_SECURE_NO_WARNINGS
    )
endif()

set_target_properties(unistring PROPERTIES
    OUTPUT_NAME unistring
    POSITION_INDEPENDENT_CODE ON
)

install(TARGETS unistring
    EXPORT unistringTargets
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
    RUNTIME DESTINATION bin
)

install(DIRECTORY lib/
    DESTINATION include
    FILES_MATCHING PATTERN "*.h"
)

install(EXPORT unistringTargets
    FILE unistringTargets.cmake
    NAMESPACE unistring::
    DESTINATION lib/cmake/unistring
)
