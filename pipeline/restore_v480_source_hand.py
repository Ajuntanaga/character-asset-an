import bpy,json
from pathlib import Path
assert not bpy.app.is_job_running('RENDER')
s=bpy.data.scenes['V480_SOURCE_REVIEW']
main=next(x for x in bpy.data.scenes if x!=s and x.objects.get('V357_CLOUDRIG_CONTROLS'))
bpy.context.window.scene=main
for o in list(s.objects):bpy.data.objects.remove(o,do_unlink=True)
bpy.data.scenes.remove(s)
r=bpy.data.objects['V357_CLOUDRIG_CONTROLS'];assert len(r.animation_data.drivers)==1957
p=Path('/home/ajuntanaga/Projects/Blender/Character Asset_An/production_v480_hand_source_review/restored.json')
p.write_text(json.dumps({'scene':main.name,'file':bpy.data.filepath,'drivers':1957,'review_scene_removed':True},indent=2));print(p.read_text())
