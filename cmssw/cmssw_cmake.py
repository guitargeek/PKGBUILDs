import glob


class CMakeLists(object):
    def __init__(self, path):
        self._path = os.path.join(os.getcwd(), path)
        self._txt = []

    def __iadd__(self, rhs):
        self._txt += rhs
        return self

    def add_interface_library(self, target):
        # In CMake, one should optimally specify the interface files after the INTERFACE property.
        # But since this is CMSSW, this does not make much sense here.
        # http://mariobadr.com/creating-a-header-only-library-with-cmake.html
        # https://cmake.org/cmake/help/latest/command/add_library.html#interface-libraries
        self._txt += [
            "add_library(" + target + " INTERFACE)",
        ]

    def add_library(self, target, source_files):

        self._txt += [
            "add_library(" + target + " SHARED " + " ".join(source_files) + ")",
            "set_target_properties(" + target + " PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${PROJECT_BINARY_DIR}/lib)",
            "install(TARGETS " + target + " LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR})",
        ]

    def add_executable(self, target, source_files):
        self._txt += [
            "add_executable(" + target + " " + " ".join(source_files) + ")",
            "set_target_properties(" + target + " PROPERTIES RUNTIME_OUTPUT_DIRECTORY ${PROJECT_BINARY_DIR}/bin)",
            "install(TARGETS " + target + " DESTINATION ${CMAKE_INSTALL_BINDIR})",
        ]

    def write(self):
        text = self._txt
        if type(text) == list:
            text = "\n".join(text)

        if "<target>" in text:
            raise RuntimeError("There are still <target> placeholders in the CMake file!")

        filename = os.path.join(self._path, "CMakeLists.txt")
        if not os.path.exists(filename):
            with open(filename, "w") as f:
                f.write(text)
        with open(filename, "r") as f:
            old_text = f.read()
        if old_text != text:
            with open(filename, "w") as f:
                f.write(text)


def fill_target(cmake_lines, target):
    return list(map(lambda l: l.replace("<target>", target), cmake_lines))


def name(elem):
    if not elem.get("name") is None:
        return elem.get("name")
    return elem.get("Name")


def lcg_dict_sources(lib_name, n_dicts):
    sources = []
    if n_dicts == 1:
        sources.append(lib_name + "_xr.cxx")
    if n_dicts > 1:
        for i in range(1, n_dicts + 1):
            sources.append(lib_name + f"_x{i}r.cxx")
    return sources


def write_cmake_if_not_same(path, text):
    if type(text) == list:
        text = "\n".join(text)
    filename = os.path.join(path, "CMakeLists.txt")
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            f.write(text)
    with open(filename, "r") as f:
        old_text = f.read()
    if old_text != text:
        with open(filename, "w") as f:
            f.write(text)


def load_config(config_file):
    import yaml

    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    for subsystem, subsystem_config in config["subsystems"].items():
        if subsystem_config is not None:
            if "whitelist" in subsystem_config and "blacklist" in subsystem_config:
                raise ValueError("Package config can't contain blacklist and whitelist at the same time.")
        else:
            config["subsystems"][subsystem] = {}

    if not "requirements-nolink" in config:
        config["requirements-nolink"] = []

    if not "requirements-rename" in config:
        config["requirements-rename"] = {}

    if "build-bin" in config:
        config["build-bin"] = bool(config["build-bin"])
    else:
        config["build-bin"] = True

    if "build-test" in config:
        config["build-test"] = bool(config["build-test"])
    else:
        config["build-test"] = True

    return config


def cmake_dependency_lines(dependency, config):
    cmake = [""]

    dependency = dependency.replace("/", "")

    if dependency in config["requirements-include-dir"]:
        cmake += ["target_include_directories(<target> PUBLIC " + config["requirements-include-dir"][dependency] + ")"]

    if dependency in config["requirements-nolink"]:
        return cmake

    if dependency in config["requirements-rename"]:
        dependency = config["requirements-rename"][dependency]

    if dependency.startswith("root"):
        cmake += ["target_link_libraries(<target> ${ROOT_LIBRARIES})"]
    elif dependency == "boost":
        cmake += [
            "find_package( Boost COMPONENTS filesystem program_options thread REQUIRED )",
            "target_link_libraries(<target> ${Boost_LIBRARIES})",
        ]
    elif dependency == "eigen":
        cmake += ["find_package (Eigen3 3.3 REQUIRED NO_MODULE)", "target_link_libraries(<target> Eigen3::Eigen)"]
    else:
        cmake += ["target_link_libraries(<target> " + dependency + ")"]

    return cmake


