import bpy

head = bpy.data.objects["V216_REFERENCE_FITTED_HEAD"]
for x in (0.043, -0.043):
    samples = []
    for vertex in head.data.vertices:
        point = head.matrix_world @ vertex.co
        distance = ((point.x - x) ** 2 + (point.z - 1.675) ** 2) ** 0.5
        if distance < 0.025:
            samples.append((distance, point.y, point.x, point.z))
    samples.sort()
    print(x, samples[:12])
