"""Command line utility for creating and manipulating PAK files

Supported Games:
    - QUAKE
"""


import argparse
import os
import sys

from vgio.quake import pak

import qcli
from qcli.common import Parser, ResolvePathAction, read_from_stdin


def main():
    parser = Parser(
        prog='pak',
        description='Default action is to add or replace pak files '
                    'entries from list.\nIf list is omitted, pak will '
                    'use stdin.',
        epilog='example: pak tex.pak image.png => adds image.png to tex.pak'
    )

    parser.add_argument(
        'file',
        metavar='file.pak',
        action=ResolvePathAction,
        help='pak file to create'
    )

    parser.add_argument(
        'list',
        nargs='*',
        action=ResolvePathAction,
        default=read_from_stdin()
    )

    parser.add_argument(
        '-q',
        dest='quiet',
        action='store_true',
        help='quiet mode'
    )

    parser.add_argument(
        '-v', '--version',
        dest='version',
        action='version',
        help=argparse.SUPPRESS,
        version='{} version {}'.format(parser.prog, qcli.pak.__version__)
    )

    args = parser.parse_args()

    if not args.list:
        parser.error('the following arguments are required: list')

    dir = os.path.dirname(args.file) or '.'
    if not os.path.exists(dir):
        os.makedirs(dir)

    filemode = 'a'
    if not os.path.isfile(args.file):
        filemode = 'w'

    with pak.PakFile(args.file, filemode) as pak_file:
        if not args.quiet:
            print(f'Archive: {os.path.basename(args.file)}')

        # Process input files
        for file in args.list:
            # Walk directories
            if os.path.isdir(file):
                for root, dirs, files in os.walk(file):
                    for name in [f for f in files if not f.startswith('.')]:
                        fullpath = os.path.join(root, name)
                        relpath = os.path.relpath(fullpath, os.getcwd())

                        if not args.quiet:
                            print(f'  adding: {relpath}')

                        pak_file.write(relpath)

            else:
                relpath = os.path.relpath(file, os.getcwd())

                if not args.quiet:
                    print(f'  adding: {relpath}')

                pak_file.write(relpath)

    sys.exit(0)


if __name__ == '__main__':
    main()