def root_node_from_build_file(build_file, default_lib_name=None, in_plugin_dir=False):

    with open(build_file) as f:
        xml = f.read()

    auto = not "<bin" in xml and not "<library" in xml

    if auto and in_plugin_dir:
        xml = '<flags EDM_PLUGIN="1"/>\n' + xml
        default_lib_name = default_lib_name + "Plugins"
    if auto:
        xml = '<library   file="*.cc" name="' + default_lib_name + '">\n' + xml + "\n</library>"

    return ET.fromstring("<root>" + xml + "</root>")


def parse_elements(root_node, config):
    cmake = []
    flags = {"LCG_DICT_HEADER": [], "LCG_DICT_XML": []}

    for elem in root_node:
        if elem.tag == "flags":
            if elem.get("cppflags"):
                cmake += ['set_target_properties(<target> PROPERTIES COMPILE_FLAGS "' + elem.get("cppflags") + '")']
                cmake += ['set_target_properties(<target> PROPERTIES PREFIX "plugin")']
            if elem.get("EDM_PLUGIN"):
                cmake += ['set_target_properties(<target> PROPERTIES PREFIX "plugin")']
            if elem.get("LCG_DICT_HEADER"):
                flags["LCG_DICT_HEADER"] = elem.get("LCG_DICT_HEADER").split(" ")
            if elem.get("LCG_DICT_XML"):
                flags["LCG_DICT_XML"] = elem.get("LCG_DICT_XML").split(" ")
        if elem.tag == "use" or elem.tag == "lib" and name(elem) != "1":
            cmake += cmake_dependency_lines(name(elem), config)
        if elem.tag == "lib":
            cmake += ["target_link_libraries(<target> " + name(elem) + ")"]

    return cmake, flags


def interpret_files(file):
    files = []
    for f in file.split(","):
        if "*" in f:
            globbed = glob.glob(os.path.join(root, f))
            files += [g[len(root) + 1 :] for g in globbed]
        else:
            files.append(f)
    return files


def lcg_dict_generation(lib_name, headers, xmls, include_dirs):
    sources = lcg_dict_sources(lib_name, len(headers))
    cmake = []
    for header, xml, source in zip(headers, xmls, sources):
        cmake += [
            """
add_custom_command(OUTPUT """
            + source
            + """
    COMMAND genreflex ${CMAKE_CURRENT_SOURCE_DIR}/src/"""
            + header
            + """
    -s ${CMAKE_CURRENT_SOURCE_DIR}/src/"""
            + xml
            + """
    -o """
            + source
            + """
    --rootmap=${CMAKE_BINARY_DIR}/lib/lib"""
            + lib_name
            + "_"
            + source.replace(".cxx", ".rootmap")
            + """
    --rootmap-lib=${CMAKE_BINARY_DIR}/lib/lib"""
            + lib_name
            + """.so
    --library ${CMAKE_BINARY_DIR}/lib/lib"""
            + lib_name
            + """.so --multiDict
    -DCMS_DICT_IMPL -D_REENTRANT -DGNUSOURCE -D__STRICT_ANSI__ -DCMSSW_REFLEX_DICT -I${PROJECT_SOURCE_DIR}/cmssw
    """
            + " ".join(["-I" + d for d in include_dirs])
            + """
    DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/src/"""
            + header
            + """ ${CMAKE_CURRENT_SOURCE_DIR}/src/"""
            + xml
            + """
)""",
            "",
        ]
    return cmake


def get_global_dependencies(build_file):
    with open(build_file) as f:
        xml = f.read()

    root_node = ET.fromstring("<root>" + xml + "</root>")

    global_dependencies = []

    for elem in root_node:
        if elem.tag == "use":
            global_dependencies.append(name(elem).replace("/", ""))
        if elem.tag == "environment":
            for sub_elem in elem:
                if sub_elem.tag == "use":
                    global_dependencies.append(name(sub_elem).replace("/", ""))

    return global_dependencies


def get_include_dirs(deps, include_dir_dict):
    out = []
    for dep in deps:
        if dep in include_dir_dict:
            out.append(include_dir_dict[dep])
    return out


def build_xml_to_cmake(root, build_file, root_node):

    cmake = CMakeLists(root)

    cmake += [
        "",
        "list(APPEND CMAKE_PREFIX_PATH $ENV{ROOTSYS})",
        "find_package(ROOT REQUIRED COMPONENTS Core MathCore)",
        "include(${ROOT_USE_FILE})",
        "",
        'file(GLOB_RECURSE SOURCE_FILES "src/*.cc")',
        "",
        "include_directories(.)",
        "",
    ]

    n_globbed_files = len(glob.glob(os.path.join(root, "src/*.cc")))

    global_dependencies = get_global_dependencies(build_file)

    for elem in root_node:
        if elem.tag in ["library", "bin"]:
            target = name(elem)

            files = interpret_files(elem.get("file"))

            if target is None:
                target = files[0].split(".")[0]

            is_interface = False

            if elem.tag == "library":
                n_files = n_globbed_files + len(files)
                if n_files == 0:
                    cmake.add_interface_library(target)
                    is_interface = True
                else:
                    cmake.add_library(target, files)
            if elem.tag == "bin":
                cmake.add_executable(target, files)

            cmake += parse_elements(elem, config)[0]
            for dependency in global_dependencies:
                cmake += cmake_dependency_lines(dependency, config)

            if is_interface:
                cmake._txt = fill_target(cmake._txt, target + " INTERFACE")
            else:
                cmake._txt = fill_target(cmake._txt, target)

    cmake.write()


