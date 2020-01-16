"""Command line utility for creating and manipulating WAD files

Supported Games:
    - QUAKE
"""

import argparse
import io
import os
import struct
import sys

from PIL import Image

from vgio import quake
from vgio.quake import lmp, wad

import qcli
from qcli.common import Parser, ResolvePathAction, read_from_stdin


def main():
    """CLI entrypoint"""

    # Create and configure argument parser
    parser = Parser(
        prog='wad',
        description='Default action is to add or replace wad file entries from'
            ' list.\nIf list is omitted, wad will use stdin.',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog='example:\n  wad tex.wad image.png => adds image.png to tex.wad'
    )

    parser.add_argument(
        'file',
        metavar='file.wad',
        action=ResolvePathAction,
        help='wad file to add entries to'
    )

    parser.add_argument(
        'list',
        nargs='*',
        action=ResolvePathAction,
        default=read_from_stdin()
    )

    parser.add_argument(
        '-t',
        dest='type',
        default='MIPTEX',
        choices=['LUMP', 'QPIC', 'MIPTEX'],
        help='list data type [default: MIPTEX]'
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
        version='{} version {}'.format(parser.prog, qcli.__version__)
    )

    # Parse the arguments
    args = parser.parse_args()

    if not args.list:
        parser.error('the following arguments are required: list')

    if args.quiet:
        def log(message):
            pass

    else:
        def log(message):
            print(message)

    # Ensure directory structure
    dir = os.path.dirname(args.file) or '.'
    os.makedirs(dir, exist_ok=True)

    filemode = 'a'
    if not os.path.isfile(args.file):
        filemode = 'w'

    with wad.WadFile(args.file, filemode) as wad_file:
        log(f'Archive: {os.path.basename(args.file)}')

        # Flatten out palette
        palette = []
        for p in quake.palette:
            palette += p

        # Create palette image for Image.quantize()
        palette_image = Image.frombytes('P', (16, 16), bytes(palette))
        palette_image.putpalette(palette)

        # Process input files
        for file in args.list:
            if args.type == 'LUMP':
                log(f'  adding: {file}')
                wad_file.write(file)

            elif args.type == 'QPIC':
                img = Image.open(file).convert(mode='RGB')
                img = img.quantize(palette=palette_image)
                pixels = img.tobytes()
                name = os.path.basename(file).split('.')[0]

                qpic = lmp.Lmp()
                qpic.width = img.width
                qpic.height = img.height
                qpic.pixels = pixels

                buff = io.BytesIO()
                lmp.Lmp.write(buff, qpic)
                file_size = buff.tell()
                buff.seek(0)

                info = wad.WadInfo(name)
                info.file_size = file_size
                info.disk_size = info.file_size
                info.compression = wad.CompressionType.NONE
                info.type = wad.LumpType.QPIC

                log(f'  adding: {file}')

                wad_file.writestr(info, buff)

            else:
                try:
                    img = Image.open(file).convert(mode='RGB')
                    img = img.quantize(palette=palette_image)

                    name = os.path.basename(file).split('.')[0]

                    mip = wad.Miptexture()
                    mip.name = name
                    mip.width = img.width
                    mip.height = img.height
                    mip.offsets = [40]
                    mip.pixels = []

                    # Build mip maps
                    for i in range(4):
                        resized_image = img.resize((img.width // pow(2, i), img.height // pow(2, i)))
                        data = resized_image.tobytes()
                        mip.pixels += struct.unpack(f'<{len(data)}B', data)
                        if i < 3:
                            mip.offsets += [mip.offsets[-1] + len(data)]

                    buff = io.BytesIO()
                    wad.Miptexture.write(buff, mip)
                    buff.seek(0)

                    info = wad.WadInfo(name)
                    info.file_size = 40 + len(mip.pixels)
                    info.disk_size = info.file_size
                    info.compression = wad.CompressionType.NONE
                    info.type = wad.LumpType.MIPTEX

                    log(f'  adding: {file}')

                    wad_file.writestr(info, buff)

                except:
                    parser.error(sys.exc_info()[1])

    sys.exit(0)


if __name__ == '__main__':
    main()
