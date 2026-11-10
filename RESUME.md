# Character Asset_An: current handoff

Updated 2026-11-10 00:43 UTC. Character remains unfinished; preserve reference-led build and actual visual acceptance. Earlier complete handoffs are in PROJECT_HISTORY.md.

## Current state and next actions

V584 commit ea3ff3e / Actions 42635554578 succeeded. All 12 appearance images reviewed: curl lift and rear collar accepted as intermediate improvements only; curls remain molded/shiny and collar/neck atlas unfinished. V583 run42634096386 fixes stale Basis initialization, preserving clean half/full blink, but eyes and likeness remain unfinished. Reviews saved under github_results/run-RUN/previews-combined-build-48 or -47/visual-review.json.

V585 hand material update was committed and dispatched with review_scope=hands (three views: grip, dorsal and full character). Four local before/after images were viewed in local_diagnostics/hand_v585_surface_2026-11-09; skin/nail texture improves, pose and geometry unchanged, crowded pinch remains unaccepted. New CC-BY-3.0 Antonia maps are 2,861,936 bytes with hashes and attribution in github_assets/antonia-hand/SOURCE.json. Syntax, YAML, texture hash and diff checks pass. V585 commit88a18bf pushed; Actions42728493754 started00:27:59UTCNov10, hands scope, SUCCEEDED. All three previews reviewed: ACCEPT_MATERIAL_IMPROVEMENT_ONLY_CHARACTER_UNFINISHED. Full artifact downloaded and restored against V544 with SHA256 59788ffafd282f76f571fef7a57ba64070fea4451139a414ff3afbcfaf433471. Loaded existing GUI on workspace7,247 objects,1957drivers,clean scene. Local production_v585_combined_reference/run-42728493754/Character_An_combined_reference_TRIAL_v554.blend (519197716 bytes). Review under github_results/run-42728493754/previews-combined-build-49/visual-review.json.

Read-only hand review returned: next isolated trial may contract ONLY V421_REGULAR_SLEEVE_CUFF.R middle loft ring vertices[424:520] local XY around its centroid by 0.90, with reversible entire-Basis-initialized shape key. Keep other rings, wrist opening, jacket boundary, hand, pick and poses unchanged. Intended to reduce cuff bell; validate silhouette and wrist clearance. Implemented and REJECTED after four Workbench renders: little wrist silhouette improvement, sharper pinch higher up sleeve/seam. All scene changes restored, 1957 drivers. runtime-check.json and visual-review.json plus rejected script in local_diagnostics/cuff_v586_2026-11-10. Do not integrate or repeat this middle-ring-only trim. No general jaw X widening: reference/current normalized widths do not support it.

Cuff diagnosis: posed ring7 perimeter220.35mm vs rest148.87mm; DEF-Hand.R deformation scale[1.00003,1.04032,1.38662] despite pose scale1, while forearm is unit. Disabling preserve-volume only reduces opening to211.18mm, so not a fix. V587 reversible trial contracts lower rings by20percent with smooth upper transition and coordinated stitches/button: closer wrist fit but exposes protruding donor forearm (confirmed by color identity render); HOLD_NOT_PROMOTED. Four actual Workbench views, all scene changes restored,1957drivers. Evidence/scripts in local_diagnostics/cuff_v586_2026-11-10 and cuff_v587_2026-11-10. V588 masking55 proximal donor vertices reduces protrusion but leaves a flap: HOLD_NOT_PROMOTED. Its study and review are archived under local_diagnostics/cuff_v588_2026-11-10. All trials restored; do not change rig/hand scale.

## Constraints

Preserve V357_CLOUDRIG_CONTROLS and 1957 drivers. MCP workspace7, loopback9876, prompt approval, no addon autostart. GitHub commit/push/uploads/Actions authorized, repo PRIVATE and working; Modal unavailable. One writer, at most two read-only children, all finished. Serialize local heavy jobs and preserve Codex processes. BCA_task notifications every5–10minutes/milestones via existing encrypted publisher. No manual compaction tool: keep this handoff concise. Delete only obsolete/reproducible data after restoration/redundancy checks; preserve unique backups and references.

## Live Blender and preservation

Live GUI is V585 at the path above, workspace 7, PID 1228082, two windows. MCP remains loopback 9876. Studies restored their changes and all 1957 drivers. Existing researchos-blender-mcp.service now points to V585; backup ~/.config/systemd/user/researchos-blender-mcp.service.before-v585-20261110. Daemon reloaded without restarting Blender. No reboot test. Do not start another instance.
Retain V468 fallback, V483, V514, native hand V522, base V528, V542 hardlink, V543, V544, V545, V547, V554, V575 and V585.
V528 base github_release/current-v528.blend SHA256 bc4582c0ddccc5e729371e58d3c275f43d41a11e63414a3e307c94d0e6b9e8cd.
V544 production_v544_reference_revision/Character_An_reference_revision_TRIAL_v544.blend SHA256 6299f505f4b9d31b481143e70db83c04215ff2426c7752592b35686e6fd27c02.

## Retained decisions and rejected trials

