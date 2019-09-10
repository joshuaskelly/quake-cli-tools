"""Module for handling cross platform file tasks"""

import os
import shutil
import subprocess
import sys
import tempfile


def temp_volume(name):
    """Creates a temporary volume and returns the path to it.

    Notes:
        Darwin:
            The MacOS implementation creates a ram drive.

        Win32:
            The Windows implementation creates a temporary directory and
            uses the SUBST command to make it appear as a drive.

        Linux:
            The Linux implementation defaults to using a temporary
            directory.

    Args:
        name: The archive name

    Returns:
        A path to the created volume.
    """

    if sys.platform == 'darwin':
        disk_name = name.upper()
        td = f'/Volumes/{disk_name}'

        if os.path.exists(td):
            subprocess.run(f'diskutil unmount {td}', shell=True)

        print('Mounting {0} to {1}'.format(name, td))
        subprocess.run(
            f"diskutil erasevolume HFS+ '{disk_name}' `hdiutil attach -nomount ram://262144`",
            stdout=subprocess.DEVNULL,
            shell=True
        )

        return td

    elif sys.platform == 'win32':
        td = tempfile.mkdtemp()
        drive = 'Q:\\'

        if os.path.exists(drive):
            subprocess.run(
                f'subst /D {drive[:2]}',
                stdout=subprocess.DEVNULL,
                shell=True
            )

        print(f'Mounting {name} to {drive}')
        subprocess.run(
            f'subst Q: {td}',
            stdout=subprocess.DEVNULL,
            shell=True
        )

        return drive

    else:
        td = tempfile.mkdtemp()
        print(f'Mounting {name} to {td}')

        return td


def unmount_temp_volume(path):
    """Unmounts the given volume

    Notes:
        Darwin:
            The MacOS implementation unmounts the ram drive.

        Win32:
            The Windows implementation deletes the temporary files and uses
            the SUBST command to remove the drive.

        Linux:
            Deletes the temporary directory.

    Args:
        path: The path to the volume to unmount.
    """

    if sys.platform == 'darwin':
        if os.path.exists(path):
            subprocess.run(
                f'diskutil unmount {path}',
                stdout=subprocess.DEVNULL,
                shell=True
            )

    elif sys.platform == 'win32':
        if os.path.exists(path):
            shutil.rmtree(path)
            subprocess.run(
                'subst /D Q:',
                stdout=subprocess.DEVNULL,
                shell=True
            )

    else:
        shutil.rmtree(path)


def open_file_browser(path):
    """Opens a file browser at the given path.

    Args:
        path: The location to be opened.
    """
    if sys.platform == 'darwin':
        subprocess.run(
            f'open {path}',
            stdout=subprocess.DEVNULL,
            shell=True
        )

    elif sys.platform == 'win32':
        subprocess.run(
            f'start {path}',
            stdout=subprocess.DEVNULL,
            shell=True
        )

    elif sys.platform == 'linux':
        subprocess.run(
            f'xdg-open {path}',
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=True
        )

    else:
        raise
