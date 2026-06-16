cmake_minimum_required(VERSION 3.10)
project(hccl_plugin LANGUAGES C VERSION 0.1.0)

# ---- Build configuration ------------------------------------------------

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

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

add_executable(test_topology tests/test_topology.c)

target_include_directories(test_topology
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(test_topology PRIVATE hccl_plugin)

add_executable(test_ring tests/test_ring.c)

target_include_directories(test_ring
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(test_ring PRIVATE hccl_plugin)

add_executable(test_butterfly tests/test_butterfly.c)

target_include_directories(test_butterfly
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(test_butterfly PRIVATE hccl_plugin)

# ---- Install rules ------------------------------------------------------

install(TARGETS hccl_plugin
    LIBRARY DESTINATION lib
)

install(FILES ${HEADERS}
    DESTINATION include/hccl_plugin
)

# ---- Build instructions -------------------------------------------------

message(STATUS "")
message(STATUS "HCCL Plugin — CPU-simulated build configured.")
message(STATUS "No CANN SDK required.")
message(STATUS "")
message(STATUS "Build & test:")
message(STATUS "  cd hcccl && mkdir -p build && cd build")
message(STATUS "  cmake .. && make")
message(STATUS "  ./test_topology")
message(STATUS "  ldd libhccl_plugin.so   # verify: no CANN deps")
message(STATUS "")
