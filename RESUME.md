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

Project `/home/ajuntanaga/Projects/Blender/Character Asset_An`; remote https://github.com/Ajuntanaga/character-asset-an . Source through `d2bd151` pushed. V556 run42589302878 succeeded09:03UTC; all seven actual preview images reviewed. V557 shared-lock groom and lower synthetic skin relief are prepared for cloud execution. Main rig remains V357_CLOUDRIG_CONTROLS with 1,957 drivers. Root is sole writer; no children or local heavy jobs active.
- Preserved main V514, native hand V522, delta base V528. Reference branch V544: `production_v544_reference_revision/Character_An_reference_revision_TRIAL_v544.blend`; SHA256 `6299f505f4b9d31b481143e70db83c04215ff2426c7752592b35686e6fd27c02`. Release and remote restore verified; do not repeat.
- Live GUI on workspace7: `production_v554_combined_reference/run-42585046848/Character_An_combined_reference_TRIAL_v554.blend`. Restored SHA256 `384976aaed800dced83dece932b6717bea29cbe51235990601d9b9bd55d6f9a3` matches cloud manifest. Main1957 drivers, dirty=false at08:56UTC,247 datablock objects. Textured SOLID viewport; existing second Blender window is an Image Editor. Check dirty state before replacing scene.
- V545 hands, V546 groom, V547 face/blinks, V550 guitar, V551 beard are INDEPENDENT V544 trials. None is merged or production accepted.

## Latest visual results and V554 trial

- Eye42581882190 (`1d0c743`): all6 views reviewed. Frontal closed lids continuous; clay smoother than textured skin. Open face still has a heavy continuous black upper rim, chalky sclera, doll stare, baked photographic creases/beard. No oblique/full-surface blink acceptance.
- Groom42582166572 (`77337e2`): reviewed; still repeated hollow curl rows, coarse scanned cap/sideburn blocks and an unnaturally straight scalp trench. Not accepted.
- Guitar42583595731 (`b4441fa`): both previews downloaded; guitar-front reviewed. New generated V553 maple albedo reduces distracting vertical crosshatching and improves broad soft flame. Shape/hardware still require reference review. `assets/generated/gray_maple_v553/SOURCE.json` preserves image provenance; old texture retained.
- Beard42575549129 (`77cebb5`): short fibers still dominated by blurry photo beard and flat moustache; not accepted or merged.
- Wardrobe front reviewed: leather-like broad highlights, weak weave/check variation. V379 already uses Poly Haven roughness/height. V388 HSV is correct; no mode change. Floral collar intentional.

V554 combined trial42585046848 at39896d7 succeeded08:28UTC. `pipeline/build_v554_combined_trial.py`, mode `combined-build`, combines V546 groom, V547 eye alignment and V553 maple/V552 hardware without intermediate saves. Hands remain V544 and unresolved. All six views inspected: face remains doll-like, curl rows uniform, lower nape is a dark smooth scan; jacket has broad gray bands. 209objects,1957drivers,zero missing images. Trial not accepted.

- New `refine_v554_scalp_surface.py`: weld coincident UV seam coordinates, select456-group outer hairline, flood its interior, smooth120 passes with fixed boundary and7mm movement cap. Apply identical displacement to every shape key. Fill internal skin-labelled holes. Root sampling and collision use this same current smoothed scalp, triangulated with original UVMap; never use the archived lumpy V371 surface for this trial. Offline actual-mesh topology confirmed15536 interior groups and no face flood.
- Remove global strand x-clamp. Replace170mm straight part with70mm irregular tapered part and pigmented scalp shader. Vary curl axes/radius/handedness; no claim of natural hair until rendered.
- Replace only continuous upper-margin slot0 black material with copied warm waterline tissue; individual V394 lashes retain dark material.
- V554 raised jacket light albedo to(.045,.050,.048), worsening broad baked-light bands. V556 replaces only the ramp factor with existing rest-position V384_Weave_height, narrow charcoal range(.008,.009,.009)–(.018,.021,.020). Broad gray bands reduced in actual render; jacket remains too leathery and smooth. Retains colored-detail saturation mask, roughness and bump.
- Python syntax, YAML and git diff whitespace passed including triangulation correction. V554 must preserve1957 drivers and save full detail before simplified previews.

