"""Compare the existing skin normal graph with geometric normals, without saving."""
from pathlib import Path
import json
import runpy
import bpy

root = Path(__file__).resolve().parent
head = bpy.data.objects['V740_NATIVE_FACE']
materials = [m for m in head.data.materials if m and m.use_nodes]
saved = []
report = []
for material in materials:
    for shader in material.node_tree.nodes:
        if shader.type != 'BSDF_PRINCIPLED':
            continue
        socket = shader.inputs['Normal']
        connections = [(link.from_socket, link.to_socket) for link in socket.links]
        saved.append((material.node_tree, connections))
        report.append({'material': material.name, 'shader': shader.name,
                       'normal_sources': [a.node.name for a, _ in connections],
                       'bump_nodes': [{'name': n.name,
                           'strength': float(n.inputs['Strength'].default_value),
                           'distance': float(n.inputs['Distance'].default_value)}
                           for n in material.node_tree.nodes if n.type == 'BUMP']})
assert any(links for _, links in saved), 'No skin normal input to compare'
settings = {'TEXTURE_PATH': 'Character_An_photoreal_head_basecolor_v326.png',
            'VIEWS': ['front'], 'SAMPLES': 32}
try:
    runpy.run_path(str(root / 'render_v740_cloud_groom.py'),
                   init_globals={**settings, 'TAG': 'v740_skin_normal_control'})
    for tree, connections in saved:
        for _, destination in connections:
            for link in list(destination.links):
                tree.links.remove(link)
    runpy.run_path(str(root / 'render_v740_cloud_groom.py'),
                   init_globals={**settings, 'TAG': 'v740_skin_geometric_normal'})
finally:
    for tree, connections in saved:
        for source, destination in connections:
            tree.links.new(source, destination)
restored = all(any(link.from_socket == source for link in destination.links)
               for _, connections in saved for source, destination in connections)
assert restored
Path('results/skin_normal_comparison.json').write_text(json.dumps({
    'materials': report, 'normal_connections_restored': restored,
    'scope': 'Paired frontal shading trial; geometry, albedo, lights and pose unchanged. '
             'Geometric-normal variant is diagnostic, not a finished skin material.'}, indent=2))
