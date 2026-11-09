# Character Asset_An: current handoff

Updated 2026-11-08. The character is unfinished. Continue the active reference-led Blender build; do not restart it or treat successful scripts as visual acceptance. Detailed prior decisions, rejected trials and checkpoint provenance are preserved in [PROJECT_HISTORY.md](PROJECT_HISTORY.md).

## User direction and working constraints

- Build a film/show-quality, animation-ready character matching supplied face, hair, wardrobe, hand and guitar sheets. Show actual rendered images.
- Use the live Blender MCP on workspace 7. Loopback `127.0.0.1:9876`, per-tool approval `prompt`, no add-on auto-start. Preserve the main `V357_CLOUDRIG_CONTROLS` rig and all 1,957 drivers.
- Offload heavy builds/renders to the authorized GitHub repository and Actions. Modal is unavailable. Modest Kaggle use is permitted but has not been used. Current repository is PRIVATE; Actions works. Public fallback is authorized only if needed; do not change visibility without a reason.
- One writer; at most two independent read-only children. Keep local heavy work sequential and bounded. Do not close other Codex sessions.
- Send meaningful updates and long-wait pings to `BCA_task` with `/home/ajuntanaga/.local/bin/researchos-ntfy-publish TOPIC TITLE MESSAGE`. Reuse the encrypted credential; never print or copy it. Do not create another notification daemon.
- Keep this handoff concise for automatic context compaction. Remove reproducible caches and obsolete full-size scene copies only after preserving necessary rollback data and verifying exact restoration. Keep references, current scenes, designated checkpoints and delta bases.

## Current state (2026-11-08 late evening PST)

Project `/home/ajuntanaga/Projects/Blender/Character Asset_An`; remote https://github.com/Ajuntanaga/character-asset-an . All source changes through `77cebb5` pushed. Next commit varies neighboring curl planes without changing random seeds, root density, or curl dimensions. Main rig remains V357_CLOUDRIG_CONTROLS with 1,957 drivers.

- Preserved main V514, native hand V522, delta base V528. Reference branch V544: `production_v544_reference_revision/Character_An_reference_revision_TRIAL_v544.blend`; SHA256 `6299f505f4b9d31b481143e70db83c04215ff2426c7752592b35686e6fd27c02`. Release and remote restore verified; do not repeat.
- Live GUI on workspace7: `production_v545_fretting_hand/run-42568146113/Character_An_fretting_hand_TRIAL_v545.blend`. Main1957 drivers. Temporary read-only diagnostics used copies and removed them; check dirty state before replacing the scene.
- V545 hands, V546 groom, V547 face/blinks, V550 guitar, V551 beard are INDEPENDENT V544 trials. None is merged or production accepted.
- All Actions jobs through42575549129 completed successfully; all preview artifacts downloaded. No job running/queued at this handoff. No new deltas downloaded. Use existing artifacts, do not redownload.

## Latest visual results

- Hand42572857511 (`bb84612`), `github_results/run-42572857511/`: REJECTED. Index12.17, middle4.04, ring14.46, pinky8.19, thumb10.41mm errors. Contact/orientation checks fail; thumb shape remains wrong. Main/native drivers1957/48. Earlier42568146113 had smaller distances but hooked thumb/straight distal joints and was also rejected.
- Face/blink42574020857 (`a08fee1`), `github_results/run-42574020857/previews-blink-build-17/`: rounder aperture and warmer skin applied. Frontal closed lids continuous, no visible corneal pop-through. Face still stares; sharp black lid rim, chalky sclera, insufficient tearline. No full-surface/oblique animation acceptance. Arc minimum boundary clearance0.20mm; preserve completed evidence.
- Groom42574697402 (`3cfd7d6`), `github_results/run-42574697402/previews-groom-build-18/`: all3 views inspected. Outer-boundary hairline correction removes large bald patches, but repeated wire loops, hard clumps, spring crown/back and zigzag temples remain. REJECTED. Next trial adds independent ±0.28rad direction variation to the broad flow, reusing existing RNG sample so other parameters stay fixed.
- Guitar42575041175 (`77cebb5`), `github_results/run-42575041175/previews-guitar-build-19/`: both front/oblique viewed against Strandberg product photo. 2.5x grain density visible but still low-contrast cloudy gray rather than strong irregular flamed maple. Tan edge/brown side insufficiently matched; chunky bridge tuners; front camera crops upper horn. Not accepted. No outline change yet; compare camera-aligned silhouette before changing it.
- Beard42575549129 (`77cebb5`), `github_results/run-42575549129/previews-blink-build-20/`: beard detail/full face viewed. 1.4–2.4mm fibers visible but still dominated by blurry baked-photo beard/moustache. Short chin silhouette and flat moustache need work. Runtime successful; not accepted.

