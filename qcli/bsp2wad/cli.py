"""Command line utility for creating and creating WAD files from BSP files

Supported Games:
    - QUAKE
"""


import argparse
import io
import os
import sys

from vgio.quake import bsp, wad

import qcli
from qcli.common import Parser, ResolvePathAction, read_from_stdin


def main():
    parser = Parser(
        prog='bsp2wad',
        description='Default action is to create a wad archive from '
                    'miptextures extracted from the given bsp file.'
                    '\nIf list is omitted, pak will use stdin.',
        epilog='example: bsp2wad e1m1.bsp => creates the wad file e1m1.wad'
    )

    parser.add_argument(
        'list',
        nargs='*',
        action=ResolvePathAction,
        default=read_from_stdin()
    )

    parser.add_argument(
        '-d',
        metavar='file.wad',
        dest='dest',
        default=os.getcwd(),
        action=ResolvePathAction,
        help='wad file to create'
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
        version=f'{parser.prog} version {qcli.__version__}'
    )

    args = parser.parse_args()

    if not args.list:
        parser.error('the following arguments are required: list')

    miptextures = []

    for file in args.list:
        if not bsp.is_bspfile(file):
            print('{0}: cannot find or open {1}'.format(parser.prog, file),
                  file=sys.stderr)
            continue

        bsp_file = bsp.Bsp.open(file)
        miptextures += [mip for mip in bsp_file.miptextures if mip and mip.name not in [n.name for n in miptextures]]

    if args.dest == os.getcwd():
        wad_path = os.path.dirname(file)

        if len(args.list) == 1:
            wad_name = f'{os.path.basename(file).split(".")[0]}.wad'

        else:
            wad_name = 'out.wad'

        args.dest = os.path.join(wad_path, wad_name)

    dir = os.path.dirname(args.dest) or '.'
    if not os.path.exists(dir):
        os.makedirs(dir)

    with wad.WadFile(args.dest, mode='w') as wad_file:
        if not args.quiet:
            print(f'Archive: {os.path.basename(args.dest)}')

        for miptex in miptextures:
            if not miptex:
                continue

            buff = io.BytesIO()
            wad.Miptexture.write(buff, miptex)
            buff.seek(0)

            info = wad.WadInfo(miptex.name)
            info.file_size = 40 + len(miptex.pixels)
            info.disk_size = info.file_size
            info.compression = wad.CompressionType.NONE
            info.type = wad.LumpType.MIPTEX

            if not args.quiet:
                print(f' adding: {info.filename}')

            wad_file.writestr(info, buff)

    sys.exit(0)


if __name__ == '__main__':
    main()
