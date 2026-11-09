# Character Asset_An

Private working project: reference-led, rigged guitarist character for animation. **Work in progress; not production-ready.**

## Scene files

The current [checkpoint-v544 release](https://github.com/Ajuntanaga/character-asset-an/releases/tag/checkpoint-v544) stores a Zstandard delta against V543. Restore it using `current-v528.blend` from [checkpoint-v528](https://github.com/Ajuntanaga/character-asset-an/releases/tag/checkpoint-v528) and the delta from [checkpoint-v543](https://github.com/Ajuntanaga/character-asset-an/releases/tag/checkpoint-v543). Download the base and both deltas into one directory, then run:

```sh
zstd -d -M1024MB --patch-from=current-v528.blend current-v543.delta.zst -o current-v543.blend
zstd -d -M1024MB --patch-from=current-v543.blend current-v544.delta.zst -o current-v544.blend
```

Verify each downloaded and reconstructed file against `github_assets/SHA256SUMS`. V544 changes the curl groom, eye openings and guitar material while retaining the V543 hand-pose trial. The 36.9 MB V544 delta restores the exact 387.4 MB scene; both base scenes must match the recorded checksums. The grip remains unaccepted. The earlier release also retains the intact V514 character and V522 native donor rig foundation.

Blender 5.2.2 LTS. Current scene textures are packed and there are no linked libraries. CloudRig controls and drivers are retained. The original workstation uses a loopback Blender MCP bridge for interactive editing; remote jobs do not expose that bridge.

`references/` contains the working visual design sources. `pipeline/` includes historical build and review scripts: many depend on older local checkpoints and are not standalone rebuild recipes. `RESUME.md` records current decisions and rejected trials. Old scene versions, caches, Python environments and downloaded add-on source trees remain local. This repository and release preserve current working state, not the entire historical workstation archive.

## Processing

Run **Blender scene check and preview** manually in Actions. `check`, `preview` and `review` restore and verify V544. `preview` makes a 512-pixel, 8-sample instrument render; `review` makes four 768-pixel, 32-sample renders of the instrument, grip, full character and portrait plus three blink close-ups. `build-review` reproduces the V544 construction from V543: finer curls, an almond eyelid contour with preserved closed-blink targets, and reduced guitar gloss. It saves the full-detail scene before preview simplification and returns the seven views, a checksum manifest and a Zstandard scene delta against V543. All modes use CPU rendering. Two threads, one job at a time, 20-minute job timeout, seven-day result retention. These previews reduce subdivision and hair children to fit standard hosted runner memory; they are not final quality renders or animation certification.

**Preserve Blender checkpoint** copies a successful build-review artifact directly to a GitHub release, avoiding another workstation upload. Enter its run ID and a version already recorded in `github_assets/scene-manifest.json`. Before dispatch, push a `checkpoint-VERSION` tag at the successful build's exact commit using the signed-in workstation account. The workflow verifies that tag and uses its own short-lived token for release uploads; no workstation credential is sent to Actions. The five-minute job checks the delta against the manifest, includes images/reports/checksums, and refuses to overwrite an existing release. Release assets persist beyond temporary Actions artifact retention. Both workflows share one concurrency group; neither runs on a schedule.

[V544 build and seven-view review](https://github.com/Ajuntanaga/character-asset-an/actions/runs/42556229782) completed in 5m42s. The downloaded delta restored the exact scene checksum locally. Report: 170 objects, 1,957 main-rig drivers, no missing images. All seven images were visually inspected. Curls are finer and eye openings less rectangular, but the closed-blink render exposes a small residual gap. Hair organization, facial surfaces and likeness remain unfinished; the guitar still looks cloudy rather than finely figured maple. The left hand is visibly larger than the replacement right hand. This is a working checkpoint, not visual or deformation acceptance.

[Remote archival](https://github.com/Ajuntanaga/character-asset-an/actions/runs/42557441243) preserved 18 release assets in 25 seconds. A subsequent [restore and scene check](https://github.com/Ajuntanaga/character-asset-an/actions/runs/42557508878) passed in 1m5s, verifying the release download, delta-chain checksums and restored Blender scene without another render.

[V542 four-view review](https://github.com/Ajuntanaga/character-asset-an/actions/runs/42554176852) completed in 8m27s. All four images were downloaded and visually inspected: they expose unresolved grip/anatomy, guitar finish, face and hair issues. Scene checksum passed, 169 objects, 1,957 main-rig drivers, no missing images. The images and scene report are retained with the V542 release as well as in the temporary Actions artifact. [First successful remote preview](https://github.com/Ajuntanaga/character-asset-an/actions/runs/42549182718) used V528.

No scheduled rendering, paid GPU runner, Modal job, or automatic batch fan-out. Private Actions consumes included usage and may be billable under account settings after quota; account billing/spending limits remain authoritative. Kaggle free GPU may be considered separately for a small explicitly bounded render, with no paid expansion.

## Remaining work

Matching bilateral hand proportions, thumb/index surface contact and fretting contacts, facial and hair reference fidelity, guitar finish/shape refinements, wardrobe cleanup, deformation and animation tests, and final lighting/rendering. V529 unrestricted thumb solve was rejected for distortion; V530 hinge trial retained shape but did not achieve contact.

## Asset rights

This is a private project backup, not a public asset pack or blanket license grant. Antonia hand donor: Olaf Delgado-Friedrichs, with phantom3D, MikeJ and other contributors, CC BY 3.0; see `licenses/Antonia.txt`. The hand was cropped, fitted, rigged and posed for this character. Poly Haven denim textures retain their source CC0 provenance. User-supplied/generated character assets and third-party product photographs retain their respective rights. No add-on credentials or proprietary add-on distribution is included.
