cmake_minimum_required(VERSION 3.10)
project(TianciNS_JCP VERSION 1.0.0 LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Compiler flags
if(MSVC)
    add_compile_options(/O2 /fp:fast)
else()
    add_compile_options(-O3 -march=native -ffast-math)
endif()

# Main solver executable (80000 steps)
add_executable(TianciNS_80000 src/Tianci_NS80000.cpp)
target_link_libraries(TianciNS_80000 PRIVATE m)

# Grid-specific executables
add_executable(TianciNS_256 src/tianci_256.cpp)
target_link_libraries(TianciNS_256 PRIVATE m)

# Copy data files to build directory
file(COPY ${CMAKE_SOURCE_DIR}/data DESTINATION ${CMAKE_BINARY_DIR})

# Install targets
install(TARGETS TianciNS_80000 TianciNS_256
    RUNTIME DESTINATION bin
)

# Install documentation
install(FILES README.md LICENSE
    DESTINATION share/doc/TianciNS_JCP
)

# Print configuration summary
message(STATUS "")
message(STATUS "TianciNS-JCP Configuration Summary")
message(STATUS "==================================")
message(STATUS "Version: ${PROJECT_VERSION}")
message(STATUS "C++ Compiler: ${CMAKE_CXX_COMPILER_ID} ${CMAKE_CXX_COMPILER_VERSION}")
message(STATUS "Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "")