## Hand diagnosis and next change

Authoritative targets remain `references/m3/m3_chord_mapping_v2.json`. Donor already LEFT despite .R names; do NOT reflect again. Palm length94mm. Keep pick and main rig unchanged.

Confirmed via temporary live MCP copies: latest Middle contact ray hits INDEX distal skin (97.7% Index3/2.3%Index2). Other4 rays hit their own distal finger. Reproduce full report points within0.00041mm. Rest pad transformed by distal bone is within0.09–0.25mm of evaluated own-pad surface. Replace global first-hit rays with per-digit distal skin BVHs (all polygon vertices >0.95 distal weight, skin material0), nearest to persistent pad anchor, max4mm. Use same identity-preserving method for final full-subdivision measurement. NOT YET IMPLEMENTED.

Double-precision scipy diagnostic (no neck BVH collision, diagnostic only) still converges to bad poses. Exact model/rest joints/axes/pads and probes saved under `local_diagnostics/hand_fit_2026-11-08/`. Existing limits give index11.66/ring14.23/pinky8.60/thumb11.35mm; position/orientation incompatibility remains. Removing thumb targets or widening thumb CMC does not fix all fingers. A geometry-based Kabsch seed also fails. Index/Ring splay ±55° ablation improves loss but still errors10.82/8.44/7.17/10.38mm; Index returns inside original limit. Thus saturated splay is NOT a sufficient diagnosis; do not simply widen anatomy limits. Child hand_solver_correction is isolating position vs orientation constraints; root sole writer.

Current solver: 27DOF, one analytic solve then evaluated refinement; pad35°/nail60° cones; thumb MCP/IP caps20°/15°. Analytic and Blender joint positions match. Need a concrete kinematic/target-contact correction before another expensive hand run.

## Cleanup, notifications and local resources

Archived V530–V541 (12 obsolete full trials) as Zstandard deltas against retained `github_release/current-v528.blend`; each decoded SHA256 matched before original removal. Reclaimed **4,250,005,688 bytes**. `local_archive_cleanup_2026-11-08.json` plus per-folder `.blend.archived.json` record exact restore commands/checksums. Keep base, references, V514/V522/V528/V544+.

Twelve BCA_task notifications delivered HTTP200 during this pass, latest about23:02PST. Continue meaningful updates every5–10minutes or milestones; no duplicate daemon. Disk approximately76GiB free, memory20GiB available, swap~0.7GiB. Keep heavy rendering remote. Local image viewers available (`chafa`, `image`). Manual compaction control unavailable; keep this handoff current for automatic compaction.

## Next work

1. Commit/push neighbor curl variation and dispatch ONE groom-build; record run. Do not submit a third workflow while one running/one pending.
2. Fix identity-preserving hand surface measurement, then resolve kinematic fit using cheap exported-model diagnostics before rendering. Preserve joint anatomy and approved targets.
3. Improve flamed-maple contrast/edge finish, facial-hair silhouette and eye realism; validate each with actual remote previews. Integrate acceptable branches reversibly, then deformation/animation review. Character is unfinished.

## Commands and important details

MCP Python: `/home/ajuntanaga/Documents/Codex/Blender-MCP/.venv/bin/python pipeline/blender_mcp_call.py execute_blender_code @code:/tmp/script.py` (or `@script:`). Write code to a file; do not pass malformed inline JSON. Inspect live dirty state before replacing a scene. Never open another GUI merely because `wmctrl` misses a Wayland window. Window inventory: `/run/user/1000/researchos-workstation/window-inventory.json`.

`gh run view RUN --json status,conclusion,jobs`; `gh run download RUN --dir github_results/run-RUN`. Artifact transfers may take several minutes without output; the temporary `/tmp/gh-artifact.*.zip` grows. Poll an existing process instead of duplicating it.

Workflow `.github/workflows/blender-preview.yml`: Ubuntu24.04, pinned Blender5.2.2, CPU2threads, concurrency1, 20minute limit, artifacts7days. Modes `hand-build`, `groom-build`, `blink-build`, `guitar-build` restore V544 and save full detail before preview simplification. SHA256 checks and delta manifests are mandatory. `github_assets/scene-manifest.json` records retained bases. `github_release/` includes hardlinks: removing a hardlink does not reclaim its target and editing one in place changes every link.

Authoritative hand targets: `references/m3/m3_chord_mapping_v2.json`; rig fit `pipeline/build_v545_fretting_hand.py`. Groom `pipeline/build_v544_reference_groom.py` plus V546 wrapper. Blink `pipeline/build_v547_blink_alignment.py`. Actions orchestration `pipeline/github_scene_job.py`.