V555 de-lit face run42586200698 at81f8443 succeeded08:33UTC. All four views inspected: baked shading reduced but face remains soft/waxy, and profile has temple/sideburn smearing. Rejected as a final texture. Original4K atlas preserved. Generated1254px derivative SHA256 `fa8bbf0db871b3b77461fae8f728025a045498a374c6a4a3fb7912e79aa0af1a`, provenance `assets/generated/face_delit_v555/`. Keep optional `delit_face=false` for ordinary combined trials. No V555 full-scene download needed.

V556 run42589302878 atd2bd151 succeeded09:03UTC. Previews downloaded to `github_results/run-42589302878/previews-combined-build-33/`; all seven viewed. Posterior nape now covered, but lower edge blunt; hair remains repetitive coils. Narrower lids reduce excessive eye white; eye corners remain unnaturally flat/dark and facial texture waxy. Frontal blink0/.5/1 closes continuously, actual control values verified. Full character still has unequal-looking hands and unresolved contact. 209scene objects,1957drivers,zero missing images. Full-scene artifact not downloaded; do not promote as finished.

V556 posterior extension selects only connected back skin y>=.035,z>=1.575, ear exclusion, one max-y hair-touch seed;5264faces, no front/lateral islands. Nape fibers2–4mm, root spacing3.8mm; elsewhere6.5mm. Lid heights6.2/2.3mm, powers.82/.95. Keep delit_face=false.

V557 `pipeline/build_v557_reference_locks.py` replaces independent fiber coils with shared partial-lock centerlines, parallel-transport bundle frames, and dense short wavy undercoat. Sparse macro guides9–14mm, nape4.5mm;33points per strand; variable partial turns. Part thinning occurs once after root sampling, rather than filling the lane through retries. Native curves and existing bone parenting retained. Original photo atlas unchanged; inherited synthetic pore strength drops.18→.04 and distance55→20µm on face/photo/lid materials. Python syntax and diff whitespace pass; visual result pending cloud execution.

## Hand diagnosis and next change

Authoritative targets remain `references/m3/m3_chord_mapping_v2.json`. Donor already LEFT despite .R names; do NOT reflect again. Palm length94mm. Keep pick and main rig unchanged.

Implemented per-digit distal skin BVHs (all polygon vertices >0.95 distal weight, skin material0), nearest to persistent pad anchor, max4mm, including final full-subdivision measurement. Live temporary-copy verification: Middle now samples Middle; anchor distances0.09–0.20mm. Own-pad errors I12.15/M4.00/R14.47/P8.16/T10.41mm. Sampling correctness does not solve the pose. `pad-identity-fixed-report.json` under local diagnostics. Temporary copies removed.

Exact exported kinematics and bounded scipy diagnostics are in `local_diagnostics/hand_fit_2026-11-08/`. Removing thumb, widening thumb CMC or splay, Kabsch seed, and moving pulp patch solve all still fail. Moving pulp errors I9.75/M3.93/R9.49/P4.45/T1.06mm, with pad/nail orientation failures. Axis sign test confirms positive flex bends toward palmar skin; do NOT invert axes. Bounded12-seed wrist multistart also failed: best I11.657/M.321/R14.233/P8.596/T11.345mm with orientation/limit failures. This solver path is STOPPED; do not repeat no-thumb, widened-CMC, Kabsch, moving-pulp or wrist-multistart trials.

IMPORTANT: PROJECT_HISTORY.md:375 already records the authorized index/ring fret-order crossing issue and failed endpoint fits. Do not present it as new, silently change targets, or repeat old diagnosis. The 27DOF solver uses pad35°/nail60° cones and thumb MCP/IP caps20°/15°. Need feasible coupled pose with clearance, not relaxed anatomy or point-only success.

Pending user input: permission to reassign which fingers play the SAME strings/frets for a natural grip, versus retaining the named-finger assignments. Question already sent asynchronously; do not repeat it or change assignments before the answer.

## Cleanup, notifications and local resources

