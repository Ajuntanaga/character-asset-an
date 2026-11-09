# Character Asset_An: current handoff

Updated 2026-11-09 UTC. The character is unfinished. Continue the existing reference-led build; script success is not visual acceptance. Prior trials, rejections and provenance are in [PROJECT_HISTORY.md](PROJECT_HISTORY.md).

## Direction and constraints

- Match the supplied character, face, wardrobe, hands and guitar sheets; produce a film/show-quality animation-ready Blender character and show actual renders.
- Blender MCP on workspace 7, loopback 127.0.0.1:9876, per-tool approval prompt, no add-on auto-start. Preserve V357_CLOUDRIG_CONTROLS and all 1,957 drivers.
- Heavy processing goes to authorized GitHub Actions. Modal unavailable. Modest Kaggle allowed, unused. Repository PRIVATE and Actions works; no reason to toggle visibility.
- One writer, at most two read-only children; local heavy work sequential and bounded. Do not close other Codex sessions.
- Send BCA_task progress/milestone pings about every 5–10 minutes with /home/ajuntanaga/.local/bin/researchos-ntfy-publish. Reuse encrypted credential without copying it. No additional notification daemon.
- Keep this handoff concise for compaction. Remove only obsolete/reproducible files after exact restoration or redundancy verification; retain references, current scenes, checkpoint/delta bases and designated fallbacks. Manual compaction tool unavailable.

## Current build and active work

Project /home/ajuntanaga/Projects/Blender/Character Asset_An; remote https://github.com/Ajuntanaga/character-asset-an . V563 a7fde73, Actions42601041345 succeeded10:32UTC. All five actual previews in github_results/run-42601041345/previews-combined-build-40/ reviewed. Direct original-photo projection improves central skin detail, but face, eyes, hair and wardrobe remain artificial. Full scene13666615301(96.24MB) remains remote. Main1957drivers preserved.

V56242599808028 at a48e79f succeeded; six actual previews in previews-combined-build-39 reviewed. Ringlets remain narrow and sparse on the smooth cap. Straight-front guitar outline is much closer to the product photograph than the oblique view suggested; leave outline unchanged for now. Hardware/detail still needs work. Picking placement remains unchanged after measured rejection of centroid shift below.

V564 prepared: overlapping curl guides with4.5–6.2mm lobes,1.15–1.75mm bundles,8.5–14mm axial length,1–1.45turns and140–220fibers/guide;32undercoat fibers/root,0.8–1.8mm lift. Existing true strand radii retained. Add a0.45mm convex upper-lid fold that vanishes at margin,outer join and canthi; exact closed targets unchanged. Three64sample face views, two collar closeups, whole character and five blink views. Syntax/diff checks pass; runtime/visual acceptance pending dispatch.

Current jacket is part of V416_BODY_CLEAN_JOIN, material slot6; V345_TAILORED_CHARCOAL_DENIM_JACKET no longer exists. V426_Scaled_Collar slot9 is the shirt/neck transition, not the outer jacket collar. Read-only18445vertex regional export and report in local_diagnostics/collar_2026-11-09. Collar shaping still pending; use current mesh, not obsolete wardrobe advice.

## Live Blender and preserved scenes

Live GUI is production_v554_combined_reference/run-42585046848/Character_An_combined_reference_TRIAL_v554.blend; restored SHA256384976aaed800dced83dece932b6717bea29cbe51235990601d9b9bd55d6f9a3. Workspace7, two windows, textured SOLID viewport plus Image Editor displaying V561 character-preview.png. Last MCP10:41UTC dirty=false,1957drivers. Check dirty state before replacing scene. No local render or archive job active.

Preserve V468 fallback, V483, V514, native handV522, baseV528, V542 hardlink, V543, V544, V545, V547 arc, V554 current. V544 file production_v544_reference_revision/Character_An_reference_revision_TRIAL_v544.blend SHA2566299f505f4b9d31b481143e70db83c04215ff2426c7752592b35686e6fd27c02. Base github_release/current-v528.blend SHA256bc4582c0ddccc5e729371e58d3c275f43d41a11e63414a3e307c94d0e6b9e8cd. Remote restore verification already passed; do not repeat without a new restore.

