"""Command line utility for extracting image files from WAD files

Supported Games:
    - QUAKE
"""


import array
import argparse
import os
import sys
from tabulate import tabulate

from PIL import Image

from vgio import quake
from vgio.quake import lmp, wad

import qcli
from qcli.common import Parser, ResolvePathAction


def main():
    """CLI entrypoint"""

    parser = Parser(
        prog='unwad',
        description='Default action is to convert files to png format and extract to xdir.',
        epilog='example: unwad gfx.wad -d ./out => extract all files to ./out'
    )

    parser.add_argument(
        'file',
        metavar='file.wad',
        action=ResolvePathAction
    )

    parser.add_argument(
        '-l', '--list',
        action='store_true',
        help='list files'
    )

    parser.add_argument(
        '-d',
        metavar='xdir',
        default=os.getcwd(),
        dest='dest',
        action=ResolvePathAction,
        help='extract files into xdir'
    )

    parser.add_argument(
        '-q',
        dest='quiet',
        action='store_true',
        help='quiet mode'
    )

    parser.add_argument(
        '-f',
        dest='format',
        default='png',
        choices=['bmp','gif','png','tga'],
        help='image format to convert to'
    )

    parser.add_argument(
        '-v', '--version',
        dest='version',
        action='version',
        help=argparse.SUPPRESS,
        version=f'{parser.prog} version {qcli.unwad.__version__}'
    )

    args = parser.parse_args()

    archive_name = os.path.basename(args.file)

    if not wad.is_wadfile(args.file):
        print(f'{parser.prog}: cannot find or open {args.file}', file=sys.stderr)
        sys.exit(1)

    if args.list:
        with wad.WadFile(args.file) as wad_file:
            info_list = sorted(wad_file.infolist(), key=lambda i: i.filename)

            lump_types = {
                0: 'NONE',
                1: 'LABEL',
                64: 'LUMP',
                65: 'QTEX',
                66: 'QPIC',
                67: 'SOUND',
                68: 'MIPTEX'
            }

            def lump_type(num):
                if num in lump_types:
                    return lump_types[num]

                return num

            headers = ['Length', 'Type', 'Name']
            table = [[i.file_size, lump_type(i.type), i.filename] for i in info_list]
            length = sum([i.file_size for i in info_list])
            count = len(info_list)
            table.append([length, '', f'{count} file{"s" if count > 1 else ""}'])

            separator = []
            for i in range(len(headers)):
                t = max(len(str(length)), len(headers[i]) + 2)
                separator.append('-' * t)

            table.insert(-1, separator)

            print(f'Archive: {archive_name}')
            print(tabulate(table, headers=headers))

            sys.exit(0)

    if not os.path.exists(args.dest):
        os.makedirs(args.dest)

    with wad.WadFile(args.file) as wad_file:
        if not args.quiet:
            print(f'Archive: {archive_name}')

        # Flatten out palette
        palette = []
        for p in quake.palette:
            palette += p

        for item in wad_file.infolist():
            filename = item.filename
            fullpath = os.path.join(args.dest, filename)
            fullpath_ext = '{0}.{1}'.format(fullpath, args.format)

            data = None
            size = None

            # Pictures
            if item.type == wad.LumpType.QPIC:
                with wad_file.open(filename) as lmp_file:
                    lump = lmp.Lmp.open(lmp_file)
                    size = lump.width, lump.height
                    data = array.array('B', lump.pixels)

            # Special cases
            elif item.type == wad.LumpType.MIPTEX:
                # Console characters
                if item.file_size == 128 * 128:
                    size = 128, 128

                    with wad_file.open(filename) as lump:
                        data = lump.read(item.file_size)

                else:
                    # Miptextures
                    try:
                        with wad_file.open(filename) as mip_file:
                            mip = wad.Miptexture.read(mip_file)
                            data = mip.pixels[:mip.width * mip.height]
                            data = array.array('B', data)
                            size = mip.width, mip.height
                    except:
                        print(f' failed to extract resource: {item.filename}', file=sys.stderr)
                        continue

            try:
                # Convert to image file
                if data is not None and size is not None:
                    img = Image.frombuffer('P', size, data, 'raw', 'P', 0, 1)
                    img.putpalette(palette)
                    img.save(fullpath_ext)

                    if not args.quiet:
                        print(f' extracting: {fullpath_ext}')

                # Extract as raw file
                else:
                    wad_file.extract(filename, args.dest)

                    if not args.quiet:
                        print(f' extracting: {fullpath}')
            except:
                print(f'{parser.prog}: error: {sys.exc_info()[1]}', file=sys.stderr)

    sys.exit(0)


if __name__ == '__main__':
    main()
