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

Project `/home/ajuntanaga/Projects/Blender/Character Asset_An`; remote https://github.com/Ajuntanaga/character-asset-an . Source through `81f8443` pushed; V556 combined correction prepared for the next commit. V554 run42585046848 and V555 run42586200698 succeeded; all ten preview images reviewed. Main rig remains V357_CLOUDRIG_CONTROLS with 1,957 drivers. Root is sole writer. Read-only children completed posterior-mask geometry and archive-candidate checks; root remains sole writer.
- Preserved main V514, native hand V522, delta base V528. Reference branch V544: `production_v544_reference_revision/Character_An_reference_revision_TRIAL_v544.blend`; SHA256 `6299f505f4b9d31b481143e70db83c04215ff2426c7752592b35686e6fd27c02`. Release and remote restore verified; do not repeat.
- Live GUI on workspace7: `production_v545_fretting_hand/run-42568146113/Character_An_fretting_hand_TRIAL_v545.blend`. Main1957 drivers, dirty=false at08:40UTC. Check again before replacing the scene. V554 delta download completed08:52UTC in `github_results/run-42585046848/blender-combined-build-31/`; restore and GUI load pending.
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
- V554 raised jacket light albedo to(.045,.050,.048), worsening broad baked-light bands. V556 pending correction replaces only the ramp factor with existing rest-position V384_Weave_height, narrow charcoal range(.008,.009,.009)–(.018,.021,.020). Retains colored-detail saturation mask, roughness and bump. No render of this correction yet.
- Python syntax, YAML and git diff whitespace passed including triangulation correction. V554 must preserve1957 drivers and save full detail before simplified previews.

V555 de-lit face run42586200698 at81f8443 succeeded08:33UTC. All four views inspected: baked shading reduced but face remains soft/waxy, and profile has temple/sideburn smearing. Rejected as a final texture. Original4K atlas preserved. Generated1254px derivative SHA256 `fa8bbf0db871b3b77461fae8f728025a045498a374c6a4a3fb7912e79aa0af1a`, provenance `assets/generated/face_delit_v555/`. Keep optional `delit_face=false` for ordinary combined trials. No V555 full-scene download needed.

V556 prepared08:53UTC, not rendered yet. Dark lower nape is raw Tripo hair baked into V377 skin faces, outside the old V371 mask (whose minimum z1.655 is ear-top height). Extend only the connected posterior skin region with center z1.575–1.668 and y>=.035, excluding the ear ellipse, seeded once at maximum-y hair-touch face. Independent snapshot replay selects5264 faces, no front/lateral islands. Runtime perimeter and interior-size gates still apply. Shorten nape fibers toward2–4mm with3.8mm root spacing; preserve ordinary6.5mm spacing elsewhere. Narrow reopened lid height from8/3.8mm to6.2/2.3mm and power from.52/.58 to.82/.95. Jacket uses weave height as narrow charcoal albedo factor. Combined job renders face, profile, character, wardrobe and blink0/.5/1; full scene saved before preview simplification. Keep delit_face=false.

## Hand diagnosis and next change

Authoritative targets remain `references/m3/m3_chord_mapping_v2.json`. Donor already LEFT despite .R names; do NOT reflect again. Palm length94mm. Keep pick and main rig unchanged.

Implemented per-digit distal skin BVHs (all polygon vertices >0.95 distal weight, skin material0), nearest to persistent pad anchor, max4mm, including final full-subdivision measurement. Live temporary-copy verification: Middle now samples Middle; anchor distances0.09–0.20mm. Own-pad errors I12.15/M4.00/R14.47/P8.16/T10.41mm. Sampling correctness does not solve the pose. `pad-identity-fixed-report.json` under local diagnostics. Temporary copies removed.

Exact exported kinematics and bounded scipy diagnostics are in `local_diagnostics/hand_fit_2026-11-08/`. Removing thumb, widening thumb CMC or splay, Kabsch seed, and moving pulp patch solve all still fail. Moving pulp errors I9.75/M3.93/R9.49/P4.45/T1.06mm, with pad/nail orientation failures. Axis sign test confirms positive flex bends toward palmar skin; do NOT invert axes. Bounded12-seed wrist multistart also failed: best I11.657/M.321/R14.233/P8.596/T11.345mm with orientation/limit failures. This solver path is STOPPED; do not repeat no-thumb, widened-CMC, Kabsch, moving-pulp or wrist-multistart trials.

