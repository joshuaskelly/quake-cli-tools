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


def convert(bsp_file, svg_file, args):
    """Renders the given bsp file to an svg file.

    Args:
        bsp_file: A file path to the bsp file to read.

        svg_file: A file path to the svg file to write.

        args: An argsparse args object with additional arguments.
    """
    print(f"Reading {os.path.basename(bsp_file)}")
    bsp_file = Bsp.open(bsp_file)
    projection_axis = args.projection_axis

    # Filter faces
    faces = [face for model in bsp_file.models for face in model.faces]
    ignore_textures = ["clip", "hint", "trigger"] + args.ignore
    faces = list(
        filter(
            lambda f: not (
                f.texture_name.startswith("sky") or f.texture_name in ignore_textures
            ),
            faces,
        )
    )

    # Determine map bounds
    vs = [vertex[:] for face in faces for vertex in face.vertexes]
    xs = [v[0] for v in vs]
    ys = [v[1] for v in vs]
    zs = [v[2] for v in vs]

    drawing_xs = xs if projection_axis in ["y", "z"] else ys
    drawing_ys = zs if projection_axis in ["x", "y"] else ys
    drawing_min_x = min(drawing_xs)
    drawing_max_x = max(drawing_xs)
    drawing_min_y = min(drawing_ys)
    drawing_max_y = max(drawing_ys)

    width = drawing_max_x - drawing_min_x
    height = drawing_max_y - drawing_min_y
    padding = min(width // 10, height // 10)

    dwg = svgwrite.Drawing(
        svg_file,
        viewBox=f"{drawing_min_x - padding} {drawing_min_y - padding} {width + padding * 2} {height + padding * 2}",
        profile="tiny",
    )

    dwg.add(
        dwg.rect(
            id="background",
            insert=(drawing_min_x - padding, drawing_min_y - padding),
            size=(width + padding * 2, height + padding * 2),
            fill="#fff",
        )
    )

    group = dwg.g(id="bsp_ref")
    dwg.defs.add(group)

    if projection_axis == "x":
        faces.sort(key=lambda f: f.vertexes[0].x)
    elif projection_axis == "y":
        faces.sort(key=lambda f: f.vertexes[0].y)
    elif projection_axis == "z":
        faces.sort(key=lambda f: f.vertexes[0].z)

    def vs_picker(vertexes):
        if projection_axis == "x":
            return vertexes[1:3]
        elif projection_axis == "y":
            return vertexes[0], vertexes[2]
        elif projection_axis == "z":
            return vertexes[:2]

    for face in IncrementalBar(
        "Converting", suffix="%(index)d/%(max)d [%(elapsed_td)s / %(eta_td)s]"
    ).iter(faces):
        # Process the vertices into points
        points = [vs_picker(v) for v in face.vertexes]
        points = list(
            map(lambda p: (p[0], drawing_max_y - p[1] + drawing_min_y), points)
        )
        points = [tuple(map(simplify_number, p)) for p in points]

        # Draw the polygon
        group.add(dwg.polygon(points))

    dwg.add(
        dwg.use(
            href="#bsp_ref",
            fill="none",
            stroke="black",
            stroke_width="15",
            stroke_miterlimit="0"
            # stroke_miterlimit defaults to 4
            # 3 & 4 shows nasty pointy bits on some corners
            # 2 takes care care of most (but not all) of those bits
            # 0 & 1 takes care of all bits, but tapers some corners
        )
    )

    dwg.add(dwg.use(href="#bsp_ref", fill="white", stroke="black", stroke_width="1"))

    print(f"Writing {os.path.basename(svg_file)}")
    dwg.save()
    print("Done")
