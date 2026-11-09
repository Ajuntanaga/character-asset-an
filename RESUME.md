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

Project /home/ajuntanaga/Projects/Blender/Character Asset_An; remote https://github.com/Ajuntanaga/character-asset-an . Pushed source 552927dfdeb4fac9f1bfd5508d6a85cc232dbe7f. V560 run42595153834 SUCCEEDED; all nine previews reviewed. Full chin displacement is excessive in profile, so V561 retains only35% of its chin field and keeps nose correction. V561 source now ready to dispatch; see git HEAD for exact pushed revision.

V559 run42594193337 @b615a84 succeeded09:40UTC; all seven previews reviewed under github_results/run-42594193337/previews-combined-build-36/. Compact curls are less rope-like, but gray clumps, bright part, zigzag hairline and blunt nape remain. Face has narrow flat upper lids, chalky sclera and patchy/waxy photo shading. Frontal blink0/.5/1 closes continuously; no oblique acceptance. Jacket remains gray/leather-like despite roughness.84–.96/specular.10. Whole character still has unequal hands. 209objects,1957drivers,zero missing images. Full scene not downloaded.

V560 run42595153834 @552927d: previews-combined-build-37 and blender-combined-build-37. Nine views include matched before/after front/profile neutral clay, textured front/profile and three blink states. Actual textured and clay comparison: nose correction modest; chin creates a forward ledge. Full field rejected; V561 chin contribution reduced to35%. Full delta not downloaded. Do not duplicate an active artifact transfer.

V561 uncommitted files: pipeline/build_v544_reference_eyelids.py raises reopened upper lid6.2→6.9mm, retains lower2.3mm and closed targets; pipeline/refine_v561_jacket_check.py adds a restrained8–12% cool-gray 26/30mm check in V372_RestPosition X/Z, 1mm core/1.6mm feathered width; combined builder integrates it. Live MCP verified garment rest coordinates are world-scale metres. Pipeline shots now whole character, face front, wardrobe front/detail plus blink0/.5/1. V561 also narrows the scalp part to55mm long/0.5mm core/2.3mm total and darkens linear scalp color(.115,.054,.026). Matched face front/profile compare photo gain.65 against.90, with identical geometry. Saved full scene stays.65 pending review. Five blink views include oblique half/full closure. Root sole writer; all children finished. Runtime/render pending.

## Live Blender and preserved scenes

Live GUI is production_v554_combined_reference/run-42585046848/Character_An_combined_reference_TRIAL_v554.blend; restored SHA256384976aaed800dced83dece932b6717bea29cbe51235990601d9b9bd55d6f9a3. Workspace7, two windows, textured SOLID viewport plus Image Editor displaying V559 character-preview.png. Last MCP09:47UTC dirty=false,1957drivers. Check dirty state before replacing scene. No local render or archive job active.

Preserve V468 fallback, V483, V514, native handV522, baseV528, V542 hardlink, V543, V544, V545, V547 arc, V554 current. V544 file production_v544_reference_revision/Character_An_reference_revision_TRIAL_v544.blend SHA2566299f505f4b9d31b481143e70db83c04215ff2426c7752592b35686e6fd27c02. Base github_release/current-v528.blend SHA256bc4582c0ddccc5e729371e58d3c275f43d41a11e63414a3e307c94d0e6b9e8cd. Remote restore verification already passed; do not repeat without a new restore.

## Face, eyes, hair and jacket decisions

- V560 relative key V560_ReferenceCentralFace on V416 uses retained V376 FaceBuilder donor18,024vertices/51expressions and existing V377/V381 registration. World-Y only, central nose/chin, smooth eye/lip exclusions, all1,536 lid vertices excluded. 2,329 affected vertices,8mm tanh cap, trial value.75(max5.975mm). Large registration residuals require matched clay review. Existing V377 had transferred photo color, not neutral donor shape. Rig and separate lip mesh unchanged.
- V555 generated1254px de-lit face was rejected for waxy softness/smearing. Original4K atlas preserved; keep delit_face=false. V549 photo-mask gain.65 exposes raw Tripo; read-only child identified.65 gain as~39% raw Tripo contribution; compare.90 gain without swapping the4K atlas. Do not promote solely on shader changes.
- V558 eye material copies imported shader/group; Dilation.90 contracts pupil (old comment reversed). Bypass30cm AO baked into Base Color; seven Bump distances5m→20micrometres; specular0→.5,roughness.24. Corneal roughness.035/IOR1.337, sclera(.40,.345,.30),SSS.08/scale.0007. Actual iris clearer, sclera still chalky.
- V547 blink recalculates closed targets with V369 positive-Y70micrometre margin and11-row falloff excluding Blink target; BlinkArc4b(1-b),15ray steps/200micrometre corneal clearance. V554 upper continuous black margin replaced with warm tissue; individual54upper/8lower lashes remain. Frontal closure verified, oblique/full-surface still needed.
- V554 scalp welding/smoothing fixes outer boundary and caps movement7mm, applies identical delta to all keys; current scalp is used for roots/collisions. V556 connected posterior extension5264faces excludes ears/front islands. Do not revert to old lumpy V371 root surface.
- V557 shared guide locks initially made thick repetitive ropes. V559 reduced top lobes7–11→3–5mm, bundle radius1.8–2.8→.6–1.1mm, variable.75–1.05turns and100–300micrometre child departures. Real strand radii3–48micrometres, world scale1.0 already verified; do not repeat radius probe.
- V560 scalp part70mm long,1.2mm core/4.4mm gradient and color(.30,.145,.078) is visibly too bright. V561 narrows/darkens it; actual render pending. Curl volume/silhouette still needs improvement.
- V556 jacket grayscale ramp driven by V384_Weave_height, charcoal(.008,.009,.009)→(.018,.021,.020), instead of baked lighting. V559 roughness.84–.96/specular.10. V561 check modulates only neutral branch, preserving saturation-selected detail and floral shirt.
- V553 generated gray curly-maple albedo improves broad flame and reduces crosshatching. Source/provenance in assets/generated/gray_maple_v553. Guitar geometry/hardware still needs reference review. V551 beard extension rejected/unmerged; photo beard remains patchy.

