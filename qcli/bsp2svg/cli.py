"""Command line utility for creating SVG files from BSP files

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
        '-p', '--projection-axis',
        dest='projection_axis',
        choices=['x', 'y', 'z'],
        default='z',
        help='projection axis. "z" (default) will create a top down view, "x" and "y" will create a frontal and lateral view'
    )

    parser.add_argument(
        '-l', '--slicing-axis',
        dest='slicing_axis',
        choices=['x', 'y', 'z'],
        help='slicing axis. the slices will be aligned to this axis. if not specified, the projection axis will be used for slicing as well. a common use case is to use "z" for slicing and "x" or "y" for projection. only relevant when using the -f option, otherwise it\s ignored'
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
        '-s', '--slices',
        dest='slices',
        metavar='slice',
        nargs='*',
        type=float,
        help='enables slicing functionality. without any parameters, it will also enable automatic floor / wall detection. it can have additional number parameters representing floor / wall distances where slices are created'
    )

    parser.add_argument(
        '-t', '--detection-parameters',
        dest='detection_params',
        metavar=(1, 0.3, 64),
        nargs=3,
        type=float,
        default=[1, 0.3, 64],
        help='automatic slice detection parameters. the detection works in 3 passes, each parameter is a number that affects each pass. the first is slice_threshold, defaults to 1, usable values are in (1, 32) range. affects the initial detection of floors / walls, smaller values will detect more floors / walls. the second is fake_slice_ratio, defaults to 0.5, usable values are in the (0.01, 0.9) range. it represents the ratio of slice/biggest_slice, any slice below this ratio will be ignored. the third is slice_merge_threshold, defaults to 64, usable values are in the (16, 96) range. this affects the last pass in the slice trimming procedure, any previously detected slices that are followed by a slice at less distance than this param will be ignored.'
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
        svg_suffix = f"_{args.projection_axis}_{args.slicing_axis or args.projection_axis}" if args.slices != None else ""
        svg_name = f'{os.path.basename(args.file).split(".")[0]}{svg_suffix}.svg'
        args.dest = os.path.join(svg_path, svg_name)

    dest_dir = os.path.dirname(args.dest) or '.'
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir, exist_ok=True)

    converter.convert(args.file, args.dest, args)

    sys.exit(0)


if __name__ == '__main__':
    main()
