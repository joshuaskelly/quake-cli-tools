"""Command line utility for creating and creating WAD files from BSP files

Supported Games:
    - QUAKE
"""


import argparse
import os
import sys


from vgio.quake import bsp

import qcli
from qcli.bsp2svg import converter
from qcli.common import Parser, ResolvePathAction


def main():
    parser = Parser(
        prog='bsp2svg',
        description='Create an svg document from the given bsp file.',
        epilog='example: bsp2svg e1m1.bsp => creates the svg file e1m1.svg'
    )

    parser.add_argument(
        'file',
        metavar='file.bsp',
        action=ResolvePathAction
    )

    parser.add_argument(
        '-d',
        metavar='file.svg',
        dest='dest',
        default=os.getcwd(),
        action=ResolvePathAction,
        help='svg file to create'
    )

    parser.add_argument(
        '-i', '--ignore',
        dest='ignore',
        metavar='name',
        nargs='*',
        default=[],
        help='texture names to ignore'
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

    if not bsp.is_bspfile(args.file):
        print(f'{parser.prog}: cannot find or open {args.file}', file=sys.stderr)

    # Validate or create out file
    if args.dest == os.getcwd():
        svg_path = os.path.dirname(args.file)
        svg_name = f'{os.path.basename(args.file).split(".")[0]}.svg'
        args.dest = os.path.join(svg_path, svg_name)

    dest_dir = os.path.dirname(args.dest) or '.'
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir, exist_ok=True)

    converter.convert(args.file, args.dest, args)

    sys.exit(0)


if __name__ == '__main__':
    main()
