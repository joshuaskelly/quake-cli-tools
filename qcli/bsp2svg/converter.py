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

def get_clustered_floor_heights(zvalues, parameters):
    clusters = []
    floor_threshold = parameters[0]
    fake_floor_ratio = parameters[1]
    floor_merge_threshold = parameters[2]
    zvalues_sorted = sorted(zvalues)
    crt_point = zvalues_sorted[0]
    crt_cluster = [crt_point]
    max_len = 0
    for point in IncrementalBar('Clustering floors', suffix='%(index)d/%(max)d [%(elapsed_td)s / %(eta_td)s]').iter(zvalues_sorted[1:]):
        if point - crt_point <= floor_threshold:
            crt_cluster.append(point)
        else:
            clusters.append(crt_cluster)
            max_len = max(max_len, len(crt_cluster))
            crt_cluster = [point]
        crt_point = point
    clusters.append(crt_cluster)

    initial_clusters = list(map(lambda s: (s[0], len(s)/max_len), clusters))
    print("initial clusters: %s" % initial_clusters)

    floors_trimmed = []
    for cluster in clusters:
        if len(cluster) / max_len > fake_floor_ratio:
            floors_trimmed.append(cluster[0])
    print("floors after trimming: %s" % floors_trimmed)

    floors_merged = []
    crt_height = floors_trimmed[0]
    for floor in floors_trimmed:
        if floor - crt_height > floor_merge_threshold:
            floors_merged.append(floor)
        crt_height = floor

    top_height = zvalues_sorted[len(zvalues) - 1]
    print("will also include bottom and ceiling: %i, %i" % (zvalues_sorted[0], top_height))
    floors_merged.insert(0, zvalues_sorted[0])
    floors_merged.append(top_height)
    print("floors after merging: %s" % floors_merged)


    return floors_merged

def convert(bsp_file, svg_file, args):
    """Renders the given bsp file to an svg file.

    Args:
        bsp_file: A file path to the bsp file to read.

        svg_file: A file path to the svg file to write.

        args: An argsparse args object with additional arguments.
    """
    print(f'Reading {os.path.basename(bsp_file)}')
    bsp_file = Bsp.open(bsp_file)
    projection_axis = args.axis

    # Filter faces
    faces = [face for model in bsp_file.models for face in model.faces]
    ignore_textures = ['clip', 'hint', 'trigger'] + args.ignore
    faces = list(filter(lambda f: not (f.texture_name.startswith('sky') or f.texture_name in ignore_textures), faces))

    # Determine map bounds
    vs = [vertex[:] for face in faces for vertex in face.vertexes]
    xs = [v[0] for v in vs]
    ys = [v[1] for v in vs]
    zs = [v[2] for v in vs]

    # Filter face with type2 plane (axial plane aligned to the z-axis)
    zfaces = list(filter(lambda f: f.plane.type == 2, faces))
    zheights = [int(face.plane.distance) for face in zfaces]
    # zheights = [vertex[:][2] for face in zfaces for vertex in face.vertexes]
    floors = args.floors if len(args.floors) > 0 else get_clustered_floor_heights(zheights, args.params)

    drawing_xs = xs if projection_axis in ['y', 'z'] else ys
    drawing_ys = zs if projection_axis in ['x', 'y'] else ys
    drawing_min_x = min(drawing_xs)
    drawing_max_x = max(drawing_xs)
    drawing_min_y = min(drawing_ys)
    drawing_max_y = max(drawing_ys)

    width = drawing_max_x - drawing_min_x
    height = drawing_max_y - drawing_min_y
    padding = min(width // 10, height // 10)

    dwg = svgwrite.Drawing(
        svg_file,
        viewBox=f'{drawing_min_x - padding} {drawing_min_y - padding} {width + padding * 2} {height + padding * 2}',
        profile='tiny'
    )

    dwg.add(
        dwg.rect(
            id='background',
            insert=(drawing_min_x - padding, drawing_min_y - padding),
            size=(width + padding * 2, height + padding * 2),
            fill='#fff'
        )
    )

    dwg_tuples = []
    for i in range(len(floors)):
        group = dwg.g(
            id='bsp_ref_%i' % i,
        )
        dwg.defs.add(group)
        dwg_tuples.append((floors[i], group))

    complete_group = dwg.g(
        id='bsp_complete_ref',
    )
    dwg.defs.add(complete_group)

    if projection_axis == 'x':
        faces.sort(key=lambda f: f.vertexes[0].x)
    elif projection_axis == 'y':
        faces.sort(key=lambda f: f.vertexes[0].y)
    elif projection_axis == 'z':
        faces.sort(key=lambda f: f.vertexes[0].z)
    
    def vs_picker(vertexes):
        if projection_axis == 'x':
            return vertexes[1:3]
        elif projection_axis == 'y':
            return [vertexes[0], vertexes[2]]
        elif projection_axis == 'z':
            return vertexes[:2]
        else: return []

    for face in IncrementalBar('Converting', suffix='%(index)d/%(max)d [%(elapsed_td)s / %(eta_td)s]').iter(faces):
        # Process the vertices into points
        points = [vs_picker(v) for v in face.vertexes]
        points = list(map(lambda p: (p[0], drawing_max_y - p[1] + drawing_min_y), points))
        points = [tuple(map(simplify_number, p)) for p in points]

        # Draw the complete polygon
        # TODO Find a way to create the complete polygon and avoid doubling everything
        # complete_group.add(dwg.polygon(points))

        was_added = False
        # Find the correct layer to draw on, based on height
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
            # if a face was not added until this point, it goes into to the last group
            last_tuple = dwg_tuples[len(dwg_tuples) - 1]
            last_tuple[1].add(dwg.polygon(points))

    for i in range(len(dwg_tuples)):
        # use multiple shades, from 70% gray to white
        color_val = 70 + 30 * (i+1)/len(dwg_tuples)

        group = dwg.g(
            id='height_%i' % dwg_tuples[i][0],
        )
        group.add(
            dwg.use(
                href='#bsp_ref_%i' % i,
                fill='none',
                stroke='black',
                stroke_width='15',
                stroke_miterlimit='0'
                # defaults to 4
                # 3 & 4 shows nasty pointy bits on some corners
                # 2 takes care care of most (but not all) of those bits
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

    group = dwg.g(id="complete")
    group.add(
        dwg.use(
            href='#bsp_complete_ref',
            fill='none',
            stroke='black',
            stroke_width='15',
            stroke_miterlimit='0'
        )
    )
    group.add(
        dwg.use(
            href='#bsp_complete_ref',
            fill='white',
            stroke='black',
            stroke_width='1'
        )
    )
    dwg.add(group)

    print(f'Writing {os.path.basename(svg_file)}')
    dwg.save()
    print('Done')