- V571 fills 12,418 zero-weight portrait UVs; UV(0,0) interpolation caused the pale eye annulus. Actual emission/lit renders confirm improvement. V569 continuous eye albedo remains.
- V547 closed targets follow V369 margins through 11 rows; driven BlinkArc=4b(1-b), 15 samples, 200 micrometre corneal margin. Stored endpoint equality does not prove evaluated lid clearance. V369 wet-margin tubes hidden after alignment; lashes remain.
- V573 transfers normals to 595 seam vertices after Subsurf, without geometry/key changes. V574 direct lip photo and V575 shared surround affect 960 lip/2,177 body vertices. Actual neutral/pucker/jaw views improve continuity. Dental anatomy is correctly placed; an isolation filter had accidentally hidden V363_DENTAL objects. No dental reposition needed.
- V570 lip-volume ledge, V572 UV-only mouth fix, V573 surface movement, V551 beard extension and V580 moustache-weight exclusion were rejected from actual renders. V580 made an angular albedo boundary and did not remove the gray patch. Do not repeat them.
- V581 domed/flatter guitar control caps were rejected: softened shoulders and scalloped outline. Existing V401 caps retained. Straight-front guitar outline is closer to the product reference than the oblique view suggested; don't reshape from perspective alone.
- V554 welded/fair scalp and V556 posterior extension retained. Hair radii/world scale already verified; do not repeat. Current problem is the groom's coherent molded curl shape and bright part, not missing subdivision.
- V560 face donor shape is reversible; V566 pucker intentionally excludes lids, but its old key initialization was defective; V583 explicitly initializes Basis before applying the transfer. Full expression quality is not accepted.
- V565 collar narrowing/flattening and V567 2,436-face rear cloth mask plus V578 18-face rim mask remain trials. Collar still inflated/pale in places. Original V379 samples are exported; avoid repeated 8192px image.pixels slices, which previously hung Blender.
- Original 4K photo atlas retained; generated de-lit V555 face rejected as waxy. V553 maple albedo retained with provenance. Face, facial hair, garment and instrument detail all still need work.

## Hands

Authoritative references/m3/m3_chord_mapping_v2.json. Pending asynchronous question asks whether finger assignment may change while preserving the SAME strings/frets; unanswered, do not repeat or change mapping silently. Current I:S6F11, M:S6F10 hover, R:S7F9, P:S8F11, T:rear; S4F10/S5F9 unassigned.
Picking palm 94.002 mm/MCP width 44.248 mm is intended; reject 1.63x enlargement. Legacy fretting hand is 182.475/72.095 mm. Donor already LEFT despite .R names; no extra reflection. Wrist-to-tip chord depends on pose, not scale.
Per-digit pad identity verified. Errors I12.15/M4/R14.47/P8.16/T10.41 mm; solver fails. Stopped no-thumb, wider CMC/splay, Kabsch, moving pulp and 12-seed wrist ±pi branches. Keep 27 DOF, pad35/nail60deg cones, thumb MCP20/IP15 caps. Require actual pad/thumb contact, clearance and open/curl/grip deformation.
Picking centroid residual 9.253 mm is along exposed-tip axis; existing 13 mm seat matches within .000122 mm. No centroid shift justified. Gap1.005/thickness.840 mm, normals-.9823. Physical contact/clearance still unaccepted.

## Resources and cleanup

Previously reclaimed32,060,063,086bytes across108 obsolete scenes after decode/SHA verification. Latest manifest local_archive_cleanup_2026-11-09_pre387.json; V385 inefficient delta rejected, original kept; no archive job active. Unique backups/checkpoints retained. At00:20UTCNov10:12GiB RAM available,swap4.6/8GiB,disk99GiB free. No further deletion warranted merely to meet a cadence.

## Notifications and cloud

BCA_task publisher: CURL_HOME=/tmp/character-ntfy-curl /home/ajuntanaga/.local/bin/researchos-ntfy-publish BCA_task TITLE MESSAGE. Scoped curl resolution preserves TLS; refresh DNS using Google DoH before expired entries. No OS DNS changes or new notification daemon. Two confirmed HTTP200 pings this resumed turn, latest00:29UTCNov10. Prior88confirmed pings; old15:45Nov9attempt outcome not captured.

Kaggle V583v2 CANCEL_ACKNOWLEDGED externally14:18Nov9, no root cancellation/reason. Inputs restored and hashes verified, next Blender download; no GPU result. Do not retry now. prepare_kaggle_character adds V585 maps/license for future use only. Signed ignored mode600 payloads expired; never print/commit.

Actions workflow35minCPU2, concurrency1, artifacts7days. Restores V528→V543→V544 SHA checked, saves scene before rendering. review_scope full15/mouth5/appearance12/hands3. Combined filename remains Character_An_combined_reference_TRIAL_v554.blend; identify revision by report/run. MCP call via /home/ajuntanaga/Documents/Codex/Blender-MCP/.venv/bin/python pipeline/blender_mcp_call.py execute_blender_code @script:/tmp/script.py . Inspect structured status. Inventory /run/user/1000/researchos-workstation/window-inventory.json. Do not start second Blender.
