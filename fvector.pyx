#import pyximport; pyximport.install()

#import math
cimport cython
from libc.stdint cimport int64_t, uint64_t
from cpython.sequence cimport PySequence_Check
from libc.math cimport sqrt, cos, sin, acos, pi

#python setup.py build_ext --inplace

cdef inline int _extract(object o, double *x, double *y) except -1:
    cdef int64_t l
    if isinstance(o, Vector):
        x[0] = (<Vector> o).x
        y[0] = (<Vector> o).y
        return 1

    if not PySequence_Check(o):
        return 0
    if len(o) != 2:
        raise TypeError("Tuple was not of length 2")

    x[0] = <double?> o[0]
    y[0] = <double?> o[1]
    return 1


@cython.freelist(32)
cdef class Vector:
    cdef public double x, y

    def __cinit__(self, *args):
        if len(args) == 2:
            self.x = <double?> args[0]
            self.y = <double?> args[1]
            return
        elif len(args) == 1:
            if _extract(args[0], &self.x, &self.y):
                return
        elif len(args) == 0:
            self.x = .0
            self.y = .0
            return
        raise TypeError(
            "Expected a vector object or tuple, or x and y parameters"
        )

#    def __iter__(self):
#        return self

    def __getitem__(self, int key):
        return self.x if key == 0 else self.y

    def __len__(self):
        return 2

    def set(self, object iterable):
        self.x = iterable[0]
        self.y = iterable[1]

    def add(self, object vec):
        self.x += vec[0]
        self.y += vec[1]

    def sub(self, object vec):
        self.x -= vec[0]
        self.y -= vec[1]

    def mult(self, object vec):
        self.x *= vec[0]
        self.y *= vec[1]

    def div(self, object vec):
        try:
            self.x /= vec[0]
            self.y /= vec[1]
        except ZeroDivisionError:
            print("No div by 0")

    def flip(self):  # forgot the real name for this...
        self.x = 1. / self.x
        self.y = 1. / self.y

    def getDis(self, object vec):
        dis = Vector()
        dis.set(self)
        dis.sub(vec)
        return dis.getMag()

    def normalize(self):
        self.setMag(1)

    def getMag(self):
        return sqrt(self.x * self.x + self.y * self.y)

    def setMag(self, double mag):
        mag = mag / self.getMag()
        self.mult(Vector(mag, mag))

    def limitMag(self, double max_mag):
        mag = self.getMag()
        if mag > max_mag:
            mag *= max_mag
            self.div((mag, mag))

    def dot(self, object vec):
        return (self.x * vec[0]) + (vec[1] * self.y)

    def getProjection(self, object vec):
        """ projects vec onto self """
        cdef double p
        p = self.dot(vec) / (self.getMag() ** 2)
        proj = Vector(self.x, self.y)
        proj.mult((p, p))
        return proj

    def getReciprocal(self):
        """ rot 90 """
        return Vector(self.y, -1 * self.x)

    def rotate(self, a, (double, double) c=(.0, .0), double degree=0):
        self.sub(c)
        a = a / (180.0 / pi) if degree else a
        x = (self.x * cos(a)) - (self.y * sin(a))
        y = (self.x * sin(a)) + (self.y * cos(a))
        self.set((x, y))
        self.add(c)

    def getAngleDiff(self, object vec):
        val = self.dot(vec) / (self.getMag() * vec.getMag())
        val = max(min(val, 1), -1)
        angle = acos(val)  # in radians
        return angle

    def scale(self, double scale, (double, double) c=(.0, .0)):
        self.sub(c)
        self.mult(scale)
        self.add(c)

    def __repr__(self):
        return "Vec = [x: {}, y: {}]".format(self.x, self.y)
