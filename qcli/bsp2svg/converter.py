import svgwrite

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


def process_vertexes(vertexes):
    """Converts vertices into points.

    Args:
        vertexes: A sequence of three-tuples.

    Returns:
        A sequence of two-tuples.
    """
    return [tuple(map(simplify_number, v[:2])) for v in vertexes]


def convert(bsp_file, svg_file):
    """Renders the given bsp file to an svg file.

    Args:
        bsp_file: A file path to the bsp file to read.

        svg_file: A file path to the svg file to write.
    """
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
        stroke='black',
        stroke_width=1,
        fill='none'
    )
    dwg.add(group)

    for model in bsp_file.models:
        drawn_polygons = []

        for face in model.faces:
            # Ignore perfectly vertical faces
            if face.plane.normal[2] == 0:
                continue

            points = process_vertexes(face.vertexes)

            # Check if this polygon already exists
            edges = list(zip(points, (points[1:] + [points[0]])))
            polygon = {*edges}
            reversed_polygon = {tuple(reversed(edge)) for edge in edges}
            if polygon in drawn_polygons or reversed_polygon in drawn_polygons:
                continue

            drawn_polygons.append(polygon)

            # Draw the polygon
            group.add(dwg.polygon(points))

    dwg.save()
