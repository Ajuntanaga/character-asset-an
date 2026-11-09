# Character Asset_An: current handoff

Updated 2026-11-09 14:13 UTC. The character remains unfinished. Continue the existing reference-led build. Successful scripts are not visual acceptance. Earlier details and rejected trials are preserved in PROJECT_HISTORY.md, including the complete handoff archived at 13:41 UTC.

## Constraints

- Match the supplied character, face, wardrobe, hands and guitar sheets; produce a film/show-quality animation-ready character and show actual renders.
- Preserve V357_CLOUDRIG_CONTROLS and its 1,957 drivers. Blender MCP belongs on workspace 7, loopback 127.0.0.1:9876, per-tool approval prompt, no add-on auto-start.
- GitHub uploads, commits/push and Actions are authorized. Repo https://github.com/Ajuntanaga/character-asset-an remains PRIVATE; Actions works. Modal unavailable. Modest Kaggle allowed.
- One writer, at most two read-only children. v584_part_geometry finished: part material footprint can narrow from 2.3 to 1.4 mm. v584_collar_remaining derives rear-roll geometry bounds from existing exports; no further arbitrary rim mask. Root remains sole writer. The finished expression-key audit found no additional active post-rebuild creation sites beyond the four fixed. Serialize bounded local heavy jobs; do not close other Codex sessions.
- BCA_task notifications about every 5–10 minutes and at milestones, using the existing encrypted credential publisher. No notification daemon. No manual compaction tool; keep this handoff compact.
- Remove only obsolete/reproducible files after exact restoration or redundancy checks. Keep references, unique backups, current scenes and designated bases/checkpoints.

## Current cloud work

V582 commit 4b7102a is pushed. Actions run 42627527644 started around 13:40 UTC, appearance scope (12 actual views), delit_face=false and facial_hair=false. Main changes:
- Restore upper eye opening 11.5 to 8.8 mm. V578 wider opening caused a pale overlapping flap at full closure, despite intermediate stored-target assertions.
- V557 groom now gives each macro curl five related trajectories: amplitude .85–1.15, turn .88–1.12, root-zero phase warp ±.35 radians. Existing density, radii, root distribution, undercoat, macro amplitude and shader unchanged. Separate RNG preserves old random sequence. Root points retained. Actual render review pending.
Compilation and diff checks passed before commit. Run SUCCEEDED by 14:00 UTC. All 12 previews downloaded and viewed in github_results/run-42627527644/previews-combined-build-46; visual-review.json records findings. Hair variation improved but molded clumps, dark cap and bright tan part remain. Eye rollback removes the pale flap but open/half-blink defects remain; V583 local correction supersedes these pending full build. Front/rear collar still thick. Full artifact 13679589159, 134902549 bytes, remains remote; no overall quality acceptance.

V578 run 42622660668 succeeded 13:18:52 UTC. All 12 images reviewed in github_results/run-42622660668/previews-combined-build-45. Eyes remain narrow/triangular, half-blink shiny caps, full-blink pale flap regression. Hair remains molded shiny C loops and a bright straight part. Collar still inflated with pale rear rim. Full artifact 13678121039 (134,838,062 bytes) stays remote.

V575 run 42619527185 is fully downloaded and restored. Valid scene: production_v575_combined_reference/run-42619527185/Character_An_combined_reference_TRIAL_v554.blend, 514141241 bytes, SHA256 369e8a79c7e19c95479b5a783d674f7f08379aa450691aa931ff4e7524f4769f. Restoration manifest beside it. Bad 135002024-byte ranged-transfer scratch removed after successful restore; local_diagnostics/v575-failed-transfer-cleanup.json records it. No active download.

## V583 eye correction: implemented, Kaggle build submitted

Actual cause found through live MCP: newly added partial shape keys inherit stale mesh coordinates after direct Basis edits. V560_ReferenceCentralFace (.75) and V565_ReferenceJacketCollar (1) lower upper lids by 3.1499/3.1195 mm combined; MouthPucker has the same unintended lid offsets at zero value. BlinkArc.R also inherited a left-eye delta. Disabling the Armature makes no difference, so this is not a rig-transform problem. Details: local_diagnostics/eye-deformation-v575.json and neutral-eye-aperture-v575.json.

Source fixes explicitly copy the entire Basis before partial edits in V560, V565, V566 and V547. Combined revision bumped V583. Compilation and diff checks pass. Committed/pushed 3e5fe66 with Kaggle input correction. Live lid-only trial corrected these three keys and the opposite-eye Arc deltas, then rendered six open/half/full front/oblique images in local_diagnostics/lid_v583_clean_keys_2026-11-09. All six viewed: open aperture enlarged; half-blink cap and full-blink flap removed. Actual target eye shape still needs refinement. The trial restored all key data, pose, visibility, camera/render settings and 1957 drivers, with no scene overwrite.

Earlier cornea visibility study confirmed the shiny cap came from cornea penetration. Arc clearance 200 to 550 micrometres did not fix it and was REJECTED from actual renders. Both studies restored scene; directories lid_v576_cornea_2026-11-09 and lid_v579_arc_2026-11-09 under local_diagnostics. No local render active now.

## Next actions

