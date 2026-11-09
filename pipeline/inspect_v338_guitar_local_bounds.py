import bpy
from mathutils import Vector

for name in ("V206_BODY_CORE", "V318_BODY_REVEAL", "V206_NECK", "V206_FRETBOARD"):
    obj = bpy.data.objects[name]
    points = [Vector(corner) for corner in obj.bound_box]
    lo = [min(point[i] for point in points) for i in range(3)]
    hi = [max(point[i] for point in points) for i in range(3)]
    print("LOCAL_BOUNDS", name, lo, hi, "location", list(obj.location))
