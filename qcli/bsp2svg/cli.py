"""Command line utility for creating and creating WAD files from BSP files

Supported Games:
    - QUAKE
"""


import argparse
import os
import sys


from vgio.quake import bsp

# sys.path.insert(0, '../../')
sys.path.insert(0, 'C:/gitprojects/quake-cli-tools/')
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
        '-a', '--axis',
        dest='axis',
        choices=['x', 'y', 'z'],
        default='z',
        help='projection axis. "z" (default) will create a top down view, "x" and "y" will create a frontal and lateral view'
    )

    parser.add_argument(
        '-p', '--parameters',
        dest='params',
        metavar=(1, 0.5, 64),
        nargs=3,
        type=float,
        default=[1, 0.5, 64],
        help='automatic floor detection parameters. the detection works in 3 passes, each parameter is a number that affects each pass. the first is floor_threshold, defaults to 1, usable values are in (1, 32) range. affects the initial detection of floors, smaller values will detect mor floors. the second is fake_floor_ratio, defaults to 0.5, usable values are in the (0.01, 0.9) range. it represents the ratio of floor/biggest_floor, any floor below this ratio will be ignored. the third is floor_merge_threshold, defaults to 64, usable values are in the (16, 96) range. this affects the last pass in the floor trimming procedure, any previously detected floors that are followed by a floor at less z-distance than this param will be ignored.'
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
        '-f', '--floors',
        dest='floors',
        metavar='floor',
        nargs='*',
        type=float,
        default=[],
        help='numbers representing floor heigts where slices are created. skip for automatic floor detection'
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
        svg_name = f'{os.path.basename(args.file).split(".")[0]}_{args.axis}.svg'
        args.dest = os.path.join(svg_path, svg_name)

    dest_dir = os.path.dirname(args.dest) or '.'
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir, exist_ok=True)

    converter.convert(args.file, args.dest, args)

    sys.exit(0)


if __name__ == '__main__':
    main()