1. V582 review is complete. Continue from its recorded findings; no active download.
2. V583 Kaggle v1 failed after 49.24 seconds, before rendering, on the zstd window cap. Expanded reference input restoration and V528 download verification succeeded. Pinned zstandard 0.25.0 C backend uses bytes, so old 1 MiB cap rejected the 357953331-byte V543 frame. Changed bounded cap to 1 GiB; actual local old-cap failure reproduced and new-cap decode SHA matched the manifest in 0.9 seconds. Report local_diagnostics/kaggle-zstd-window-validation.json. Preparing one corrected v2 retry; do not also dispatch Actions V583.
3. Update/load a verified cloud scene into workspace 7 after visual review and checksum restoration. Continue reference face/hair/wardrobe and hand/animation work. No overall completion claim.
4. V583 source/Kaggle loader fix committed and pushed 3e5fe66. Continue with actual cloud results and maintain frequent notifications and recoverable cleanup.

## Live Blender and preservation

Live GUI is V575 at the path above, workspace 7, PID 1228082, two windows. MCP remains loopback 9876. Studies restored their changes and all 1957 drivers. Existing researchos-blender-mcp.service now points to V575; backup ~/.config/systemd/user/researchos-blender-mcp.service.before-v575-20261109. Daemon reloaded without restarting Blender. No reboot test. Do not start another instance.
Retain V468 fallback, V483, V514, native hand V522, base V528, V542 hardlink, V543, V544, V545, V547, V554 and V575.
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

## Cleanup, resources, notifications

32,060,063,086 bytes (32.06 GB / 29.86 GiB) reclaimed across 108 obsolete full scenes. Each was encoded against retained V528, decoded and SHA256 verified before original removal. Latest V386 reclaimed 200896951 bytes, manifest local_archive_cleanup_2026-11-09_pre387.json. The next V385 archive exceeded the half-size cutoff, so its original was kept and only the newly created inefficient trial delta removed; V383/V381 skipped. Record local_diagnostics/archive-pre387-stop.json. No archive job active. Each .blend.archived.json has exact restore instructions. Also 19 byte-verified redundant installer fragments and four rejected deltas removed; unique .blend1 backups and references retained.
At 13:55 UTC: 15 GiB memory available, swap 3.3/8 GiB, about 96 GiB disk free. No local heavy job active. Native image viewer chafa available.
80 successful BCA_task notifications through 14:09 UTC, seven DNS failures. Scoped CURL_HOME=/tmp/character-ntfy-curl resolves ntfy.sh from TLS Google DoH; latest lookup 14:11 UTC TTL385 seconds, refresh after 14:17 UTC. Saved encrypted credential loading and normal TLS retained; no OS DNS changes.

## Kaggle

anthovargas/character-an-v567-gpu-preview v1 FAILED before rendering, in 2.03 seconds: /kaggle/input/**/reference-inputs.zip absent. Kaggle documentation confirms archive inputs are expanded; the loader assumed a ZIP. Log/report in kaggle_results/v567. Two T4 GPUs available, but no rendering occurred. Dataset anthovargas/character-an-v544-render-inputs private. V583 version 1 submitted at 14:00 UTC and FAILED before rendering after 49.24 seconds: https://www.kaggle.com/code/anthovargas/character-an-v583-gpu-preview . Dataset update READY before submission. Expanded inputs restored correctly. The decoder cap fix passed the actual local patch test; one v2 retry is being prepared with fresh signed URLs. One selected T4 GPU, CPU2, 1800-second cap; do not duplicate. Temporary asset URLs generated about 13:57 UTC, expire about 14:57 UTC.
Source fix adds kaggle_reference_inputs.py, a pinned per-file manifest embedded in the input ZIP, supports either ZIP or expanded mounts, and validates file sizes/hashes before restoring. prepare_kaggle_character.py adds missing v578-collar-rim-mask.json and bundles the helper. Local fixture reproduces old missing-ZIP failure, restores identical bytes through ZIP/expanded paths, rejects corrupt expanded inputs; syntax checks pass. Generated bundle includes all four Basis initialization fixes, revision V583, 30 scripts and seven reference inputs; 3.32 MB uploaded. No claim of GPU success yet.
Refresh temporary signed scene URLs immediately before any authorized upload/run. Generated kaggle_payload scripts contain signed URLs; ignored, mode600, do not print/commit. Modest single-GPU/30min cap remains.

## Commands

MCP: /home/ajuntanaga/Documents/Codex/Blender-MCP/.venv/bin/python pipeline/blender_mcp_call.py execute_blender_code @script:/tmp/script.py . Inspect structured status, not exit0 alone. Window inventory /run/user/1000/researchos-workstation/window-inventory.json.
GitHub: gh run view RUN --repo Ajuntanaga/character-asset-an --json status,conclusion,jobs . Download named previews before full artifacts. Current run42627527644. Do not duplicate active transfers.
Workflow Blender5.2.2/Ubuntu24.04, CPU2, concurrency1,35minlimit, artifacts7days. Restores V528→V543→V544 with SHA checks; saves full scene before previews. Review scopes full15/mouth5/appearance12. Combined filename stays V554 across revisions; identify by run/report, not filename.
