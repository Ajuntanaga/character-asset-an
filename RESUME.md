# Character Asset_An: current handoff

Updated 2026-11-08. The character is unfinished. Continue the active reference-led Blender build; do not restart it or treat successful scripts as visual acceptance. Detailed prior decisions, rejected trials and checkpoint provenance are preserved in [PROJECT_HISTORY.md](PROJECT_HISTORY.md).

## User direction and working constraints

- Build a film/show-quality, animation-ready character matching supplied face, hair, wardrobe, hand and guitar sheets. Show actual rendered images.
- Use the live Blender MCP on workspace 7. Loopback `127.0.0.1:9876`, per-tool approval `prompt`, no add-on auto-start. Preserve the main `V357_CLOUDRIG_CONTROLS` rig and all 1,957 drivers.
- Offload heavy builds/renders to the authorized GitHub repository and Actions. Modal is unavailable. Modest Kaggle use is permitted but has not been used. Current repository is PRIVATE; Actions works. Public fallback is authorized only if needed; do not change visibility without a reason.
- One writer; at most two independent read-only children. Keep local heavy work sequential and bounded. Do not close other Codex sessions.
- Send meaningful updates and long-wait pings to `BCA_task` with `/home/ajuntanaga/.local/bin/researchos-ntfy-publish TOPIC TITLE MESSAGE`. Reuse the encrypted credential; never print or copy it. Do not create another notification daemon.
- Keep this handoff concise for automatic context compaction. Remove reproducible caches and obsolete full-size scene copies only after preserving necessary rollback data and verifying exact restoration. Keep references, current scenes, designated checkpoints and delta bases.

## Current files and branches

Project: `/home/ajuntanaga/Projects/Blender/Character Asset_An`.
Remote: https://github.com/Ajuntanaga/character-asset-an . HEAD `c25566b` was pushed before the current hand/groom iteration.

- Preserved main character: V514. Native hand foundation: V522. V528 remains a retained delta base.
- Working reference branch V544: `production_v544_reference_revision/Character_An_reference_revision_TRIAL_v544.blend`; SHA256 `6299f505f4b9d31b481143e70db83c04215ff2426c7752592b35686e6fd27c02`. Its release and remote restore are verified. Do not redo that verification.
- Live GUI file: `production_v545_fretting_hand/run-42568146113/Character_An_fretting_hand_TRIAL_v545.blend`, restored from the verified remote delta. SHA256 `1cf81292e89691713f1ff01c80be0a9f44892c425820882d39943a350e4a4519`. V547 arc trial and prior scenes are retained. Main rig has 1,957 drivers.
- V545 hands, V546 groom and V547 blinks are INDEPENDENT branches from V544; none is merged or production accepted.

## Jobs: resume these, do not duplicate

**Hand run 42568146113 succeeded but is visually rejected.** Results: `github_results/run-42568146113/blender-hand-build-9/`. Viewed front/oblique/rear/character. Palms both 94mm; main/native drivers 1957/48; wrist anchor error 0.000149mm; pick unchanged. Palm/wrist clearance 12.70/3.734mm. Contact errors index 2.030, middle hover 0.101, ring 1.731, pinky 2.875, thumb 1.950mm. Thumb is hooked and all four distal flexions reached zero. New unrendered trial adds thumb CMC axial roll, three analytic roll seeds, smaller MCP/IP flexion limits, rounded DIP posture priors and rear-neck containment. The donor is already LEFT despite .R bone names: V522 maps it to main .L; V528 explicitly reflects it for the right hand. Do NOT add another reflection. Rear-neck normal equals -fretboard normal here; changing that is also not a fix.

**Groom run 42568298993 succeeded but is visually rejected.** Download complete at `github_results/run-42568298993/blender-groom-build-10/`. Viewed all three images against the photoreal triptych: curls still form rows of extended springs, hairline remains serrated. New unrendered trial reduces axial advance from 18-22mm to 4-7mm while keeping the 11-14mm loop diameter and coherent directions. This targets compact ringlets; it does not fix the hairline by itself.

**Blink run 42569037176 succeeded.** Results: `github_results/run-42569037176/blender-blink-build-11/`. Viewed frontal open/half/closed closeups: lids close continuously with no apparent corneal pop-through. Full-surface, oblique and animation deformation remain unreviewed. Scene has 170 objects, 1957 main drivers, no missing images. Local full-detail scene: `production_v547_blink_alignment/arc_trial/Character_An_blink_alignment_TRIAL_v547.blend`. Arc diagnostic at 0/0.25/0.5/0.75/1 had zero penetrating boundary samples and minimum clearance 0.1999mm, compared with the earlier half-blink -0.4273/-0.4165mm. Do not repeat the completed frontal check.

No cloud jobs are active as of 2026-11-09 06:03UTC. Dispatch the pending hand/groom changes after syntax and diff checks; record run IDs here.

## Cleanup and notifications completed

2026-11-08: archived V530–V541 (12 superseded trials) as Zstandard deltas against retained `github_release/current-v528.blend`. Each decoded stream matched the original SHA256 before the full scene was removed. Recovered **4,250,005,688 bytes**. Aggregate record: `local_archive_cleanup_2026-11-08.json`; each scene folder has `<original>.blend.archived.json` with exact restore command, base/delta checksums and original checksum. These are local archive records, not a remote backup of all history. Do not delete the base. Root filesystem now approximately 77GiB available; memory approximately 20GiB available and swap 466MiB.

Three BCA_task notifications delivered HTTP200 during this pass: build progress, cleanup milestone and completed render review (latest about 21:57PST Nov8). Continue at meaningful milestones and during long waits.

## Next work

1. Render the pending hand and compact-ringlet trials on Actions. Inspect actual images and contact/clearance; do not accept on numerical distance alone.
2. Address the observed groom hairline and remaining hand deformation after the trials. Preserve the approved M3 chord targets.
3. Integrate acceptable branches reversibly and inspect the full character. Continue reference face/skin/hair, guitar shape/figured-maple finish, wardrobe, rig/deformation and animation work. None is finished.

## Commands and important details

MCP Python: `/home/ajuntanaga/Documents/Codex/Blender-MCP/.venv/bin/python pipeline/blender_mcp_call.py execute_blender_code @code:/tmp/script.py` (or `@script:`). Write code to a file; do not pass malformed inline JSON. Inspect live dirty state before replacing a scene. Never open another GUI merely because `wmctrl` misses a Wayland window. Window inventory: `/run/user/1000/researchos-workstation/window-inventory.json`.

`gh run view RUN --json status,conclusion,jobs`; `gh run download RUN --dir github_results/run-RUN`. Artifact transfers may take several minutes without output; the temporary `/tmp/gh-artifact.*.zip` grows. Poll an existing process instead of duplicating it.

Workflow `.github/workflows/blender-preview.yml`: Ubuntu24.04, pinned Blender5.2.2, CPU2threads, concurrency1, 20minute limit, artifacts7days. Modes `hand-build`, `groom-build`, `blink-build` restore V544 and save full detail before preview simplification. SHA256 checks and delta manifests are mandatory. `github_assets/scene-manifest.json` records retained bases. `github_release/` includes hardlinks: removing a hardlink does not reclaim its target and editing one in place changes every link.

Authoritative hand targets: `references/m3/m3_chord_mapping_v2.json`; rig fit `pipeline/build_v545_fretting_hand.py`. Groom `pipeline/build_v544_reference_groom.py` plus V546 wrapper. Blink `pipeline/build_v547_blink_alignment.py`. Actions orchestration `pipeline/github_scene_job.py`.