## Hands: stopped solver and pending input

Authoritative targets references/m3/m3_chord_mapping_v2.json. Do not change strings/frets or finger assignments silently. Already-sent asynchronous question asks whether fingers may be reassigned to the SAME strings/frets. It is pending; do not repeat it. Current I:S6F11,M:S6F10hover,R:S7F9,P:S8F11,T:rear; S4F10/S5F9 unassigned. Index/ring crossing is already documented at PROJECT_HISTORY.md:375.

Donor already LEFT despite .R names; no extra reflection. Picking palm94.002mm/MCP breadth44.248mm, legacy fretting182.475/72.095mm. Picking94mm is intended; reject proposed1.63x picking enlargement. Fretting donor must preserve intended94mm palm. Measurements in local_diagnostics/hand_proportions_2026-11-09/landmarks.json. Wrist→tip chord is pose-dependent, not a scale target.

Per-digit skin BVHs use polygons all vertices>.95 distal weight, skin0, nearest own pad anchor within4mm, full subdivision measured. Correct identity now confirmed; own-pad errors I12.15/M4/R14.47/P8.16/T10.41mm. Solver remains failing. Positive flex bends palmar; no sign inversion. Stopped trials: no-thumb, wider CMC/splay, Kabsch, moving pulp patch,12seed wrist±pi. Do not repeat.27DOF pad35deg/nail60deg cones, thumb MCP20/IP15caps; do not relax anatomy for point-only success. Need actual pad/thumb contact, clearance and deformation. Diagnostics local_diagnostics/hand_fit_2026-11-08/.

## Cleanup and notifications

Cumulative13,254,980,777bytes (13.25GB/12.34GiB) reclaimed.37 obsolete full scenes are exact-restorable Zstandard deltas against retained V528; decoded SHA256 matched before removal. Latest five V477/476/475/473/471 reclaimed1,755,339,728bytes, manifest local_archive_cleanup_2026-11-09_pre478.json. Per-folder .blend.archived.json has exact restore command/checksums. Earlier manifests local_archive_cleanup_2026-11-08.json, local_archive_cleanup_2026-11-09_older.json, local_archive_cleanup_2026-11-09_pre500.json. Keep base/checkpoints.

Also19 byte-verified redundant installer fragments and4 rejected superseded deltas removed, retaining complete installer, previews/reports and current scenes. Records local_installer_fragment_cleanup_2026-11-09.json and local_rejected_delta_cleanup_2026-11-09.json. Installer underscore/hyphen aliases are hardlinks, not duplicated storage. Do not delete unique .blend1 backups or unrelated projects.

40successful BCA_task notifications, latest~09:56UTC HTTP200. Latest resources:83GiB disk free,19GiB memory available,swap2/8GiB. Viewers chafa/image available. No notification daemon or local heavy process.

## Immediate next steps

1. Dispatch V561 combined-build, inspect all actual face A/B, wardrobe, whole-character and frontal/oblique blink previews.
2. Keep/discard the.90 photo-mask gain based on matched front/profile. Retain reduced chin only if profile/front improve. Continue hair curl volume and silhouette, then guitar/body work.
3. Restore a newer full scene only when improvement warrants it; show images in existing Blender window. Keep pending hand-finger question open; do not repeat failed solver branches.

## Commands

MCP: /home/ajuntanaga/Documents/Codex/Blender-MCP/.venv/bin/python pipeline/blender_mcp_call.py execute_blender_code @script:/tmp/script.py (or @code:). Inspect returned status, not just exit0. Inventory /run/user/1000/researchos-workstation/window-inventory.json; do not open another GUI just because wmctrl misses Wayland.

GitHub: gh run view RUN --repo Ajuntanaga/character-asset-an --json status,conclusion,jobs ; gh run download RUN --repo Ajuntanaga/character-asset-an --name NAME --dir github_results/run-RUN/NAME . Transfers may take minutes, poll same process. Dispatch gh workflow run blender-preview.yml --repo Ajuntanaga/character-asset-an --ref main -f mode=combined-build -f delit_face=false -f facial_hair=false .

Workflow pinned Blender5.2.2, Ubuntu24.04,CPU2threads,concurrency1,20minlimit,artifacts7days. Restores V528→V543→V544 with SHA checks, saves full scene before simplified previews, produces checked delta. Manifest github_assets/scene-manifest.json. Combined filename remains Character_An_combined_reference_TRIAL_v554.blend across revisions; identify by run/report, not filename alone.
