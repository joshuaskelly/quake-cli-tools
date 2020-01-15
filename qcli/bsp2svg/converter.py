import os

import svgwrite
from progress.bar import IncrementalBar

from .api import Bsp


def simplify_number(number):
    """Will convert the given number to an integer if number has not fractional
    part.

    Args:
        number: The number to convert to an integer.

    Returns:
        A number.
    """
    return int(number) if int(number) == number else number


def convert(bsp_file, svg_file):
    """Renders the given bsp file to an svg file.

    Args:
        bsp_file: A file path to the bsp file to read.

        svg_file: A file path to the svg file to write.
    """
    print(f'Reading {os.path.basename(bsp_file)}')
    bsp_file = Bsp.open(bsp_file)

    # Determine map bounds
    vs = [vertex[:] for model in bsp_file.models for face in model.faces for vertex in face.vertexes]
    xs = [v[0] for v in vs]
    ys = [v[1] for v in vs]

    min_x = min(xs)
    max_x = max(xs)
    min_y = min(ys)
    max_y = max(ys)

    width = max_x - min_x
    height = max_y - min_y
    padding = min(width // 10, height // 10)

    dwg = svgwrite.Drawing(
        svg_file,
        viewBox=f'{min_x - padding} {min_y - padding} {width + padding * 2} {height + padding * 2}',
        profile='tiny'
    )

    group = dwg.g(
        id='bsp_ref',
    )
    dwg.defs.add(group)

    faces = [face for model in bsp_file.models for face in model.faces]

    for face in IncrementalBar('Converting', suffix='%(index)d/%(max)d [%(elapsed_td)s / %(eta_td)s]').iter(faces):
        if face.texture_name.startswith('sky'):
            continue

        # Process the vertices into points
        points = [v[:2] for v in face.vertexes]
        points = list(map(lambda p: (p[0], max_y - p[1] + min_y), points))
        points = [tuple(map(simplify_number, p)) for p in points]

        # Draw the polygon
        group.add(dwg.polygon(points))

    dwg.add(
        dwg.use(
            href='#bsp_ref',
            fill='none',
            stroke='black',
            stroke_width='15'
        )
    )

    dwg.add(
        dwg.use(
            href='#bsp_ref',
            fill='white',
            stroke='black',
            stroke_width='1'
        )
    )

    print(f'Writing {os.path.basename(svg_file)}')
    dwg.save()
    print('Done')
