"""Build script for packaging binaries built with PyInstaller. It will combine
the contents of all subdirectories in the ./dist directory."""

import os
import sys
import zipfile

import qcli

# Don't attempt to package if nothing has been built
if not os.path.exists("./dist"):
    print("No dist directory to package.", file=sys.stderr)
    sys.exit(1)

# Get short name for platform
platform = {"win32": "windows", "darwin": "macos"}.get(sys.platform, sys.platform)

package_name = f"quake-cli-tools-{qcli.__version__}-{platform}"

# Create a mapping of internal zip archive names to external relative paths
archive_files = {}
for root, dirs, files in os.walk("./dist"):
    root = os.path.normpath(root)
    parts = root.split(os.path.sep)

    # Don't add files from the root of ./dist
    if len(parts) < 2:
        continue

    for file in files:
        filename = os.path.join(root, file)
        sub_path = os.path.join(package_name, *parts[2:])
        arcname = os.path.join(sub_path, file)
        archive_files[arcname] = filename

# Don't attempt to package if no build artifacts
if not archive_files:
    print("Nothing in dist directory to package.", file=sys.stderr)
    sys.exit(1)

# Write files to zip archive
with zipfile.ZipFile(f"{package_name}.zip", "w") as zip_file:
    for arcname, filename in archive_files.items():
        zip_file.write(filename, arcname=arcname)

sys.exit(0)
