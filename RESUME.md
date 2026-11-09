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

Project /home/ajuntanaga/Projects/Blender/Character Asset_An; remote https://github.com/Ajuntanaga/character-asset-an . V561 source61a73b1dc733dcdff23feeb5facbcfd2299c85ba, Actions42597328082 succeeded10:05:20UTC. All12 previews downloaded under github_results/run-42597328082/previews-combined-build-38/ and reviewed. Main1957drivers,209objects,no missing images. Full artifact13663479186(66.14MB) remains remote.

V561: .90 photo-mask gain does not remove white cheek/temple etching; retain.65. Reduced35% chin field removes V560's worst profile ledge; keep provisionally. Upper lid6.9mm closes continuously at front0/.5/1 and oblique.5/1; open shape still artificial/chalky. Narrow darker part improves contrast but is still straight; flat waves lack reference curl volume. Jacket check is too faint, collar reads rubbery, pocket detail visibly stretched; whole character still has unequal hands. Actual renders are diagnostic, not final acceptance.

V562 prepared: shared rising ringlet guides,35–55deg axis tilt,11–18mm axial length,1.25–1.75turns,3.2–4.8mm lobes,9.5mm top spacing; retain fine fibers/undercoat and scalp clearance. Next shots whole character,front/profile/oblique hair,guitar-front,pick-grip. Blink suite not repeated for hair-only changes. Root sole writer. Read-only guitar_next_correction child still comparing the guitar. Picking child completed; proposed centroid shift rejected by actual live measurement below.

V56042595153834 full chin field rejected; nine renders retained in previews-combined-build-37. V55942594193337 seven renders retained in previews-combined-build-36. Neither full scene downloaded.

## Live Blender and preserved scenes

Live GUI is production_v554_combined_reference/run-42585046848/Character_An_combined_reference_TRIAL_v554.blend; restored SHA256384976aaed800dced83dece932b6717bea29cbe51235990601d9b9bd55d6f9a3. Workspace7, two windows, textured SOLID viewport plus Image Editor displaying V561 character-preview.png. Last MCP10:13UTC dirty=false,1957drivers. Check dirty state before replacing scene. No local render or archive job active.

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

Cumulative14,963,460,563bytes (14.96GB/13.94GiB) reclaimed.42 obsolete full scenes are exact-restorable Zstandard deltas against retained V528; decoded SHA256 matched before removal. Latest five V466/460/459/458/456 reclaimed1,708,479,786bytes, manifest local_archive_cleanup_2026-11-09_pre468.json. Previous five V477/476/475/473/471 are in local_archive_cleanup_2026-11-09_pre478.json. Per-folder .blend.archived.json has exact restore command/checksums. Earlier manifests local_archive_cleanup_2026-11-08.json, local_archive_cleanup_2026-11-09_older.json, local_archive_cleanup_2026-11-09_pre500.json. Keep base/checkpoints.

Also19 byte-verified redundant installer fragments and4 rejected superseded deltas removed, retaining complete installer, previews/reports and current scenes. Records local_installer_fragment_cleanup_2026-11-09.json and local_rejected_delta_cleanup_2026-11-09.json. Installer underscore/hyphen aliases are hardlinks, not duplicated storage. Do not delete unique .blend1 backups or unrelated projects.

43successful BCA_task notifications, latest~10:12UTC HTTP200. Latest resources:83GiB disk free,19GiB memory available,swap2/8GiB. Viewers chafa/image available. No notification daemon or local heavy process.

## Immediate next steps

1. Dispatch V562 after syntax/diff check and inspect six actual previews. Integrate one concrete guitar geometry correction if the read-only finding supports it.
2. Retain.65 face blend. Cheek etching persists and needs a targeted texture correction; do not retry the same gain comparison. Live V554 shader probe confirms only procedural Bump connects to Normal, not an imported normal map; V557 reduces its amplitude in newer builds.
3. Restore a newer full scene only when improvement warrants it. Keep pending hand-finger question open; do not repeat failed solver branches.

## Commands

MCP: /home/ajuntanaga/Documents/Codex/Blender-MCP/.venv/bin/python pipeline/blender_mcp_call.py execute_blender_code @script:/tmp/script.py (or @code:/tmp/script.py; this also expects a file path). Inspect returned status, not just exit0. Inventory /run/user/1000/researchos-workstation/window-inventory.json; do not open another GUI just because wmctrl misses Wayland.

GitHub: gh run view RUN --repo Ajuntanaga/character-asset-an --json status,conclusion,jobs ; gh run download RUN --repo Ajuntanaga/character-asset-an --name NAME --dir github_results/run-RUN/NAME . Transfers may take minutes, poll same process. Dispatch gh workflow run blender-preview.yml --repo Ajuntanaga/character-asset-an --ref main -f mode=combined-build -f delit_face=false -f facial_hair=false .

Workflow pinned Blender5.2.2, Ubuntu24.04,CPU2threads,concurrency1,20minlimit,artifacts7days. Restores V528→V543→V544 with SHA checks, saves full scene before simplified previews, produces checked delta. Manifest github_assets/scene-manifest.json. Combined filename remains Character_An_combined_reference_TRIAL_v554.blend across revisions; identify by run/report, not filename alone.
