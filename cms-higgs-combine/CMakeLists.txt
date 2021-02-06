project(HiggsAnalysis-CombinedLimit CXX)
cmake_minimum_required(VERSION 3.2)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -pthread -std=c++17 -lvdt -m64 -O2 -rdynamic -Wno-deprecated-declarations ")

find_package(ROOT REQUIRED COMPONENTS Core MathMore RooFit RooFitCore RooStats Minuit HistFactory)
include(${ROOT_USE_FILE})

find_package(Boost 1.45.0 COMPONENTS program_options filesystem system)

set(LIBNAME HiggsAnalysisCombinedLimit)
set(COMBINE_DIR HiggsAnalysis/CombinedLimit)

include_directories(.)
include_directories(/usr/include/eigen3)
include_directories(${COMBINE_DIR}/interface)

file(GLOB SOURCE_FILES ${COMBINE_DIR}/src/*.c*)
file(GLOB HEADER_FILES ${COMBINE_DIR}/interface/*.h*)

ROOT_GENERATE_DICTIONARY(${LIBNAME}_xr ${COMBINE_DIR}/interface/classes.h LINKDEF ${COMBINE_DIR}/src/classes_def.xml)

add_library(${LIBNAME} SHARED ${SOURCE_FILES} ${LIBNAME}_xr.cxx)
set_target_properties(${LIBNAME} PROPERTIES PUBLIC_HEADER "${HEADER_FILES}")

target_link_libraries(${LIBNAME} PUBLIC ${ROOT_LIBRARIES})
target_link_libraries(${LIBNAME} PUBLIC ${Boost_LIBRARIES})

add_executable(combine ${COMBINE_DIR}/bin/combine.cpp)
target_link_libraries(combine PUBLIC ${LIBNAME})

install(FILES ${PROJECT_BINARY_DIR}/lib${LIBNAME}_xr_rdict.pcm DESTINATION ${CMAKE_INSTALL_PREFIX}/lib)
install(TARGETS ${LIBNAME}
        LIBRARY DESTINATION ${CMAKE_INSTALL_PREFIX}/lib
        PUBLIC_HEADER DESTINATION ${CMAKE_INSTALL_PREFIX}/include/${COMBINE_DIR}/interface
)
install(TARGETS combine DESTINATION ${CMAKE_INSTALL_PREFIX}/bin)
