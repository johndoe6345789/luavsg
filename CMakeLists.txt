cmake_minimum_required(VERSION 3.24)

project(MyFirstVsgApplication
    VERSION 0.0.0
    DESCRIPTION "Template of how to create a program using VulkanSceneGraph and CMake"
    LANGUAGES CXX
)

# -----------------------------------------------------------------------------
# Global configuration
# -----------------------------------------------------------------------------

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${PROJECT_BINARY_DIR}/bin)

# -----------------------------------------------------------------------------
# Vulkan (baked-in fallback to vendored SDK under lib/VulkanSDK)
# -----------------------------------------------------------------------------
# Priority:
#  1) -DVULKAN_SDK=... passed on the command line
#  2) Environment variable VULKAN_SDK
#  3) Vendored SDK under <repo>/lib/VulkanSDK/<version>

if(NOT DEFINED VULKAN_SDK OR VULKAN_SDK STREQUAL "")
    if(DEFINED ENV{VULKAN_SDK} AND NOT "$ENV{VULKAN_SDK}" STREQUAL "")
        set(VULKAN_SDK "$ENV{VULKAN_SDK}")
    else()
        file(GLOB _vulkan_sdk_candidates
            LIST_DIRECTORIES true
            "${CMAKE_SOURCE_DIR}/lib/VulkanSDK/*"
        )
        list(SORT _vulkan_sdk_candidates)
        list(REVERSE _vulkan_sdk_candidates)

        if(_vulkan_sdk_candidates)
            list(GET _vulkan_sdk_candidates 0 VULKAN_SDK)
        endif()
    endif()
endif()

if(NOT DEFINED VULKAN_SDK OR VULKAN_SDK STREQUAL "")
    message(FATAL_ERROR
        "VULKAN_SDK not set and no vendored SDK found at "
        "${CMAKE_SOURCE_DIR}/lib/VulkanSDK/<version>."
    )
endif()

set(_vulkan_include "${VULKAN_SDK}/Include")

# Prefer x64 libs by default; fall back to ARM64 layout if present.
set(_vulkan_lib_dir "${VULKAN_SDK}/Lib")
if(NOT EXISTS "${_vulkan_lib_dir}/vulkan-1.lib")
    if(EXISTS "${VULKAN_SDK}/Lib-ARM64/vulkan-1.lib")
        set(_vulkan_lib_dir "${VULKAN_SDK}/Lib-ARM64")
    endif()
endif()

set(_vulkan_lib "${_vulkan_lib_dir}/vulkan-1.lib")

if(NOT EXISTS "${_vulkan_include}/vulkan/vulkan.h")
    message(FATAL_ERROR
        "Vulkan headers not found at: ${_vulkan_include}/vulkan/vulkan.h\n"
        "VULKAN_SDK is: ${VULKAN_SDK}"
    )
endif()

if(NOT EXISTS "${_vulkan_lib}")
    message(FATAL_ERROR
        "Vulkan import library not found at: ${_vulkan_lib}\n"
        "VULKAN_SDK is: ${VULKAN_SDK}"
    )
endif()

# Force these hints into the cache so subprojects (vsg) can pick them up.
set(VULKAN_SDK "${VULKAN_SDK}" CACHE PATH "Vulkan SDK root" FORCE)
set(Vulkan_INCLUDE_DIR "${_vulkan_include}" CACHE PATH "Vulkan include dir" FORCE)
set(Vulkan_LIBRARY "${_vulkan_lib}" CACHE FILEPATH "Vulkan library" FORCE)

message(STATUS "Using VULKAN_SDK: ${VULKAN_SDK}")
message(STATUS "Vulkan include:  ${Vulkan_INCLUDE_DIR}")
message(STATUS "Vulkan library:  ${Vulkan_LIBRARY}")

# -----------------------------------------------------------------------------
# Dependencies (Option B: subprojects)
# -----------------------------------------------------------------------------

add_subdirectory(lib/VulkanSceneGraph)

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/lib/vsgXchange/CMakeLists.txt")
    add_subdirectory(lib/vsgXchange)
    set(HAVE_VSGXCHANGE ON)
endif()

# -----------------------------------------------------------------------------
# Application
# -----------------------------------------------------------------------------

set(SOURCES
    src/main.cpp
)

add_executable(myfirstvsgapplication ${SOURCES})

target_link_libraries(myfirstvsgapplication
    PRIVATE
        vsg::vsg
)

if(HAVE_VSGXCHANGE)
    target_compile_definitions(myfirstvsgapplication PRIVATE vsgXchange_FOUND)
    target_link_libraries(myfirstvsgapplication PRIVATE vsgXchange::vsgXchange)
endif()

# -----------------------------------------------------------------------------
# Utility targets
# -----------------------------------------------------------------------------

add_custom_target(clobber
    COMMAND git clean -d -f -x
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
)

# -----------------------------------------------------------------------------
# Install
# -----------------------------------------------------------------------------

install(TARGETS myfirstvsgapplication
    RUNTIME DESTINATION bin
)
