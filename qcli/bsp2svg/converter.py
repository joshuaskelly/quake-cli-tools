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

def get_clustered_slices(values, args):
    clusters = []
    slice_threshold = args.detection_params[0]
    fake_slice_ratio = args.detection_params[1]
    slice_merge_threshold = args.detection_params[2]
    values_sorted = sorted(values)
    crt_point = values_sorted[0]
    crt_cluster = [crt_point]
    max_len = 0
    for point in IncrementalBar('Clustering slices', suffix='%(index)d/%(max)d [%(elapsed_td)s / %(eta_td)s]').iter(values_sorted[1:]):
        if point - crt_point <= slice_threshold:
            crt_cluster.append(point)
        else:
            clusters.append(crt_cluster)
            max_len = max(max_len, len(crt_cluster))
            crt_cluster = [point]
        crt_point = point
    clusters.append(crt_cluster)

    if not args.quiet:
        initial_clusters = list(map(lambda s: (s[0], len(s)/max_len), clusters))
        print(f'initial slice clusters: {initial_clusters}')

    slices_trimmed = []
    for cluster in clusters:
        if len(cluster) / max_len > fake_slice_ratio:
            slices_trimmed.append(cluster[0])
    if not args.quiet:
        print(f'slices after trimming: {slices_trimmed}')

    slices_merged = []
    crt_distance = slices_trimmed[0]
    for slice_distance in slices_trimmed:
        if slice_distance - crt_distance > slice_merge_threshold:
            slices_merged.append(slice_distance)
        crt_distance = slice_distance

    top_height = values_sorted[len(values) - 1]
    if not args.quiet:
        print(f'will also include bottom and ceiling: {values_sorted[0]}, {top_height}')
    slices_merged.insert(0, values_sorted[0])
    slices_merged.append(top_height)
    if not args.quiet:
        print(f'slices after merging: {slices_merged}')

    return slices_merged

def convert(bsp_file, svg_file, args):
    """Renders the given bsp file to an svg file.

    Args:
        bsp_file: A file path to the bsp file to read.

        svg_file: A file path to the svg file to write.

        args: An argsparse args object with additional arguments.
    """
    print(f'Reading {os.path.basename(bsp_file)}')
    bsp_file = Bsp.open(bsp_file)
    projection_axis = args.projection_axis
    slicing_axis = args.slicing_axis or projection_axis

    # Filter faces
    faces = [face for model in bsp_file.models for face in model.faces]
    ignore_textures = ['clip', 'hint', 'trigger'] + args.ignore
    faces = list(filter(lambda f: not (f.texture_name.startswith('sky') or f.texture_name in ignore_textures), faces))

    # Determine map bounds
    vs = [vertex[:] for face in faces for vertex in face.vertexes]
    xs = [v[0] for v in vs]
    ys = [v[1] for v in vs]
    zs = [v[2] for v in vs]

    # Filter faces by plane type (axial plane aligned to the slicing axis)
    plane_type_dict = {'x':0, 'y':1, 'z':2}
    slice_faces = list(filter(lambda f: f.plane.type == plane_type_dict[slicing_axis], faces))
    slice_distances = [int(face.plane.distance) for face in slice_faces]
    slices = []
    if args.slices == None:
        # disable slicing - everything will go on one layer
        slices = [0]
    elif len(args.slices) > 0:
        # enable slicing at user configured levels
        slices = sorted(args.slices)
    else:
        # enable slicing and automatic detection
        slices = get_clustered_slices(slice_distances, args)

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
    for i in range(len(slices)):
        group = dwg.g(id=f'bsp_ref_{i}')
        dwg.defs.add(group)
        dwg_tuples.append((slices[i], group))

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
            return vertexes[0], vertexes[2]
        elif projection_axis == 'z':
            return vertexes[:2]

    for face in IncrementalBar('Converting', suffix='%(index)d/%(max)d [%(elapsed_td)s / %(eta_td)s]').iter(faces):
        # Process the vertices into points
        points = [vs_picker(v) for v in face.vertexes]
        points = list(map(lambda p: (p[0], drawing_max_y - p[1] + drawing_min_y), points))
        points = [tuple(map(simplify_number, p)) for p in points]

        was_added = False
        # Find the correct layer to draw on, based on distance
        for i in range(len(dwg_tuples) - 1):
            if slicing_axis == 'x':
                crt_face_dist = face.vertexes[0].x
            elif slicing_axis == 'y':
                crt_face_dist = face.vertexes[0].y
            elif slicing_axis == 'z':
                crt_face_dist = face.vertexes[0].z
            if crt_face_dist >= dwg_tuples[i][0] and crt_face_dist < dwg_tuples[i+1][0]:
                crt_group = dwg_tuples[i][1]
                crt_group.add(dwg.polygon(points))
                was_added = True
                break
        if was_added == False:
            # if a face was not added until this point, it goes into to the last group
            last_tuple = dwg_tuples[len(dwg_tuples) - 1]
            last_tuple[1].add(dwg.polygon(points))
    
    complete_group_edges = dwg.g(
        id='complete_edges',
        fill='none',
        stroke='black',
        stroke_width='15',
        stroke_miterlimit='0'
        # stroke_miterlimit defaults to 4
        # 3 & 4 shows nasty pointy bits on some corners
        # 2 takes care care of most (but not all) of those bits
        # 0 & 1 takes care of all bits, but tapers some corners
    )
    complete_group_fill = dwg.g(
        id='complete_fill',
        fill='white',
        stroke='black',
        stroke_width='1',
        stroke_miterlimit='0'
    )
    for i in range(len(dwg_tuples)):
        # use multiple shades, from 70% gray to white
        color_val = 70 + 30 * (i+1)/len(dwg_tuples)

        group = dwg.g(id=f'layer_{dwg_tuples[i][0]}')
        group.add(
            dwg.use(
                href=f'#bsp_ref_{i}',
                fill='none',
                stroke='black',
                stroke_width='15',
                stroke_miterlimit='0'
            )
        )
        group.add(
            dwg.use(
                href=f'#bsp_ref_{i}',
                fill=svgwrite.rgb(color_val, color_val, color_val, '%'),
                stroke='black',
                stroke_width='1'
            )
        )
        dwg.add(group)
        complete_group_edges.add(dwg.use(href=f'#bsp_ref_{i}'))
        complete_group_fill.add(dwg.use(href=f'#bsp_ref_{i}'))

    if len(slices) > 1:
        # only add the complete group if more that one slice was detected / configured
        group = dwg.g(
            id='complete',
            display='none',
        )
        group.add(complete_group_edges)
        group.add(complete_group_fill)
        dwg.add(group)

    print(f'Writing {os.path.basename(svg_file)}')
    dwg.save()
    print('Done')
