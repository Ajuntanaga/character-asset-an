# Character Asset_An: current handoff

Updated 2026-11-09 UTC. The character is unfinished. Continue the active reference-led Blender build; do not restart it or treat successful scripts as visual acceptance. Detailed prior decisions, rejected trials and checkpoint provenance are preserved in [PROJECT_HISTORY.md](PROJECT_HISTORY.md).

## User direction and working constraints

- Build a film/show-quality, animation-ready character matching supplied face, hair, wardrobe, hand and guitar sheets. Show actual rendered images.
- Use the live Blender MCP on workspace 7. Loopback `127.0.0.1:9876`, per-tool approval `prompt`, no add-on auto-start. Preserve the main `V357_CLOUDRIG_CONTROLS` rig and all 1,957 drivers.
- Offload heavy builds/renders to the authorized GitHub repository and Actions. Modal is unavailable. Modest Kaggle use is permitted but has not been used. Current repository is PRIVATE; Actions works. Public fallback is authorized only if needed; do not change visibility without a reason.
- One writer; at most two independent read-only children. Keep local heavy work sequential and bounded. Do not close other Codex sessions.
- Send meaningful updates and long-wait pings to `BCA_task` with `/home/ajuntanaga/.local/bin/researchos-ntfy-publish TOPIC TITLE MESSAGE`. Reuse the encrypted credential; never print or copy it. Do not create another notification daemon.
- Keep this handoff concise for automatic context compaction. Remove reproducible caches and obsolete full-size scene copies only after preserving necessary rollback data and verifying exact restoration. Keep references, current scenes, designated checkpoints and delta bases.

## Current state (2026-11-09 UTC)

Project `/home/ajuntanaga/Projects/Blender/Character Asset_An`; remote https://github.com/Ajuntanaga/character-asset-an . Source through `cad82e4` pushed. Main rig remains V357_CLOUDRIG_CONTROLS with 1,957 drivers. New groom run42580685710 is active; no other render queued. Root is sole writer.
- Preserved main V514, native hand V522, delta base V528. Reference branch V544: `production_v544_reference_revision/Character_An_reference_revision_TRIAL_v544.blend`; SHA256 `6299f505f4b9d31b481143e70db83c04215ff2426c7752592b35686e6fd27c02`. Release and remote restore verified; do not repeat.
- Live GUI on workspace7: `production_v545_fretting_hand/run-42568146113/Character_An_fretting_hand_TRIAL_v545.blend`. Main1957 drivers. Temporary read-only diagnostics used copies and removed them; check dirty state before replacing the scene.
- V545 hands, V546 groom, V547 face/blinks, V550 guitar, V551 beard are INDEPENDENT V544 trials. None is merged or production accepted.
- Guitar run42579739576 (`959931a`) and eye run42580180604 (`cdaaf5d`) succeeded; previews downloaded and root visually reviewed. New deltas not downloaded.

## Latest visual results

- Hand42572857511 (`bb84612`): REJECTED. Index12.17, middle4.04, ring14.46, pinky8.19, thumb10.41mm errors. Earlier smaller-distance42568146113 also rejected for hooked thumb/straight distal joints. Main/native drivers1957/48.
- Face/blink42580180604 (`cdaaf5d`), `github_results/run-42580180604/previews-blink-build-25/`: all4 frames reviewed. Upper54/lower8 lashes, lower length0.55–0.75mm before fade. Sparse lower lashes help; open eyes still have a continuous heavy black rim, chalky sclera and doll stare. Frontal closed lids continuous, no visible corneal pop-through. Arc minimum boundary clearance0.20mm; no full-surface/oblique animation acceptance. Child face_next_correction investigating source of rim read-only.
- Groom42578933062 (`5b2a16a`), `github_results/run-42578933062/previews-groom-build-23/`: all3 views inspected, REJECTED hollow hoops over dark cap, hard temple blocks, no scalp part. Active42580685710 (`cad82e4`): coherent axis tilt .78+.14clump, axial pitch7–11mm, turns .78–1.10, bundle width1.5–2.2mm,28% radius fade, roots excluded within±8mm part; scalp shader clean central3mm plus2.5mm falloff each side. Preview required.
- Guitar42579739576 (`959931a`), `github_results/run-42579739576/previews-guitar-build-24/`: both images reviewed. New rounded bridge housings/knurled tuners, pickup seams/lettering and thin selector improve hardware, all saddle transforms unchanged. Maple too bright/coarse and fabric-like; brown side/tan rim wrong. Curve .22→.075,.32→.72 over-amplifies linear input .222–.321. Needs softer contrast, broader burst and dark edges. Not accepted as a whole.
- Beard42575549129 (`77cebb5`): 1.4–2.4mm fibers still dominated by blurry photo beard/moustache; short chin and flat moustache. Not accepted.
- Wardrobe actual active body slot6 V379_DARK_COTTON_JACKET, refined V384/V388; V345 suggestion was stale. Floral buttonup collar is intentional in approved design. Child wardrobe_next_correction reading active shaders, no writes.

