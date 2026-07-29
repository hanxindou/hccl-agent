cmake_minimum_required(VERSION 3.10)
project(hccl_plugin LANGUAGES C VERSION 0.1.0)

# ---- Build configuration ------------------------------------------------

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

set(HCCL_BACKEND "CPU_SIM" CACHE STRING "HCCL backend: CPU_SIM or ASCEND_CANN")
set_property(CACHE HCCL_BACKEND PROPERTY STRINGS CPU_SIM ASCEND_CANN)
string(TOUPPER "${HCCL_BACKEND}" HCCL_BACKEND)
set(HCCL_BACKEND_OPTIONS CPU_SIM ASCEND_CANN)

if(NOT HCCL_BACKEND STREQUAL "CPU_SIM" AND
   NOT HCCL_BACKEND STREQUAL "ASCEND_CANN")
    message(FATAL_ERROR
        "Unsupported HCCL_BACKEND='${HCCL_BACKEND}'. "
        "Use -DHCCL_BACKEND=CPU_SIM or -DHCCL_BACKEND=ASCEND_CANN."
    )
endif()

if(WIN32)
    # Export all symbols by default so Visual Studio/MSVC builds produce
    # both hccl_plugin.dll and the import library needed by test executables.
    set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)
endif()

if(MSVC)
    add_compile_options(/source-charset:utf-8 /execution-charset:utf-8 /wd4819)
endif()

# ---- Source files -------------------------------------------------------

set(SOURCES
    src/hccl_comm.c
    src/hccl_algorithms.c
)

set(HEADERS
    include/hccl_comm.h
    include/hccl_algorithms.h
)

# ---- Shared library target (CPU-simulated, no CANN SDK required) --------

add_library(hccl_plugin SHARED ${SOURCES})

target_include_directories(hccl_plugin
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)

if(HCCL_BACKEND STREQUAL "CPU_SIM")
    target_compile_definitions(hccl_plugin PRIVATE HCCL_BACKEND_CPU_SIM=1)
else()
    set(HCCL_CANN_ROOT "" CACHE PATH "CANN/Ascend SDK root for ASCEND_CANN backend")
    set(_HCCL_CANN_HINTS
        "${HCCL_CANN_ROOT}"
        "$ENV{ASCEND_HOME_PATH}"
        "$ENV{ASCEND_HOME}"
        "$ENV{CANN_HOME}"
    )
    find_path(HCCL_CANN_INCLUDE_DIR
        NAMES hccl/hccl.h hccl.h
        PATHS ${_HCCL_CANN_HINTS}
        PATH_SUFFIXES include include/hccl latest/include latest/include/hccl
        NO_DEFAULT_PATH
    )
    find_library(HCCL_CANN_LIBRARY
        NAMES hccl libhccl
        PATHS ${_HCCL_CANN_HINTS}
        PATH_SUFFIXES lib lib64 latest/lib64 latest/lib
        NO_DEFAULT_PATH
    )

    if(NOT HCCL_CANN_INCLUDE_DIR OR NOT HCCL_CANN_LIBRARY)
        message(FATAL_ERROR
            "HCCL_BACKEND=ASCEND_CANN requires a real CANN/HCCL SDK. "
            "Missing: HCCL header (hccl/hccl.h or hccl.h) and/or hccl library. "
            "Set HCCL_CANN_ROOT or ASCEND_HOME_PATH/CANN_HOME to the SDK root. "
            "CPU_SIM remains the default and does not require CANN."
        )
    endif()

    target_compile_definitions(hccl_plugin
        PRIVATE
            HCCL_BACKEND_ASCEND_CANN=1
            HCCL_ASCEND_CANN_STUB_UNVERIFIED=1
    )
    target_include_directories(hccl_plugin PRIVATE ${HCCL_CANN_INCLUDE_DIR})
    target_link_libraries(hccl_plugin PRIVATE ${HCCL_CANN_LIBRARY})
endif()

# ---- Tests --------------------------------------------------------------

enable_testing()

add_executable(test_topology tests/test_topology.c)

