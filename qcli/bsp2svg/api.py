from collections import namedtuple
from functools import lru_cache

from vgio.quake import bsp


def dot(v0, v1):
    return v0[0] * v1[0] + v0[1] * v1[1] + v0[2] * v1[2]


def cross(v0, v1):
    return v0[1] * v1[2] - v0[2] * v1[1], \
           v0[2] * v1[0] - v0[0] * v1[2], \
           v0[0] * v1[1] - v0[1] * v1[0]


def subtract(v0, v1):
    return v0[0] - v1[0], v0[1] - v1[1], v0[2] - v1[2]


__all__ = ['Bsp']


class Bsp(object):
    __slots__ = (
        'models'
    )

    def __init__(self, models):
        self.models = models

    @staticmethod
    def open(file):
        bsp_file = bsp.Bsp.open(file)
        bsp_file.close()

        def get_models():
            return [process_model(m) for m in bsp_file.models]

        def process_model(bsp_model):
            faces = get_faces(bsp_model)

            return Model(faces)

        def get_faces(bsp_model):
            start = bsp_model.first_face
            stop = start + bsp_model.number_of_faces
            face_range = range(start, stop)

            return [process_face(f) for f in face_range]

        @lru_cache(maxsize=None)
        def process_face(face_index):
            edges = get_edges(face_index)
            vertexes = get_vertexes(face_index)
            uvs = []#get_uvs(face_index)
            plane = get_plane(face_index)
            texture_name = get_texture_name(face_index)

            return Face(vertexes, edges, uvs, plane, texture_name)

        @lru_cache(maxsize=None)
        def get_edges(face_index):
            bsp_face = bsp_file.faces[face_index]
            start = bsp_face.first_edge
            stop = start + bsp_face.number_of_edges
            es = bsp_file.surf_edges[start:stop]

            result = []
            for e in es:
                v = bsp_file.edges[abs(e)].vertexes

                if e < 0:
                    v = list(reversed(v))

                v0 = process_vertex(v[0])
                v1 = process_vertex(v[1])

                result.append(Edge(v0, v1))

            return result

        @lru_cache(maxsize=None)
        def get_vertexes(face_index):
            edges = get_edges(face_index)
            return [e.vertex_0 for e in edges]

        @lru_cache(maxsize=None)
        def process_vertex(index):
            bsp_vertex = bsp_file.vertexes[index]
            return Vertex(*bsp_vertex[:])

        @lru_cache(maxsize=None)
        def get_texture_name(face_index):
            bsp_face = bsp_file.faces[face_index]
            tex_info = bsp_file.texture_infos[bsp_face.texture_info]
            miptex = bsp_file.miptextures[tex_info.miptexture_number]

            return miptex.name

        @lru_cache(maxsize=None)
        def get_uvs(face_index):
            bsp_face = bsp_file.faces[face_index]
            vertexes = get_vertexes(face_index)
            texture_info = bsp_file.texture_infos[bsp_face.texture_info]
            miptex = bsp_file.miptextures[texture_info.miptexture_number]
            s = texture_info.s
            ds = texture_info.s_offset
            t = texture_info.t
            dt = texture_info.t_offset
            w = miptex.width
            h = miptex.height

            uvs = []
            for v in vertexes:
                v = v[:]
                uv = (dot(v, s) + ds) / w, -(dot(v, t) + dt) / h
                uvs.append(uv)

            return uvs

        @lru_cache(maxsize=None)
        def get_plane(face_index):
            bsp_face = bsp_file.faces[face_index]
            return bsp_file.planes[bsp_face.plane_number]

        models = get_models()
        result = Bsp(models)

        return result


class Model(object):
    __slots__ = (
        'faces'
    )

    def __init__(self, faces):
        self.faces = faces

    @property
    @lru_cache(maxsize=None)
    def vertexes(self):
        return list(set([v for f in self.faces for v in f.vertexes]))

    @property
    @lru_cache(maxsize=None)
    def edges(self):
        return list(set([e for f in self.faces for e in f.edges]))


class Face(object):
    __slots__ = (
        'vertexes',
        'edges',
        'uvs',
        'plane',
        'texture_name'
    )

    def __init__(self, vertexes, edges, uvs, plane, texture_name):
        self.vertexes = vertexes
        self.edges = edges
        self.uvs = uvs
        self.plane = plane
        self.texture_name = texture_name


Edge = namedtuple('Edge', ['vertex_0', 'vertex_1'])


class Vertex(object):
    __slots__ = (
        'x',
        'y',
        'z'
    )

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __getitem__(self, item):
        return [self.x, self.y, self.z][item]
