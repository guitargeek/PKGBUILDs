import shutil
import os
import subprocess
import yaml
import xml.etree.ElementTree as ET


with open("config.yml", "r") as f:
    config = yaml.safe_load(f)

cmake_includes = ["include_directories(.)", ""]

for root, directories, files in os.walk("coral"):
    if root.count("/") == 1:
        package = root[6:]

        if package in config["whitelisted-packages"]:

            cmake_includes += ["add_subdirectory(" + package + ")"]

            with open(os.path.join(root, "CMakeLists.txt"), "w") as f:
                for directory in directories:
                    f.write("add_subdirectory(" + directory + ")\n")

    for file in files:

        if file == "BuildFile.xml":

            libname = package.replace("/", "")

            cmake = config["cmake-lib-base"][:]

            with open(os.path.join(root, file)) as f:
                xml = f.read()
            root_node = ET.fromstring("<root>" + xml + "</root>")

            cmake += ["add_library(" + libname + " SHARED ${SOURCE_FILES})", ""]

            for elem in root_node:
                if elem.tag == "use":
                    dependency = elem.get("name").replace("/", "")

                    if dependency in config["requirements-rename"]:
                        dependency = config["requirements-rename"][dependency]

                    if dependency == "boost":
                        cmake += [
                            "find_package( Boost COMPONENTS filesystem REQUIRED )",
                            "target_link_libraries(" + libname + " ${Boost_LIBRARIES})",
                        ]
                    elif dependency == "python":
                        cmake += [
                            "include_directories(/usr/include/python2.7)",
                            "target_link_libraries(" + libname + " python2.7)",
                        ]
                    else:
                        cmake += ["target_link_libraries(" + libname + " " + dependency + ")"]

            cmake += [
                """install(TARGETS """
                + libname
                + """
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    PUBLIC_HEADER DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})"""
            ]

            with open(os.path.join(root, "CMakeLists.txt"), "w") as f:
                f.write("\n".join(cmake))

with open("coral/CMakeLists.txt", "w") as f:
    f.write("\n".join(cmake_includes))
