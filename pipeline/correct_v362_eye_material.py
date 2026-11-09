import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'production_v362_face_anatomy'
mat=bpy.data.materials['V362_BROWN_PROCEDURAL_EYE']
group_node=next(n for n in mat.node_tree.nodes if n.type=='GROUP')
if group_node.node_tree.name=='Eyeball':
    group_node.node_tree=group_node.node_tree.copy();group_node.node_tree.name='V362_METRIC_EYEBALL'
group=group_node.node_tree
report=[]
for n in group.nodes:
    if n.type=='BUMP':
        n.inputs['Distance'].default_value=.000015
        if not n.inputs['Strength'].is_linked:n.inputs['Strength'].default_value=.12
    if n.type=='BSDF_PRINCIPLED':
        for name,value in [('Roughness',.24),('Subsurface Weight',.035),('Subsurface Scale',.001),('Coat Weight',.16),('Coat Roughness',.055),('Specular IOR Level',.35)]:
            if name in n.inputs:
                for link in list(n.inputs[name].links):group.links.remove(link)
                n.inputs[name].default_value=value
        for link in list(n.inputs['Normal'].links):group.links.remove(link)
        report.append({'shader':n.name,'links':[(l.from_node.name,l.from_socket.name,l.to_socket.name) for l in group.links if l.to_node==n]})
group_node.inputs['Subsurface Scattering'].default_value=.035
group_node.inputs['Blood Vessels Bump'].default_value=.025
scene=bpy.context.scene;scene.render.filepath=str(OUT/'v362_metric_eye_material.png')
bpy.ops.render.render(write_still=True)
print(json.dumps(report))
