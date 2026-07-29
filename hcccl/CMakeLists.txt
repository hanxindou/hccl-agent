cmake_minimum_required(VERSION 3.10)
project(hccl_plugin LANGUAGES C VERSION 0.1.0)

# ---- Build configuration ------------------------------------------------

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

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

# No special link dependencies — this is a CPU-simulated build.
# When CANN SDK is available, add:
#   target_link_libraries(hccl_plugin PRIVATE hccl)

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

# ---- Install rules ------------------------------------------------------

install(TARGETS hccl_plugin
    LIBRARY DESTINATION lib
)

install(FILES ${HEADERS}
    DESTINATION include/hccl_plugin
)

# ---- Build instructions -------------------------------------------------

message(STATUS "")
message(STATUS "HCCL Plugin - CPU-simulated build configured.")
message(STATUS "No CANN SDK required.")
message(STATUS "")
message(STATUS "Build & test:")
message(STATUS "  cd hcccl && mkdir -p build && cd build")
message(STATUS "  cmake .. && make")
message(STATUS "  ctest --output-on-failure")
message(STATUS "  ldd libhccl_plugin.so   # verify: no CANN deps")
message(STATUS "")
