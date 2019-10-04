import svgwrite

from .api import Bsp, subtract, cross


def i(number):
    return int(number) if int(number) == number else number


def convert(bsp_file, svg_file):
    bsp_file = Bsp.open(bsp_file)

    vs = [vertex[:] for model in bsp_file.models for face in model.faces for vertex in face.vertexes]
    xs = [v[0] for v in vs]
    ys = [v[1] for v in vs]

    min_x = min(xs)
    max_x = max(xs)
    min_y = min(ys)
    max_y = max(ys)

    width = max_x - min_x
    height = max_y - min_y
    padding_x = width // 10
    padding_y = height // 10

    dwg = svgwrite.Drawing(
        svg_file,
        size=(width + padding_x * 2, height + padding_y * 2),
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
            vertexes = face.vertexes

            if face.plane.normal[2] == 0:
                continue

            # Transform 3D into 2D!
            points = [tuple(v[:2]) for v in vertexes]
            points = list(map(lambda x: (i(x[0] - (min_x - padding_x)), i(x[1] - (min_y - padding_y))), points))
            points = list(map(lambda x: (x[0] * -1 + int(dwg.attribs['width']), x[1]), points))

            # Check if this polygon already exists
            edges = list(zip(points, (points[1:] + [points[0]])))
            polygon = {*edges}
            reversed_polygon = {tuple(reversed(edge)) for edge in edges}
            if polygon in drawn_polygons or reversed_polygon in drawn_polygons:
                continue

            drawn_polygons.append(polygon)

            # Draw the polygon
            group.add(
                dwg.polygon(points)
            )

    dwg.save()
