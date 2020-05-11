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
    cmd = "cd " + path + ' && git --no-pager grep "' + package + '"'

    out = os.popen(cmd).read()

    # We need to make sure the hit was not in a BuildFile
    hits = out.split("\n")
    hits = [h for h in hits if not "BuildFile.xml" in h]
    cleaned_out = "\n".join(hits)

    return cleaned_out.strip() != ""


directory = "."

build_file_dirs = []

for root, directories, files in os.walk(directory):
    for f in files:
        if os.path.basename(f) == "BuildFile.xml":
            build_file_dirs.append(root)

for build_file_dir in build_file_dirs:

    build_file = os.path.join(build_file_dir, "BuildFile.xml")

    try:
        root_node = root_node_from_build_file(build_file)
    except:
        print("Skipping", build_file_dir, "because xml was not well formed")
        continue

    unused_dependencies = []

    is_library = not build_file_dir.split("/")[-1] in ["test", "plugins", "bin"]

    for elem in root_node:
        if elem.tag == "use":
            dependency = elem.get("name")
            if not dependency:
                continue
            if "/" in dependency:
                if is_library:
                    if not (
                        package_included(dependency, os.path.join(build_file_dir, "interface"))
                        or package_included(dependency, os.path.join(build_file_dir, "src"))
                    ):
                        unused_dependencies.append(dependency)
                else:
                    if not package_included(dependency, build_file_dir):
                        unused_dependencies.append(dependency)

    for dependency in unused_dependencies:
        os.system("sed -i '/" + dependency.replace("/", "\/") + "/d' " + build_file)
