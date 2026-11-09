from pathlib import Path
import bpy,json
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
s=bpy.context.scene
assert not bpy.app.is_job_running('RENDER')
g=bpy.data.objects['V206_GUITAR_ROOT']
request={'output':'production_v401_guitar_controls/v401_pick_close.png','resolution':[720,640],'samples':24,'scale':.23,'camera':list(g.matrix_world@Vector((.68,.28,.42))),'target':list(g.matrix_world@Vector((.68,-.035,.035)))}
(ROOT/'pipeline/render_preview_request.json').write_text(json.dumps(request))
exec(compile((ROOT/'pipeline/render_preview_job.py').read_text(),str(ROOT/'pipeline/render_preview_job.py'),'exec'))