## Face, eyes, hair and jacket decisions

- V560 relative key V560_ReferenceCentralFace on V416 uses retained V376 FaceBuilder donor18,024vertices/51expressions and existing V377/V381 registration. World-Y only, central nose/chin, smooth eye/lip exclusions, all1,536 lid vertices excluded. 2,329 affected vertices,8mm tanh cap, trial value.75(max5.975mm). Large registration residuals require matched clay review. Existing V377 had transferred photo color, not neutral donor shape. Rig and separate lip mesh unchanged.
- V555 generated1254px de-lit face was rejected for waxy softness/smearing. Original4K atlas preserved; keep delit_face=false. V549 photo-mask gain.65 exposes raw Tripo; read-only child identified.65 gain as~39% raw Tripo contribution; compare.90 gain without swapping the4K atlas. Do not promote solely on shader changes.
- V558 eye material copies imported shader/group; Dilation.90 contracts pupil (old comment reversed). Bypass30cm AO baked into Base Color; seven Bump distances5m→20micrometres; specular0→.5,roughness.24. Corneal roughness.035/IOR1.337, sclera(.40,.345,.30),SSS.08/scale.0007. Actual iris clearer, sclera still chalky.
- V547 blink recalculates closed targets with V369 positive-Y70micrometre margin and11-row falloff excluding Blink target; BlinkArc4b(1-b),15ray steps/200micrometre corneal clearance. V554 upper continuous black margin replaced with warm tissue; individual54upper/8lower lashes remain. V561 front and oblique half/full closure visually continuous. Broader animated expressions still need acceptance.
- V554 scalp welding/smoothing fixes outer boundary and caps movement7mm, applies identical delta to all keys; current scalp is used for roots/collisions. V556 connected posterior extension5264faces excludes ears/front islands. Do not revert to old lumpy V371 root surface.
- V557 shared guide locks initially made thick repetitive ropes. V559 reduced top lobes7–11→3–5mm, bundle radius1.8–2.8→.6–1.1mm, variable.75–1.05turns and100–300micrometre child departures. Real strand radii3–48micrometres, world scale1.0 already verified; do not repeat radius probe.
- V560 scalp part70mm long,1.2mm core/4.4mm gradient and color(.30,.145,.078) is visibly too bright. V561 narrows/darkens it; actual V561 part is darker/narrower, but curl volume/silhouette still needs improvement.
- V556 jacket grayscale ramp driven by V384_Weave_height, charcoal(.008,.009,.009)→(.018,.021,.020), instead of baked lighting. V559 roughness.84–.96/specular.10. V561 check modulates only neutral branch, preserving saturation-selected detail and floral shirt.
- V553 generated gray curly-maple albedo improves broad flame and reduces crosshatching. Source/provenance in assets/generated/gray_maple_v553. Guitar geometry/hardware still needs reference review. V551 beard extension rejected/unmerged; photo beard remains patchy.

## Hands: stopped solver and pending input

Authoritative targets references/m3/m3_chord_mapping_v2.json. Do not change strings/frets or finger assignments silently. Already-sent asynchronous question asks whether fingers may be reassigned to the SAME strings/frets. It is pending; do not repeat it. Current I:S6F11,M:S6F10hover,R:S7F9,P:S8F11,T:rear; S4F10/S5F9 unassigned. Index/ring crossing is already documented at PROJECT_HISTORY.md:375.

Donor already LEFT despite .R names; no extra reflection. Picking palm94.002mm/MCP breadth44.248mm, legacy fretting182.475/72.095mm. Picking94mm is intended; reject proposed1.63x picking enlargement. Fretting donor must preserve intended94mm palm. Measurements in local_diagnostics/hand_proportions_2026-11-09/landmarks.json. Wrist→tip chord is pose-dependent, not a scale target.

