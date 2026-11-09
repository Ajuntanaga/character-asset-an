# Character Asset_An: current handoff

Updated 2026-11-08. The character is unfinished. Continue the active reference-led Blender build; do not restart it or treat successful scripts as visual acceptance. Detailed prior decisions, rejected trials and checkpoint provenance are preserved in [PROJECT_HISTORY.md](PROJECT_HISTORY.md).

## User direction and working constraints

- Build a film/show-quality, animation-ready character matching supplied face, hair, wardrobe, hand and guitar sheets. Show actual rendered images.
- Use the live Blender MCP on workspace 7. Loopback `127.0.0.1:9876`, per-tool approval `prompt`, no add-on auto-start. Preserve the main `V357_CLOUDRIG_CONTROLS` rig and all 1,957 drivers.
- Offload heavy builds/renders to the authorized GitHub repository and Actions. Modal is unavailable. Modest Kaggle use is permitted but has not been used. Current repository is PRIVATE; Actions works. Public fallback is authorized only if needed; do not change visibility without a reason.
- One writer; at most two independent read-only children. Keep local heavy work sequential and bounded. Do not close other Codex sessions.
- Send meaningful updates and long-wait pings to `BCA_task` with `/home/ajuntanaga/.local/bin/researchos-ntfy-publish TOPIC TITLE MESSAGE`. Reuse the encrypted credential; never print or copy it. Do not create another notification daemon.
- Keep this handoff concise for automatic context compaction. Remove reproducible caches and obsolete full-size scene copies only after preserving necessary rollback data and verifying exact restoration. Keep references, current scenes, designated checkpoints and delta bases.

## Current state (2026-11-08 UTC)

Project `/home/ajuntanaga/Projects/Blender/Character Asset_An`; remote https://github.com/Ajuntanaga/character-asset-an . Source through `3dc8378` pushed. Own-digit hand surface sampling is implemented and live verified; the next groom trial rotates the loop planes toward the scalp and reduces outward pitch. Main rig remains V357_CLOUDRIG_CONTROLS with 1,957 drivers.

- Preserved main V514, native hand V522, delta base V528. Reference branch V544: `production_v544_reference_revision/Character_An_reference_revision_TRIAL_v544.blend`; SHA256 `6299f505f4b9d31b481143e70db83c04215ff2426c7752592b35686e6fd27c02`. Release and remote restore verified; do not repeat.
- Live GUI on workspace7: `production_v545_fretting_hand/run-42568146113/Character_An_fretting_hand_TRIAL_v545.blend`. Main1957 drivers. Temporary read-only diagnostics used copies and removed them; check dirty state before replacing the scene.
- V545 hands, V546 groom, V547 face/blinks, V550 guitar, V551 beard are INDEPENDENT V544 trials. None is merged or production accepted.
- All Actions jobs through42577808048 completed successfully; all preview artifacts downloaded and viewed. No job running/queued at this handoff. New groom run pending dispatch. No new deltas downloaded.

## Latest visual results

- Hand42572857511 (`bb84612`), `github_results/run-42572857511/`: REJECTED. Index12.17, middle4.04, ring14.46, pinky8.19, thumb10.41mm errors. Contact/orientation checks fail; thumb shape remains wrong. Main/native drivers1957/48. Earlier42568146113 had smaller distances but hooked thumb/straight distal joints and was also rejected.
- Face/blink42574020857 (`a08fee1`), `github_results/run-42574020857/previews-blink-build-17/`: rounder aperture and warmer skin applied. Frontal closed lids continuous, no visible corneal pop-through. Face still stares; sharp black lid rim, chalky sclera, insufficient tearline. No full-surface/oblique animation acceptance. Arc minimum boundary clearance0.20mm; preserve completed evidence.
- Groom42576959425 (`2c1fa07`), `github_results/run-42576959425/previews-groom-build-21/`: all3 views inspected. Independent direction variation did not fix the upright wire/spring loops or hard temple masses. REJECTED. Next trial changes curl-axis tilt from .30–1.00rad to 1.03–1.47rad and top pitch from4–7mm to1.5–3mm, placing loops along the scalp.
- Guitar42577808048 (`3dc8378`), `github_results/run-42577808048/previews-guitar-build-22/`: front/oblique reviewed. Contrast curve still gives faint muddy grain; investigate linear texture values before another remap. Camera wider but top horn touches frame. Brown sides, bright tan edge, bridge blocks and toggle switch do not match product photo. Not accepted.
- Beard42575549129 (`77cebb5`), `github_results/run-42575549129/previews-blink-build-20/`: beard detail/full face viewed. 1.4–2.4mm fibers visible but still dominated by blurry baked-photo beard/moustache. Short chin silhouette and flat moustache need work. Runtime successful; not accepted.

