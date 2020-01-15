"""Command line utility for creating and creating image files from SPR files

Supported Games:
    - QUAKE
"""

import array
import argparse
import os
import sys

import vgio
from PIL import Image
from vgio.quake import spr

import qcli
from qcli.common import Parser
from qcli.common import ResolvePathAction

def main():
    parser = Parser(
        prog='spr2image',
        description='Default action is to convert a spr file to a gif.',
        epilog='example: spr2image bubble.spr => convert bubble.spr to bubble.gif'
    )

    parser.add_argument(
        'file',
        metavar='file.spr',
        action=ResolvePathAction
    )

    parser.add_argument(
        '-d',
        metavar='file.gif',
        dest='dest',
        default=os.getcwd(),
        action=ResolvePathAction,
        help='image file to create'
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
        version=f'{parser.prog} version {qcli.spr2image.__version__}'
    )

    args = parser.parse_args()

    # Validate source file
    if not spr.is_sprfile(args.file):
        print(f'{parser.prog}: cannot find or open {args.file}', file=sys.stderr)
        sys.exit(1)

    # Validate or create out file
    if args.dest == os.getcwd():
        image_path = os.path.dirname(args.file)
        image_name = os.path.basename(args.file).split('.')[0] + '.gif'
        args.dest = os.path.join(image_path, image_name)

    dest_dir = os.path.dirname(args.dest) or '.'
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    image_filename = os.path.basename(args.dest)
    image_extension = image_filename.split('.')[-1]

    with spr.Spr.open(args.file) as spr_file:
        if not args.quiet:
            print(f'Converting: {os.path.basename(args.file)}')

        # Flatten out palette
        palette = [channel for rgb in vgio.quake.palette for channel in rgb]

        # Default frame animation is 10 frames per second
        default_duration = 10 / 60 * 1000

        # Build a sequence of images from spr frames
        images = []
        for frame in spr_file.frames:
            if frame.type == spr.SINGLE:
                size = frame.width, frame.height
                data = array.array('B', frame.pixels)

                img = Image.frombuffer('P', size, data, 'raw', 'P', 0, 1)
                img.putpalette(palette)
                images.append(img)

            else:
                print(f'{parser.prog}: frame groups are not supported', file=sys.stderr)
                sys.exit(1)

    # Save as gif
    if image_extension.upper() == 'GIF':
        first_frame = images[0]
        first_frame.putpalette(palette)
        remaining_frames = images[1:]
        first_frame.save(
            args.dest,
            save_all=True,
            append_images=remaining_frames,
            duration=default_duration,
            loop=0,
            optimize=False,
            #transparency=255,
            palette=palette
        )

    else:
        image_directory = os.path.dirname(args.dest)
        image_name = image_filename.split('.')[0]
        for image_index, image in enumerate(images):
            filename = '{}_{}.{}'.format(image_name, image_index, image_extension)
            image.save(
                os.path.join(image_directory, filename),
                optimize=False,
                #transparency=255,
                palette=palette
            )

    sys.exit(0)

if __name__ == '__main__':
    main()
