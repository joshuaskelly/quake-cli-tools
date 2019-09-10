import svgwrite

from .api import Bsp


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

    group = dwg.g()
    dwg.add(group)

    for model in bsp_file.models:
        for face in model.faces:
            vertexes = face.vertexes

            # Disregard vertical faces
            #a = np.subtract(vertexes[0][:], vertexes[1][:])
            #b = np.subtract(vertexes[0][:], vertexes[2][:])
            #normal = np.cross(a, b)
            #if normal[2] == 0:
            #    continue

            # Transform 3D into 2D!
            points = [tuple(v[:2]) for v in vertexes]
            points = list(map(lambda x: (x[0] - (min_x - padding_x), x[1] - (min_y - padding_y)), points))

            group.add(
                dwg.polygon(
                    points,
                    stroke=svgwrite.rgb(0, 0, 0, '%'),
                    stroke_width=1,
                    fill='none'
                )
            )

    dwg.save()