Per-digit skin BVHs use polygons all vertices>.95 distal weight, skin0, nearest own pad anchor within4mm, full subdivision measured. Correct identity now confirmed; own-pad errors I12.15/M4/R14.47/P8.16/T10.41mm. Solver remains failing. Positive flex bends palmar; no sign inversion. Stopped trials: no-thumb, wider CMC/splay, Kabsch, moving pulp patch,12seed wrist±pi. Do not repeat.27DOF pad35deg/nail60deg cones, thumb MCP20/IP15caps; do not relax anatomy for point-only success. Need actual pad/thumb contact, clearance and deformation. Diagnostics local_diagnostics/hand_fit_2026-11-08/.

Picking centroid probe10:08UTC in local_diagnostics/picking_contact_2026-11-09/centroid_probe.json:9.253mm residual entirely along exposed-tip axis; normal-.000586mm/transverse-.000244mm. Existing13mm point matches seat within.000122mm. No justification for centroid shift; retain placement. Gap1.005mm/thickness.840mm, normals-.9823. V543 front/side Workbench views examined; physical pad/clearance acceptance remains unresolved. Live MCP1957+12drivers,dirtyfalse.

## Cleanup and notifications

Cumulative16,638,733,260bytes (16.64GB/15.50GiB) reclaimed.47 obsolete full scenes are exact-restorable Zstandard deltas against retained V528; decoded SHA256 matched before removal. Latest five V455/452/450/449/448 reclaimed1,675,272,697bytes, manifest local_archive_cleanup_2026-11-09_pre456.json. Earlier manifests local_archive_cleanup_2026-11-08.json and local_archive_cleanup_2026-11-09_{older,pre500,pre478,pre468}.json. Per-folder .blend.archived.json has exact restore commands/checksums. Keep base/checkpoints.

Also19 byte-verified redundant installer fragments and4 rejected superseded deltas removed, retaining complete installer, previews/reports and current scenes. Records local_installer_fragment_cleanup_2026-11-09.json and local_rejected_delta_cleanup_2026-11-09.json. Installer underscore/hyphen aliases are hardlinks, not duplicated storage. Do not delete unique .blend1 backups or unrelated projects.

47successful BCA_task notifications, latest~10:40UTC HTTP200. Latest resources:86GiB disk free,19GiB memory available,swap2/8GiB. Viewers chafa/image available. No notification daemon or local heavy process.

## Immediate next steps

1. Dispatch/review V564 curl and upper-lid correction, including all five blink views. Retain V563 direct central-photo projection provisionally; no final face acceptance.
2. Inspect new collar closeups and current V416 mesh export to shape actual upper jacket. Do not use removed V345 object.
3. Restore a newer full scene only when improvement warrants it. Keep pending hand-finger question open; do not repeat failed solver branches.

## Commands

MCP: /home/ajuntanaga/Documents/Codex/Blender-MCP/.venv/bin/python pipeline/blender_mcp_call.py execute_blender_code @script:/tmp/script.py (or @code:/tmp/script.py; this also expects a file path). Inspect returned status, not just exit0. Inventory /run/user/1000/researchos-workstation/window-inventory.json; do not open another GUI just because wmctrl misses Wayland.

GitHub: gh run view RUN --repo Ajuntanaga/character-asset-an --json status,conclusion,jobs ; gh run download RUN --repo Ajuntanaga/character-asset-an --name NAME --dir github_results/run-RUN/NAME . Transfers may take minutes, poll same process. Dispatch gh workflow run blender-preview.yml --repo Ajuntanaga/character-asset-an --ref main -f mode=combined-build -f delit_face=false -f facial_hair=false .

Workflow pinned Blender5.2.2, Ubuntu24.04,CPU2threads,concurrency1,20minlimit,artifacts7days. Restores V528→V543→V544 with SHA checks, saves full scene before simplified previews, produces checked delta. Manifest github_assets/scene-manifest.json. Combined filename remains Character_An_combined_reference_TRIAL_v554.blend across revisions; identify by run/report, not filename alone.