IMPORTANT: PROJECT_HISTORY.md:375 already records the authorized index/ring fret-order crossing issue and failed endpoint fits. Do not present it as new, silently change targets, or repeat old diagnosis. The 27DOF solver uses pad35°/nail60° cones and thumb MCP/IP caps20°/15°. Need feasible coupled pose with clearance, not relaxed anatomy or point-only success.

Pending user input: permission to reassign which fingers play the SAME strings/frets for a natural grip, versus retaining the named-finger assignments. Question already sent asynchronously; do not repeat it or change assignments before the answer.

## Cleanup, notifications and local resources

Archived V530–V541 (12 obsolete full trials) as Zstandard deltas against retained `github_release/current-v528.blend`; each decoded SHA256 matched before original removal. Reclaimed4,250,005,688bytes from scenes, plus114,783,529bytes from19 obsolete KeenTools range/tail/race fragments, each byte-compared to retained complete installer at exact offsets. **Previous subtotal4,364,789,217bytes**. Also removed4 superseded, rejected generated deltas from runs42568298993/42571052107/42564726025/42566087166, retaining all previews/reports and current V545. Reclaimed58,261,755bytes; manifest `local_rejected_delta_cleanup_2026-11-09.json`. **Total4,423,050,972bytes (4.42GB/4.12GiB)**. Fragment manifest `local_installer_fragment_cleanup_2026-11-09.json`. Keep complete147MB core installer; underscore/hyphen names are hardlinks, not duplicated storage. `local_archive_cleanup_2026-11-08.json` plus per-folder `.blend.archived.json` record exact restore commands/checksums. Keep base, references, V514/V522/V528/V544+.

Additionally archived V500/501/506/507/508/523–527 with streamed restoration SHA256 verification, reclaiming3,547,257,288bytes. Aggregate `local_archive_cleanup_2026-11-09_older.json`; every folder has exact restore metadata. **Cumulative7,970,308,260bytes (7.97GB/7.42GiB) reclaimed.** V542 hardlink preserved. Never delete retained V528 base or designated checkpoints.

Twenty-seven BCA_task notifications delivered HTTP200; continue milestone and5–10minute updates. Continue every5–10minutes or milestones; no daemon. Approximately79GiB disk free,19GiB memory available, swap1.9GiB; keep heavy rendering remote. Local viewers `chafa`, `image` available. Manual compaction unavailable; keep this handoff current.

## Next work

1. Validate/commit/push V556 and dispatch one combined-build without de-lit face. Review seven actual renders; keep hand and reference targets unchanged.
2. Restore downloaded V554 against V544 and verify SHA, check GUI dirty state, then load on workspace7. Preserve prior scenes and keep trial status.
3. Correct face proportions/texture from reference comparison. Native hand pose remains unresolved; do not rerun stopped solver sweeps. Continue reference-led corrections.

## Commands and important details

MCP Python: `/home/ajuntanaga/Documents/Codex/Blender-MCP/.venv/bin/python pipeline/blender_mcp_call.py execute_blender_code @code:/tmp/script.py` (or `@script:`). Write code to a file; do not pass malformed inline JSON. Inspect live dirty state before replacing a scene. Never open another GUI merely because `wmctrl` misses a Wayland window. Window inventory: `/run/user/1000/researchos-workstation/window-inventory.json`.

`gh run view RUN --json status,conclusion,jobs`; `gh run download RUN --dir github_results/run-RUN`. Artifact transfers may take several minutes without output; the temporary `/tmp/gh-artifact.*.zip` grows. Poll an existing process instead of duplicating it.

Workflow `.github/workflows/blender-preview.yml`: Ubuntu24.04, pinned Blender5.2.2, CPU2threads, concurrency1, 20minute limit, artifacts7days. Modes `hand-build`, `groom-build`, `blink-build`, `guitar-build`, `combined-build` restore V544 and save full detail before preview simplification. SHA256 checks and delta manifests are mandatory. `github_assets/scene-manifest.json` records retained bases. `github_release/` includes hardlinks: removing a hardlink does not reclaim its target and editing one in place changes every link.

Authoritative hand targets: `references/m3/m3_chord_mapping_v2.json`; rig fit `pipeline/build_v545_fretting_hand.py`. Groom `pipeline/build_v544_reference_groom.py` plus V546 wrapper. Blink `pipeline/build_v547_blink_alignment.py`. Actions orchestration `pipeline/github_scene_job.py`.
