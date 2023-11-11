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

def get_clustered_floor_heights(zvalues):
    clusters = []
    # TODO Configurable parameters with default values
    eps = 32
    floor_threshold = 0.012
    points_sorted = sorted(zvalues)
    curr_point = points_sorted[0]
    curr_cluster = [curr_point]
    max_len = 0
    for point in IncrementalBar('Clustering floors', suffix='%(index)d/%(max)d [%(elapsed_td)s / %(eta_td)s]').iter(points_sorted[1:]):
        if point <= curr_point + eps:
            curr_cluster.append(point)
        else:
            clusters.append(curr_cluster)
            max_len = max(max_len, len(curr_cluster))
            curr_cluster = [point]
        curr_point = point
    clusters.append(curr_cluster)

    trimmed_clusters = []
    for cluster in clusters:
        if len(cluster) / max_len > floor_threshold:
            trimmed_clusters.append(cluster[0])

    return trimmed_clusters

def convert(bsp_file, svg_file, args):
    """Renders the given bsp file to an svg file.

    Args:
        bsp_file: A file path to the bsp file to read.

        svg_file: A file path to the svg file to write.

        args: An argsparse args object with additional arguments.
    """
    print(f'Reading {os.path.basename(bsp_file)}')
    bsp_file = Bsp.open(bsp_file)

    # Determine map bounds
    vs = [vertex[:] for model in bsp_file.models for face in model.faces for vertex in face.vertexes]
    xs = [v[0] for v in vs]
    ys = [v[1] for v in vs]
    zs = [int(v[2]) for v in vs]

    floors = list(map(lambda s: float(s), args.floors)) if len(args.floors) > 0 else get_clustered_floor_heights(zs)

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

    dwg.add(
        dwg.rect(
            insert=(min_x - padding, min_y - padding),
            size=(width + padding * 2, height + padding * 2),
            fill='#fff'
        )
    )

    crt_index = 0
    dwg_tuples = []
    for f in floors:
        group = dwg.g(
            id='bsp_ref_%i' % crt_index,
        )
        dwg.defs.add(group)
        crt_index += 1
        dwg_tuples.append((f, group))

    ignore_textures = ['clip', 'hint', 'trigger'] + args.ignore
    faces = [face for model in bsp_file.models for face in model.faces]
    faces.sort(key=lambda f: f.vertexes[0].z)

    for face in IncrementalBar('Converting', suffix='%(index)d/%(max)d [%(elapsed_td)s / %(eta_td)s]').iter(faces):
        texture_name = face.texture_name
        if texture_name.startswith('sky') or texture_name in ignore_textures:
            continue

        # Process the vertices into points
        points = [v[:2] for v in face.vertexes]
        points = list(map(lambda p: (p[0], max_y - p[1] + min_y), points))
        points = [tuple(map(simplify_number, p)) for p in points]

        # Draw the polygon
        was_added = False
        for i in range(len(dwg_tuples) - 1):
            crt_floor_z = dwg_tuples[i][0]
            next_floor_z = dwg_tuples[i+1][0]
            crt_face_z = face.vertexes[0].z
            if crt_face_z >= crt_floor_z and crt_face_z < next_floor_z:
                crt_group = dwg_tuples[i][1]
                crt_group.add(dwg.polygon(points))
                was_added = True
                break
        if was_added == False:
            dwg_tuples[len(dwg_tuples) - 1][1].add(dwg.polygon(points))

    for i in range(len(dwg_tuples)):
        color_val = 70 + 30 * (i+1)/len(dwg_tuples)

        group = dwg.g()
        group.add(
            dwg.use(
                href='#bsp_ref_%i' % i,
                fill='none',
                stroke='black',
                stroke_width='15',
                stroke_miterlimit='0'
                # defaults to 4
                # 3 & 4 shows nasty pointy bits on some corners
                # 2 takes care care of most of those bits
                # 0 & 1 takes care of all bits, but tapers some corners
            )
        )
        group.add(
            dwg.use(
                href='#bsp_ref_%i' % i,
                fill=svgwrite.rgb(color_val, color_val, color_val, '%'),
                stroke='black',
                stroke_width='1'
            )
        )
        dwg.add(group)

    print(f'Writing {os.path.basename(svg_file)}')
    dwg.save()
    print('Done')
