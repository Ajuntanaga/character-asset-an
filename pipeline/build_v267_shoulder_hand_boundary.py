"""Correct V266 shoulder coverage and exclude copied hand skin."""

from pathlib import Path

ROOT=Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
SCRIPT=ROOT/"pipeline"/"build_v266_continuous_jacket_shell.py"
ns={"__name__":"v266_library"}
exec(compile(SCRIPT.read_text(encoding="utf-8"),str(SCRIPT),"exec"),ns)
ns["STAGE"]=ROOT/"production_v267_shoulder_hand_boundary"
ns["OUTPUT"]=ns["STAGE"]/"Character_An_shoulder_hand_boundary_v267.blend"
ns["RENDERS"]=ns["STAGE"]/"renders"
ns["AUDIT"]=ns["STAGE"]/"audit"
ns["UPPER_Z"]=1.515
ns["EXCLUDE_HANDS"]=True
ns["HAND_WEIGHT_LIMIT"]=.65

if __name__=="__main__":ns["main"]()