if __name__ == "__main__":

    import argparse
    import os
    import subprocess
    import xml.etree.ElementTree as ET

    parser = argparse.ArgumentParser(description="Generate CMakeLists for CMSSW.")
    parser.add_argument("config", type=str, help="path to yaml config file")

    args = parser.parse_args()

    config = load_config(args.config)

    os.chdir("cmssw")

    packages_in_subsystem = {subsystem: set() for subsystem in config["subsystems"]}

    for root, directories, files in os.walk("."):

        root_split = root.split("/")

        if len(root_split) < 3:
            continue

        subsystem = root_split[1]

        if not subsystem in config["subsystems"]:
            continue

        subsystem_config = config["subsystems"][subsystem]
        package = root_split[2]

        if (
            "whitelist" in subsystem_config
            and not package in subsystem_config["whitelist"]
            or "blacklist" in subsystem_config
            and package in subsystem_config["blacklist"]
        ):
            continue

        packages_in_subsystem[subsystem].add(package)

        if root.count("/") == 2:

            if os.path.exists(os.path.join(root, "BuildFile.xml")):

                cmake = CMakeLists(root)

                build_file = os.path.join(root, "BuildFile.xml")
                lib_name = subsystem + package
                cmake += [
                    "",
                    "list(APPEND CMAKE_PREFIX_PATH $ENV{ROOTSYS})",
                    "find_package(ROOT REQUIRED COMPONENTS Core MathCore)",
                    "include(${ROOT_USE_FILE})",
                    "",
                    'file(GLOB_RECURSE SOURCE_FILES "src/*.cc")',
                    "",
                    "include_directories(.)",
                    "",
                ]

                global_include_dirs = get_include_dirs(
                    get_global_dependencies(build_file), config["requirements-include-dir"]
                )

                n_globbed_files = len(glob.glob(os.path.join(root, "src/*.cc")))

                root_node = root_node_from_build_file(build_file, default_lib_name=lib_name)

                lib_node = None

                for element in root_node:
                    if element.tag == "library":
                        lib_node = element

                cmake_from_build_file, flags = parse_elements(lib_node, config)

                if not len(flags["LCG_DICT_HEADER"]) == 0 in flags and os.path.exists(
                    os.path.join(root, "src/classes.h")
                ):
                    flags["LCG_DICT_HEADER"] = ["classes.h"]
                    flags["LCG_DICT_XML"] = ["classes_def.xml"]

                cmake += lcg_dict_generation(
                    lib_name, flags["LCG_DICT_HEADER"], flags["LCG_DICT_XML"], global_include_dirs
                )

                gen_sources = lcg_dict_sources(lib_name, len(flags["LCG_DICT_HEADER"]))

                is_interface = False
                n_files = n_globbed_files + len(gen_sources)
                if n_files == 0:
                    is_interface = True
                    cmake.add_interface_library(lib_name)
                else:
                    cmake.add_library(lib_name, ["${SOURCE_FILES}"] + gen_sources)

                cmake += cmake_from_build_file

                if is_interface:
                    cmake._txt = fill_target(cmake._txt, lib_name + " INTERFACE")
                else:
                    cmake._txt = fill_target(cmake._txt, lib_name)

                cmake.write()

        for file in files:
            if (
                file == "BuildFile.xml"
                and root.count("/") == 3
                and (not root.endswith("test") or config["build-test"])
                and (not root.endswith("bin") or config["build-bin"])
                and not root.endswith("python")
            ):

                build_file = os.path.join(root, file)
                root_node = root_node_from_build_file(
                    build_file, default_lib_name=subsystem + package, in_plugin_dir=os.path.basename(root) == "plugins"
                )

                build_xml_to_cmake(root, build_file, root_node)

    # Finally, include all subdirectories into which we have written CMakeList files
    cmake = CMakeLists(".")
    cmake += ["include_directories(.)", ""]
    for subsystem, packages in packages_in_subsystem.items():
        for package in packages:
            for root, _, files in os.walk(os.path.join(subsystem, package)):
                if "CMakeLists.txt" in files:
                    cmake += ["add_subdirectory(" + root + ")"]
    cmake.write()

    os.chdir("..")

    cmake = CMakeLists(".")
    cmake += config["cmake-lists-root"]
    cmake.write()