## Hand diagnosis and next change

Authoritative targets remain `references/m3/m3_chord_mapping_v2.json`. Donor already LEFT despite .R names; do NOT reflect again. Palm length94mm. Keep pick and main rig unchanged.

Implemented per-digit distal skin BVHs (all polygon vertices >0.95 distal weight, skin material0), nearest to persistent pad anchor, max4mm, including final full-subdivision measurement. Live temporary-copy verification: Middle now samples Middle; anchor distances0.09–0.20mm. Own-pad errors I12.15/M4.00/R14.47/P8.16/T10.41mm. Sampling correctness does not solve the pose. `pad-identity-fixed-report.json` under local diagnostics. Temporary copies removed.

Exact exported kinematics and bounded scipy diagnostics are in `local_diagnostics/hand_fit_2026-11-08/`. Removing thumb, widening thumb CMC or splay, Kabsch seed, and moving pulp patch solve all still fail. Moving pulp errors I9.75/M3.93/R9.49/P4.45/T1.06mm, with pad/nail orientation failures. Axis sign test confirms positive flex bends toward palmar skin; do NOT invert axes. Child hand_solver_correction now tries one bounded wrist-orientation multistart (max12 seeds/120sec, no scene writes).

IMPORTANT: PROJECT_HISTORY.md:375 already records the authorized index/ring fret-order crossing issue and failed endpoint fits. Do not present it as new, silently change targets, or repeat old diagnosis. The 27DOF solver uses pad35°/nail60° cones and thumb MCP/IP caps20°/15°. Need feasible coupled pose with clearance, not relaxed anatomy or point-only success.

## Cleanup, notifications and local resources

Archived V530–V541 (12 obsolete full trials) as Zstandard deltas against retained `github_release/current-v528.blend`; each decoded SHA256 matched before original removal. Reclaimed **4,250,005,688 bytes**. `local_archive_cleanup_2026-11-08.json` plus per-folder `.blend.archived.json` record exact restore commands/checksums. Keep base, references, V514/V522/V528/V544+.

Fourteen BCA_task notifications delivered HTTP200 during this pass, latest about07:25UTC. Continue meaningful updates every5–10minutes or milestones; no duplicate daemon. Disk approximately76GiB free, memory20GiB available, swap~0.7GiB. Keep heavy rendering remote. Local image viewers available (`chafa`, `image`). Manual compaction control unavailable; keep this handoff current for automatic compaction.

## Next work

1. Commit hand measurement fix and next groom correction; dispatch ONE groom-build. Record run and inspect all3 previews.
2. Use bounded hand multistart result only if it supplies a materially better pose; no more repeated sign/target diagnosis.
3. Correct maple linear color range and hardware; improve face/eyes/beard, wardrobe and integrate acceptable branches reversibly. Character remains substantially below supplied references and unfinished.

## Commands and important details

MCP Python: `/home/ajuntanaga/Documents/Codex/Blender-MCP/.venv/bin/python pipeline/blender_mcp_call.py execute_blender_code @code:/tmp/script.py` (or `@script:`). Write code to a file; do not pass malformed inline JSON. Inspect live dirty state before replacing a scene. Never open another GUI merely because `wmctrl` misses a Wayland window. Window inventory: `/run/user/1000/researchos-workstation/window-inventory.json`.

`gh run view RUN --json status,conclusion,jobs`; `gh run download RUN --dir github_results/run-RUN`. Artifact transfers may take several minutes without output; the temporary `/tmp/gh-artifact.*.zip` grows. Poll an existing process instead of duplicating it.

Workflow `.github/workflows/blender-preview.yml`: Ubuntu24.04, pinned Blender5.2.2, CPU2threads, concurrency1, 20minute limit, artifacts7days. Modes `hand-build`, `groom-build`, `blink-build`, `guitar-build` restore V544 and save full detail before preview simplification. SHA256 checks and delta manifests are mandatory. `github_assets/scene-manifest.json` records retained bases. `github_release/` includes hardlinks: removing a hardlink does not reclaim its target and editing one in place changes every link.

Authoritative hand targets: `references/m3/m3_chord_mapping_v2.json`; rig fit `pipeline/build_v545_fretting_hand.py`. Groom `pipeline/build_v544_reference_groom.py` plus V546 wrapper. Blink `pipeline/build_v547_blink_alignment.py`. Actions orchestration `pipeline/github_scene_job.py`.
