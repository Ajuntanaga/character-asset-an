from pathlib import Path
import hashlib
import json

from pipeline.make_contact_sheet import make_sheet


ROOT = Path("/home/ajuntanaga/Projects/Blender/Character Asset_An")
STAGE = ROOT / "production_v216_conformed_character"
REF = ROOT / "production_v212_identity" / "facebuilder_refs"
RENDERS = STAGE / "renders"
DELIVERY = STAGE / "delivery"
AUDIT = STAGE / "audit"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


contact = make_sheet(
    [
        ("Reference front", REF / "facebuilder_front_neutral.png"),
        ("Reference left three quarter", REF / "facebuilder_left_3q_neutral.png"),
        ("Reference left profile", REF / "facebuilder_left_profile_neutral.png"),
        ("V216 front candidate", RENDERS / "v216_front.png"),
        ("V216 left three quarter candidate", RENDERS / "v216_left_three_quarter.png"),
        ("V216 left profile candidate", RENDERS / "v216_left_profile.png"),
    ],
    3,
    DELIVERY / "v216_identity_conformation_contact.png",
    "V216 FaceBuilder identity conformation — visual gate (candidate, not final)",
)

blend = STAGE / "Character_An_conformed_v216.blend"
record = {
    "stage": "V216_REFERENCE_FITTED_HEAD_CONFORMED_CANDIDATE",
    "output": str(blend.relative_to(ROOT)),
    "output_sha256": sha256(blend),
    "contact": str(contact.relative_to(ROOT)),
    "contact_sha256": sha256(contact),
    "facebuilder_pins": [26, 12, 23],
    "head_vertices": 18024,
    "body_vertices_after_neck_cut": 6572,
    "accepted": False,
    "remaining": [
        "likeness requires reference hair, beard, brows, eyes, and skin texture",
        "neck/body cut is intentionally wardrobe-covered and not a welded seam",
        "head and eyes require final rig attachment and deformation validation",
    ],
}
AUDIT.mkdir(parents=True, exist_ok=True)
(AUDIT / "v216_manifest.json").write_text(
    json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
print(record)