## Hand diagnosis and next change

Authoritative targets remain `references/m3/m3_chord_mapping_v2.json`. Donor already LEFT despite .R names; do NOT reflect again. Palm length94mm. Keep pick and main rig unchanged.

Implemented per-digit distal skin BVHs (all polygon vertices >0.95 distal weight, skin material0), nearest to persistent pad anchor, max4mm, including final full-subdivision measurement. Live temporary-copy verification: Middle now samples Middle; anchor distances0.09–0.20mm. Own-pad errors I12.15/M4.00/R14.47/P8.16/T10.41mm. Sampling correctness does not solve the pose. `pad-identity-fixed-report.json` under local diagnostics. Temporary copies removed.

Exact exported kinematics and bounded scipy diagnostics are in `local_diagnostics/hand_fit_2026-11-08/`. Removing thumb, widening thumb CMC or splay, Kabsch seed, and moving pulp patch solve all still fail. Moving pulp errors I9.75/M3.93/R9.49/P4.45/T1.06mm, with pad/nail orientation failures. Axis sign test confirms positive flex bends toward palmar skin; do NOT invert axes. Bounded12-seed wrist multistart also failed: best I11.657/M.321/R14.233/P8.596/T11.345mm with orientation/limit failures. This solver path is STOPPED; do not repeat no-thumb, widened-CMC, Kabsch, moving-pulp or wrist-multistart trials.

IMPORTANT: PROJECT_HISTORY.md:375 already records the authorized index/ring fret-order crossing issue and failed endpoint fits. Do not present it as new, silently change targets, or repeat old diagnosis. The 27DOF solver uses pad35°/nail60° cones and thumb MCP/IP caps20°/15°. Need feasible coupled pose with clearance, not relaxed anatomy or point-only success.

## Cleanup, notifications and local resources

Archived V530–V541 (12 obsolete full trials) as Zstandard deltas against retained `github_release/current-v528.blend`; each decoded SHA256 matched before original removal. Reclaimed4,250,005,688bytes from scenes, plus114,783,529bytes from19 obsolete KeenTools range/tail/race fragments, each byte-compared to retained complete installer at exact offsets. **Total4,364,789,217bytes (4.36GB/4.07GiB)**. Fragment manifest `local_installer_fragment_cleanup_2026-11-09.json`. Keep complete147MB core installer; underscore/hyphen names are hardlinks, not duplicated storage. `local_archive_cleanup_2026-11-08.json` plus per-folder `.blend.archived.json` record exact restore commands/checksums. Keep base, references, V514/V522/V528/V544+.

Seventeen BCA_task notifications delivered HTTP200, latest07:44UTC. Continue every5–10minutes or milestones; no daemon. Approximately76GiB disk free,21GiB memory available, swap1.4GiB; keep heavy rendering remote. Local viewers `chafa`, `image` available. Manual compaction unavailable; keep this handoff current.

## Next work

1. Download and inspect all3 previews from groom42580685710 when complete. Do not queue more than one pending Actions job (third replaces pending).
2. Correct maple finish and dark body edge. Source `pipeline/refine_v550_maple_density.py`; hardware `pipeline/refine_v552_guitar_hardware.py` has38 new/58 hidden objects, live temporary-copy geometry/1957-driver/saddle verification already passed. No repeat needed.
3. Apply grounded eye/wardrobe corrections, then integrate improvements reversibly and review the whole character in Blender workspace7. Native hand pose remains unresolved. Character substantially below reference and unfinished.

## Commands and important details

MCP Python: `/home/ajuntanaga/Documents/Codex/Blender-MCP/.venv/bin/python pipeline/blender_mcp_call.py execute_blender_code @code:/tmp/script.py` (or `@script:`). Write code to a file; do not pass malformed inline JSON. Inspect live dirty state before replacing a scene. Never open another GUI merely because `wmctrl` misses a Wayland window. Window inventory: `/run/user/1000/researchos-workstation/window-inventory.json`.

`gh run view RUN --json status,conclusion,jobs`; `gh run download RUN --dir github_results/run-RUN`. Artifact transfers may take several minutes without output; the temporary `/tmp/gh-artifact.*.zip` grows. Poll an existing process instead of duplicating it.

Workflow `.github/workflows/blender-preview.yml`: Ubuntu24.04, pinned Blender5.2.2, CPU2threads, concurrency1, 20minute limit, artifacts7days. Modes `hand-build`, `groom-build`, `blink-build`, `guitar-build` restore V544 and save full detail before preview simplification. SHA256 checks and delta manifests are mandatory. `github_assets/scene-manifest.json` records retained bases. `github_release/` includes hardlinks: removing a hardlink does not reclaim its target and editing one in place changes every link.

Authoritative hand targets: `references/m3/m3_chord_mapping_v2.json`; rig fit `pipeline/build_v545_fretting_hand.py`. Groom `pipeline/build_v544_reference_groom.py` plus V546 wrapper. Blink `pipeline/build_v547_blink_alignment.py`. Actions orchestration `pipeline/github_scene_job.py`.
