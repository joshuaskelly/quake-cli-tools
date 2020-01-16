"""Command line utility for creating and creating SPR files from image files

Supported Games:
    - QUAKE
"""

import argparse
import os
import struct
import sys

import vgio
from PIL import Image
from vgio.quake import spr

import qcli
from qcli.common import Parser
from qcli.common import ResolvePathAction
from qcli.common import read_from_stdin


def main():
    parser = Parser(
        prog='image2spr',
        description='Default action is to convert an image file(s) to an '
            'spr.\nIf image file is omitted, image2spr will use stdin.',
        epilog='example: image2spr anim.spr anim.gif => converts anim.gif to '
            'anim.spr'
    )

    parser.add_argument(
        'dest_file',
        metavar='file.spr',
        action=ResolvePathAction,
        help='spr file to create'
    )

    parser.add_argument(
        'source_files',
        nargs='*',
        metavar='file.gif',
        action=ResolvePathAction,
        default=read_from_stdin(),
        help='image source file'
    )

    parser.add_argument(
        '-t',
        dest='type',
        default=0,
        help='sprite orientation type'
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

    # Flatten out palette
    quake_palette = [channel for rgb in vgio.quake.palette for channel in rgb]

    # Create palette image for Image.quantize()
    quake_palette_image = Image.frombytes('P', (16, 16), bytes(quake_palette))
    quake_palette_image.putpalette(quake_palette)

    images = []

    # Build a list of source images
    for source_file in args.source_files:
        if not os.path.exists(source_file):
            print(f'{parser.prog}: cannot find or open {source_file}', file=sys.stderr)
            continue

        # Open source image
        source_image = Image.open(source_file)
        size = source_image.size
        source_mode = source_image.mode
        global_transparency = source_image.info.get('transparency')

        # Decompose the source image frames into a sequence of images
        try:
            while True:
                if source_image.mode != 'P':
                    alpha = source_image.split()[-1]

                    # Set all alpha pixels to a known color
                    source_image = source_image.convert('RGB')

                    mask = Image.eval(alpha, lambda a: 255 if a <=128 else 0)
                    transparent_color = tuple(quake_palette[-3:])
                    source_image.paste(transparent_color, mask)
                    source_image.info['transparency'] = 255

                    source_image = source_image.quantize(palette=quake_palette_image)
                    source_image.putpalette(bytes(quake_palette))

                # Set the current palette's transparent color to Quake's
                local_transparency = source_image.info.get('transparency')
                source_palette = source_image.palette.palette
                source_palette = list(struct.unpack(f'{len(source_palette)}B', source_palette))

                if local_transparency:
                    source_palette[local_transparency * 3:local_transparency * 3 + 3] = vgio.quake.palette[-1]

                if global_transparency and global_transparency != local_transparency:
                    source_palette[global_transparency * 3:global_transparency * 3 + 3] = vgio.quake.palette[-1]

                source_palette = bytes(source_palette)

                # Create new image from current frame
                data = source_image.tobytes()
                sub_image = Image.frombytes('P', size, data, 'raw', 'P', 0, 1)

                if local_transparency:
                    sub_image.info['transparency'] = local_transparency

                sub_image.putpalette(source_palette)

                # Convert from indexed color to RGB color then quantize to Quake's palette
                sub_image = sub_image.convert('RGB', dither=None)
                sub_image = sub_image.quantize(palette=quake_palette_image)
                sub_image.info['transparency'] = 255
                sub_image.putpalette(bytes(quake_palette))
                images.append(sub_image)
                source_image.seek(source_image.tell() + 1)

        except EOFError:
            pass

    if not images:
        print(f'{parser.prog}: no usable source images given', file=sys.stderr)
        sys.exit(1)

    # Normalize image sizes
    if len(images) > 1:
        sizes = [image.size for image in images]

        images_all_same_size = all([size[0] == size for size in sizes])

        if not images_all_same_size:
            resized_images = []
            max_width = max([size[0] for size in sizes])
            max_height = max([size[1] for size in sizes])

            for image in images:
                resized_image = Image.new('P', (max_width, max_height), 255)
                resized_image.putpalette(bytes(quake_palette))

                top = (max_height - image.size[1]) // 2
                left = (max_width - image.size[0]) // 2
                top_left = top, left
                resized_image.paste(image, box=top_left)
                resized_images.append(resized_image)

            images = resized_images

    # Build Quake sprite
    with spr.Spr.open(args.dest_file, 'w') as spr_file:
        spr_file.width, spr_file.height = size
        spr_file.number_of_frames = len(images)
        spr_file.type = int(args.type)

        origin = -size[0] // 2, size[1] // 2

        for image in images:
            frame = spr.SpriteFrame()
            frame.width, frame.height = size
            frame.origin = origin
            data = image.tobytes()
            data = struct.unpack(f'{frame.width * frame.height}B', data)
            frame.pixels = data
            spr_file.frames.append(frame)

    sys.exit(0)


if __name__ == '__main__':
    main()
