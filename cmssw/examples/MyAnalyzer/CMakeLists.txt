project(MyAnalyzer)

# we like new cmake and C++17
cmake_minimum_required(VERSION 3.2)
set(CMAKE_CXX_STANDARD 17)

# Tell cmake where to find the CMSSW libraries
link_directories($ENV{CMSSW_BASE}/lib)

# better optimize for speed
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O2")

# We don't use ROOT in this simple example but it's probably good to know how it would work
find_package(ROOT REQUIRED COMPONENTS Core)
include(${ROOT_USE_FILE})

# Add the plugin library as a target and make sure the name of the .so file starts with "plugin" as it would with scram
file(GLOB PLUGIN_FILES plugins/*.c*)
add_library(MyAnalyzerPlugins SHARED ${PLUGIN_FILES})
set_target_properties(MyAnalyzerPlugins PROPERTIES PREFIX "plugin")

# The CMSSW packages that we need to link against
target_link_libraries(MyAnalyzerPlugins FWCoreFramework)
target_link_libraries(MyAnalyzerPlugins DataFormatsEgammaCandidates)