target_include_directories(test_topology
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(test_topology PRIVATE hccl_plugin)

add_test(NAME test_topology COMMAND test_topology)
set_tests_properties(test_topology PROPERTIES
    WORKING_DIRECTORY $<TARGET_FILE_DIR:test_topology>
)

add_executable(test_ring tests/test_ring.c)

target_include_directories(test_ring
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(test_ring PRIVATE hccl_plugin)

add_test(NAME test_ring COMMAND test_ring)
set_tests_properties(test_ring PROPERTIES
    WORKING_DIRECTORY $<TARGET_FILE_DIR:test_ring>
)

add_executable(test_butterfly tests/test_butterfly.c)

target_include_directories(test_butterfly
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(test_butterfly PRIVATE hccl_plugin)

add_test(NAME test_butterfly COMMAND test_butterfly)
set_tests_properties(test_butterfly PROPERTIES
    WORKING_DIRECTORY $<TARGET_FILE_DIR:test_butterfly>
)

add_executable(test_nhr tests/test_nhr.c)

target_include_directories(test_nhr
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(test_nhr PRIVATE hccl_plugin)

add_test(NAME test_nhr COMMAND test_nhr)
set_tests_properties(test_nhr PROPERTIES
    WORKING_DIRECTORY $<TARGET_FILE_DIR:test_nhr>
)

add_executable(test_mesh tests/test_mesh.c)

target_include_directories(test_mesh
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(test_mesh PRIVATE hccl_plugin)

add_test(NAME test_mesh COMMAND test_mesh)
set_tests_properties(test_mesh PROPERTIES
    WORKING_DIRECTORY $<TARGET_FILE_DIR:test_mesh>
)

add_executable(test_fattree tests/test_fattree.c)

target_include_directories(test_fattree
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(test_fattree PRIVATE hccl_plugin)

add_test(NAME test_fattree COMMAND test_fattree)
set_tests_properties(test_fattree PROPERTIES
    WORKING_DIRECTORY $<TARGET_FILE_DIR:test_fattree>
)

add_executable(test_api_wrappers tests/test_api_wrappers.c)

target_include_directories(test_api_wrappers
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(test_api_wrappers PRIVATE hccl_plugin)

add_test(NAME test_api_wrappers COMMAND test_api_wrappers)
set_tests_properties(test_api_wrappers PROPERTIES
    WORKING_DIRECTORY $<TARGET_FILE_DIR:test_api_wrappers>
)

add_executable(test_allgather tests/test_allgather.c)

target_include_directories(test_allgather
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(test_allgather PRIVATE hccl_plugin)

add_test(NAME test_allgather COMMAND test_allgather)
set_tests_properties(test_allgather PROPERTIES
    WORKING_DIRECTORY $<TARGET_FILE_DIR:test_allgather>
)

add_executable(test_reducescatter tests/test_reducescatter.c)

target_include_directories(test_reducescatter
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(test_reducescatter PRIVATE hccl_plugin)

add_test(NAME test_reducescatter COMMAND test_reducescatter)
set_tests_properties(test_reducescatter PROPERTIES
    WORKING_DIRECTORY $<TARGET_FILE_DIR:test_reducescatter>
)

add_executable(test_reduce_ops tests/test_reduce_ops.c)

target_include_directories(test_reduce_ops
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(test_reduce_ops PRIVATE hccl_plugin)

add_test(NAME test_reduce_ops COMMAND test_reduce_ops)
set_tests_properties(test_reduce_ops PROPERTIES
    WORKING_DIRECTORY $<TARGET_FILE_DIR:test_reduce_ops>
)

add_executable(test_dtype_emulation tests/test_dtype_emulation.c)

target_include_directories(test_dtype_emulation
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(test_dtype_emulation PRIVATE hccl_plugin)

add_test(NAME test_dtype_emulation COMMAND test_dtype_emulation)
set_tests_properties(test_dtype_emulation PROPERTIES
    WORKING_DIRECTORY $<TARGET_FILE_DIR:test_dtype_emulation>
)

# ---- Install rules ------------------------------------------------------

install(TARGETS hccl_plugin
    LIBRARY DESTINATION lib
)

install(FILES ${HEADERS}
    DESTINATION include/hccl_plugin
)

# ---- Build instructions -------------------------------------------------

message(STATUS "")
message(STATUS "HCCL Plugin backend: ${HCCL_BACKEND}")
if(HCCL_BACKEND STREQUAL "CPU_SIM")
    message(STATUS "CPU_SIM build configured. No CANN SDK required.")
else()
    message(STATUS "ASCEND_CANN build configured with STUB_UNVERIFIED adapter boundary.")
    message(STATUS "CANN include: ${HCCL_CANN_INCLUDE_DIR}")
    message(STATUS "CANN library: ${HCCL_CANN_LIBRARY}")
endif()
message(STATUS "")
message(STATUS "Build & test:")
message(STATUS "  cd hcccl && mkdir -p build && cd build")
message(STATUS "  cmake .. -DHCCL_BACKEND=CPU_SIM && make")
message(STATUS "  ctest --output-on-failure")
message(STATUS "  ldd libhccl_plugin.so   # verify: no CANN deps")
message(STATUS "")
