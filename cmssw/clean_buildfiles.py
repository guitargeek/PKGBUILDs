import xml.etree.ElementTree as ET
import os


def root_node_from_build_file(build_file):

    with open(build_file) as f:
        xml = f.read()

    xml_strip = xml.strip()

    root_node = ET.fromstring("<root>" + xml + "</root>")

    return root_node


def package_included(package, path):
    if not os.path.isdir(path):
        return False
    cmd = 'cd ' + path + ' && git --no-pager grep "' + package + '"'
    return os.popen(cmd).read().strip() != ""

directory = "."

package_dirs = []

for root, directories, files in os.walk(directory):
    for f in files:
        if os.path.basename(f) == "BuildFile.xml" and not root.split(directory)[-1][1:].count("/") != 1:
            package_dirs.append(root)

for package_dir in package_dirs:

    build_file = os.path.join(package_dir, "BuildFile.xml")

    root_node = root_node_from_build_file(build_file)
    unused_dependencies = []

    for elem in root_node:
        if elem.tag == "use":
            dependency = elem.get("name")
            if "/" in dependency:
                if( not (
                    package_included(dependency, os.path.join(package_dir, "interface")) or
                    package_included(dependency, os.path.join(package_dir, "src"))
                    )):
                    unused_dependencies.append(dependency)

    print(package_dir)
    for dependency in unused_dependencies:
        os.system("sed -i '/"+dependency.replace("/", "\/")+"/d' " + build_file)
