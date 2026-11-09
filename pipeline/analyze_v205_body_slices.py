import bpy


body = bpy.data.objects["V202_BODY"]
for lo, hi in ((0.00, 0.12), (0.12, 0.28), (0.28, 0.45), (0.45, 0.70), (0.70, 0.95), (0.95, 1.10), (1.10, 1.30), (1.30, 1.50)):
    points = [body.matrix_world @ vertex.co for vertex in body.data.vertices if lo <= (body.matrix_world @ vertex.co).z < hi]
    if points:
        print(
            f"SLICE {lo:.2f}-{hi:.2f} "
            f"x={min(point.x for point in points):.3f}..{max(point.x for point in points):.3f} "
            f"y={min(point.y for point in points):.3f}..{max(point.y for point in points):.3f} n={len(points)}"
        )
