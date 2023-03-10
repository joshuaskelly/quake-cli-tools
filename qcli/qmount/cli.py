"""Command line utility for mounting a PAK file as a logical volume

Supported Games:
    - QUAKE
"""


import argparse
import os
import signal
import sys
import time
from tkinter import filedialog

from watchdog.observers import Observer

from vgio.quake import pak

import qcli
from qcli.common import Parser, ResolvePathAction
from qcli.qmount.handlers import TempPakFileHandler
import qcli.qmount.platforms as platforms


def update_pak(context, archive_name, files, pak_filename):
    # Write out updated files
    if context['dirty']:
        print(f'Updating changes to {archive_name}...')

        with pak.PakFile(pak_filename, 'w') as pak_file:
            for filename in files:
                pak_file.writestr(filename, files[filename])

        print('Saved!')

    else:
        print(f'No changes detected to {archive_name}')


def main():
    # Fix for frozen packages
    def handleSIGINT(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, handleSIGINT)

    parser = Parser(
        prog='qmount',
        description='Default action is to mount the given pak file as a logical volume.',
        epilog='example: qmount TEST.PAK => mounts TEST.PAK as a logical volume.'
    )

    parser.add_argument(
        'file',
        metavar='file.pak',
        action=ResolvePathAction,
        help='pak file to mount',
        nargs='?'
    )

    parser.add_argument(
        '-f', '--no-file-browser',
        dest='open_file_browser',
        action='store_false',
        help="don't open a file browser once mounted"
    )

    parser.add_argument(
        '--verbose',
        dest='verbose',
        action='store_true',
        help='verbose mode'
    )

    parser.add_argument(
        '-v', '--version',
        dest='version',
        action='version',
        help=argparse.SUPPRESS,
        version=f'{parser.prog} version {qcli.__version__}'
    )

    args = parser.parse_args()

    if args.file is None:
        args.file = filedialog.askopenfilename(
            title="Choose PAK file",
            filetypes=(("Quake PAK", "*.pak"),
                       ("all files", "*.*")))

    dir = os.path.dirname(args.file) or '.'
    if not os.path.exists(dir):
        os.makedirs(dir)

    archive_name = os.path.basename(args.file)
    context = {'dirty': False}
    files = {}

    # If the pak file exists put the contents into the file dictionary
    if os.path.exists(args.file):
        with pak.PakFile(args.file) as pak_file:
            for info in pak_file.infolist():
                name = info.filename
                files[name] = pak_file.read(name)

    else:
        context['dirty'] = True

    temp_directory = platforms.temp_volume(archive_name)

    # Copy pak file contents into the temporary directory
    for filename in files:
        abs_path = os.path.join(temp_directory, filename)
        dir = os.path.dirname(abs_path)

        if not os.path.exists(dir):
            os.makedirs(dir)

        with open(abs_path, 'wb') as out_file:
            out_file.write(files[filename])

    # Open a native file browser
    if args.open_file_browser:
        platforms.open_file_browser(temp_directory)

    # Start file watching
    observer = Observer()
    handler = TempPakFileHandler(
        context,
        temp_directory,
        files,
        args.verbose,
        ignore_patterns=[
            '*/.DS_Store',
            '*/Thumbs.db'
        ],
        ignore_directories=True
    )
    observer.schedule(handler, path=temp_directory, recursive=True)

    if sys.platform == 'win32':
        print('Press Ctrl+S to save')
        print('Press Ctrl+C to quit without saving')
    else:
        print('Press Ctrl+C to save and quit')

    observer.start()

    # Wait for user to terminate
    try:
        while True:
            time.sleep(0.1)

            if platforms.check_save_key():
                update_pak(context, archive_name, files, args.file)

            # Detect the deletion of the watched directory.
            if not os.path.exists(temp_directory):
                raise KeyboardInterrupt

    except KeyboardInterrupt:
        print()
        try:
            observer.stop()

        except:
            """This is a temporary workaround. Watchdog will raise an exception
            if the watched media is ejected."""

    observer.join()

    if sys.platform != 'win32':
        update_pak(context, archive_name, files, args.file)

    # Clean up temp directory
    platforms.unmount_temp_volume(temp_directory)

    sys.exit(0)


if __name__ == '__main__':
    main()
