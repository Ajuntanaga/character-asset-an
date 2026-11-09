"""Replace the faceted collar assignment with a rest-space shader boundary."""
from pathlib import Path
import bpy,json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'production_v390_collar_boundary'
OUT.mkdir(exist_ok=True)
assert not bpy.app.is_job_running('RENDER')
body=bpy.data.objects['V357_TRIPO_CHARACTER_BODY_BOUND']
rig=bpy.data.objects['V357_CLOUDRIG_CONTROLS']
assert len(rig.animation_data.drivers)==1957
assert not body.get('V390_applied')
mat=bpy.data.materials['V379_MUTED_PATTERN_SHIRT'].copy()
mat.name='V390_CONTINUOUS_COLLAR'
nodes,links=mat.node_tree.nodes,mat.node_tree.links
src=bpy.data.materials['V377_REFERENCE_PHOTO_SKIN'].node_tree
copies={}
for old in src.nodes:
    if old.type=='OUTPUT_MATERIAL': continue
    new=nodes.new(old.bl_idname)
    for prop in old.bl_rna.properties:
        key=prop.identifier
        if prop.is_readonly or key in {'name','location','parent'}: continue
        try: setattr(new,key,getattr(old,key))
        except (TypeError,AttributeError,ValueError): pass
    new.name='V390_SKIN_'+old.name
    for a,b in zip(old.inputs,new.inputs):
        if hasattr(a,'default_value'):
            try: b.default_value=a.default_value
            except (TypeError,AttributeError,ValueError): pass
    copies[old.name]=new
for link in src.links:
    if link.from_node.name in copies and link.to_node.name in copies:
        oi=list(link.from_node.outputs).index(link.from_socket)
        ii=list(link.to_node.inputs).index(link.to_socket)
        links.new(copies[link.from_node.name].outputs[oi],copies[link.to_node.name].inputs[ii])
a=nodes.new('ShaderNodeAttribute');a.attribute_name='V372_RestPosition'
s=nodes.new('ShaderNodeSeparateXYZ');links.new(a.outputs['Vector'],s.inputs[0])
def mathop(op,*vals):
    n=nodes.new('ShaderNodeMath');n.operation=op
    for i,v in enumerate(vals):
        if isinstance(v,(float,int)): n.inputs[i].default_value=v
        else: links.new(v,n.inputs[i])
    return n.outputs[0]
x=mathop('ABSOLUTE',s.outputs['X'])
zcut=mathop('MULTIPLY_ADD',x,.12,1.474)
d=mathop('SUBTRACT',s.outputs['Z'],zcut)
f=nodes.new('ShaderNodeMapRange');f.clamp=True;f.interpolation_type='SMOOTHSTEP'
links.new(d,f.inputs['Value']);f.inputs['From Min'].default_value=-.00035;f.inputs['From Max'].default_value=.00035
mix=nodes.new('ShaderNodeMixShader')
links.new(f.outputs[0],mix.inputs[0]);links.new(nodes['Principled BSDF'].outputs[0],mix.inputs[1]);links.new(copies['Principled BSDF'].outputs[0],mix.inputs[2]);links.new(mix.outputs[0],nodes['Material Output'].inputs['Surface'])
body.data.materials.append(mat);slot=len(body.data.materials)-1
basis=body.data.shape_keys.key_blocks['Basis'].data
backup=[]
for p in body.data.polygons:
    if p.material_index not in (0,4,5,7): continue
    pts=[basis[i].co for i in p.vertices]
    if any(1.459<v.z<1.494 and abs(v.x)<.064 and v.y<-.035 for v in pts):
        backup.append([p.index,p.material_index]);p.material_index=slot
body.data.update();body['V390_applied']=True
assert len(rig.animation_data.drivers)==1957
(OUT/'report.json').write_text(json.dumps({'polygons':len(backup),'original_materials':backup,'drivers':1957},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Character_An_collar_boundary_v390.blend'),compress=True)
print(json.dumps({'polygons':len(backup),'drivers':1957}))
