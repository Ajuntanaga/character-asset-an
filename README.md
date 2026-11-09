# Character Asset_An

Private working project: reference-led, rigged guitarist character for animation. **Work in progress; not production-ready.**

## Scene files

Download the [checkpoint-v542 release asset](https://github.com/Ajuntanaga/character-asset-an/releases/tag/checkpoint-v542). `current-v542.blend` is the current hand-pose trial, with the pick attached to the evaluated donor hand and redistributed index curl. The grip remains unaccepted. The [checkpoint-v528 release](https://github.com/Ajuntanaga/character-asset-an/releases/tag/checkpoint-v528) retains the earlier integration trial, intact V514 character and V522 native donor rig foundation. Verify files with `github_assets/SHA256SUMS`.

Blender 5.2.2 LTS. Current scene textures are packed and there are no linked libraries. CloudRig controls and drivers are retained. The original workstation uses a loopback Blender MCP bridge for interactive editing; remote jobs do not expose that bridge.

`references/` contains the working visual design sources. `pipeline/` includes historical build and review scripts: many depend on older local checkpoints and are not standalone rebuild recipes. `RESUME.md` records current decisions and rejected trials. Old scene versions, caches, Python environments and downloaded add-on source trees remain local. This repository and release preserve current working state, not the entire historical workstation archive.

## Processing

Run **Blender scene check and preview** manually in Actions. It downloads the pinned release scene and Blender version and validates the scene. `preview` makes a 512-pixel, 8-sample instrument render; `review` makes four 768-pixel, 32-sample renders of the instrument, grip, full character and portrait. Both use CPU rendering. Two threads, one job at a time, 20-minute job timeout, seven-day result retention. These previews reduce subdivision and hair children to fit standard hosted runner memory; they are not final quality renders or animation certification.

[First successful remote preview](https://github.com/Ajuntanaga/character-asset-an/actions/runs/42549182718): scene checksum passed, 169 objects, 1,957 main-rig drivers, no missing images; returned PNG visually inspected.

No scheduled rendering, paid GPU runner, Modal job, or automatic batch fan-out. Private Actions consumes included usage and may be billable under account settings after quota; account billing/spending limits remain authoritative. Kaggle free GPU may be considered separately for a small explicitly bounded render, with no paid expansion.

## Remaining work

Matching bilateral hand proportions, thumb/index surface contact and fretting contacts, facial and hair reference fidelity, guitar finish/shape refinements, wardrobe cleanup, deformation and animation tests, and final lighting/rendering. V529 unrestricted thumb solve was rejected for distortion; V530 hinge trial retained shape but did not achieve contact.

## Asset rights

This is a private project backup, not a public asset pack or blanket license grant. Antonia hand donor: Olaf Delgado-Friedrichs, with phantom3D, MikeJ and other contributors, CC BY 3.0; see `licenses/Antonia.txt`. The hand was cropped, fitted, rigged and posed for this character. Poly Haven denim textures retain their source CC0 provenance. User-supplied/generated character assets and third-party product photographs retain their respective rights. No add-on credentials or proprietary add-on distribution is included.