Archived V530–V541 (12 obsolete full trials) as Zstandard deltas against retained `github_release/current-v528.blend`; each decoded SHA256 matched before original removal. Reclaimed4,250,005,688bytes from scenes, plus114,783,529bytes from19 obsolete KeenTools range/tail/race fragments, each byte-compared to retained complete installer at exact offsets. **Previous subtotal4,364,789,217bytes**. Also removed4 superseded, rejected generated deltas from runs42568298993/42571052107/42564726025/42566087166, retaining all previews/reports and current V545. Reclaimed58,261,755bytes; manifest `local_rejected_delta_cleanup_2026-11-09.json`. **Total4,423,050,972bytes (4.42GB/4.12GiB)**. Fragment manifest `local_installer_fragment_cleanup_2026-11-09.json`. Keep complete147MB core installer; underscore/hyphen names are hardlinks, not duplicated storage. `local_archive_cleanup_2026-11-08.json` plus per-folder `.blend.archived.json` record exact restore commands/checksums. Keep base, references, V514/V522/V528/V544+.

Additionally archived V500/501/506/507/508/523–527 with streamed restoration SHA256 verification, reclaiming3,547,257,288bytes. Aggregate `local_archive_cleanup_2026-11-09_older.json`; every folder has exact restore metadata. **Cumulative7,970,308,260bytes (7.97GB/7.42GiB) reclaimed.** V542 hardlink preserved. Never delete retained V528 base or designated checkpoints.

Additionally archived V497/495/494/493/491/490/484/482/481/478 with streamed restoration SHA256 verification, reclaiming3,529,332,789bytes. Manifest `local_archive_cleanup_2026-11-09_pre500.json`. **Cumulative11,499,641,049bytes (11.50GB/10.71GiB) reclaimed.** V483 designated checkpoint retained. No archive job is running.

Thirty BCA_task notifications delivered HTTP200, latest09:06UTC. Continue every5–10minutes or milestones; no daemon. Approximately82GiB disk free,15GiB memory available, swap2.0GiB; keep heavy rendering remote. Local viewers `chafa`, `image` available. Manual compaction unavailable; keep this handoff current.

## Next work

1. Commit/push and dispatch V557 combined-build with delit_face=false; inspect actual previews before accepting hair changes. Keep hand targets unchanged pending user answer.
2. V554 restored and loaded on workspace7; show actual cloud images in existing Blender Image Editor. Restore a newer verified delta only if it improves the result.
3. Correct face proportions/texture from reference comparison. Native hand pose remains unresolved; do not rerun stopped solver sweeps. Continue reference-led corrections.

## Commands and important details

MCP Python: `/home/ajuntanaga/Documents/Codex/Blender-MCP/.venv/bin/python pipeline/blender_mcp_call.py execute_blender_code @code:/tmp/script.py` (or `@script:`). Write code to a file; do not pass malformed inline JSON. Inspect live dirty state before replacing a scene. Never open another GUI merely because `wmctrl` misses a Wayland window. Window inventory: `/run/user/1000/researchos-workstation/window-inventory.json`.

`gh run view RUN --json status,conclusion,jobs`; `gh run download RUN --dir github_results/run-RUN`. Artifact transfers may take several minutes without output; the temporary `/tmp/gh-artifact.*.zip` grows. Poll an existing process instead of duplicating it.

Workflow `.github/workflows/blender-preview.yml`: Ubuntu24.04, pinned Blender5.2.2, CPU2threads, concurrency1, 20minute limit, artifacts7days. Modes `hand-build`, `groom-build`, `blink-build`, `guitar-build`, `combined-build` restore V544 and save full detail before preview simplification. SHA256 checks and delta manifests are mandatory. `github_assets/scene-manifest.json` records retained bases. `github_release/` includes hardlinks: removing a hardlink does not reclaim its target and editing one in place changes every link.

Authoritative hand targets: `references/m3/m3_chord_mapping_v2.json`; rig fit `pipeline/build_v545_fretting_hand.py`. Groom `pipeline/build_v544_reference_groom.py` plus V546 wrapper. Blink `pipeline/build_v547_blink_alignment.py`. Actions orchestration `pipeline/github_scene_job.py`.
