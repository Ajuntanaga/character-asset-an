from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v482_joint_width'
(out/'mode.txt').write_text('curl')
p=root/'pipeline/check_v472_hand_deformation.py';s=p.read_text().replace('production_v472_hand_deformation','production_v482_joint_width')
exec(compile(s,str(p),'exec'),dict(globals(),__file__=str(p)))
