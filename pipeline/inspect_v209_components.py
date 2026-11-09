import bpy

for name in ("V209_FRETTING_HAND_CONTINUOUS", "V209_PICKING_HAND_CONTINUOUS", "V209_SLEEVES_CONTINUOUS"):
    obj = bpy.data.objects[name]
    adjacency = [[] for _ in obj.data.vertices]
    for edge in obj.data.edges:
        a, b = edge.vertices
        adjacency[a].append(b)
        adjacency[b].append(a)
    unseen = set(range(len(adjacency)))
    sizes = []
    while unseen:
        seed = unseen.pop()
        stack = [seed]
        members = [seed]
        while stack:
            current = stack.pop()
            for neighbor in adjacency[current]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    stack.append(neighbor)
                    members.append(neighbor)
        coords = [obj.data.vertices[index].co for index in members]
        sizes.append((len(members), [round(sum(v[axis] for v in coords) / len(coords), 4) for axis in range(3)]))
    print(name, len(obj.data.vertices), sorted(sizes, reverse=True)[:20])
