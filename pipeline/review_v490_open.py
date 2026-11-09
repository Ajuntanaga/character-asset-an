from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'production_v490_hand_anatomy'
(out/'mode.txt').write_text('open')
p=root/'pipeline/check_v472_hand_deformation.py'
s=p.read_text().replace('production_v472_hand_deformation','production_v490_hand_anatomy')
exec(compile(s,str(p),'exec'),dict(globals(),__file__=str(p)))
