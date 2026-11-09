## 2026-11-08 V542 index curl redistribution

Loaded V541 through live MCP; reference hand_pose_sheet_v1.png re-viewed. Bounded three-joint index solve retains original radial contact-patch target with relaxed-angle regularization. Index angles changed24.90/100.58/10.81 to29.48/85.00/38.06degrees; coarse contact patch shifts3.129mm. Saved production_v542_index_curl/Character_An_index_curl_TRIAL_v542.blend and front.png/side.png, check.json. Both images viewed: hook less sharp, but hand remains smooth/oversimplified relative to reference and pick contact is not accepted. V542 now live; V541/V540 remain unchanged. Main1957drivers intact. Next refit opposing thumb/index contact under index PIP<=85degree constraint, preserving exposed tip and bone attachment; then reachable wrist/string positioning. Do not claim 3mm surface displacement is maintained contact. Script syntax verified. Host17GiB available,swap512KiB,69GiB disk available. No cloud jobs. Full character objective remains incomplete.

## 2026-11-08 V541 pick exposure comparison

Rendered 3mm and6mm plectrum slides along mesh tip axis using full bone-parent inverse transform. Viewed front_6mm.png and side_6mm.png: tip is more exposed, but remains close to curved index and wrist/playing position remains unresolved. Saved six-millimeter working variant production_v541_pick_exposure/Character_An_pick_exposure_TRIAL_v541.blend; this is now live. Main1957drivers retained. Source V540 unchanged. Trial script restores V540 after comparison; /tmp/save_v541.py subsequently applies6mm and saves V541. No final contact/animation acceptance. Next improve finger curl and evaluated wrist orientation with reachable string target; do not describe tip exposure alone as correct playing grip. No cloud compute used.

## 2026-11-08 V540 deform-hand pick attachment fixed

Saved production_v540_pick_attachment/Character_An_pick_attachment_v540.blend via live MCP; scene remains loaded. Pick now bone-parented to V528_NATIVE_RIG.R / DEF-Hand.R. Preserve full affine transform in matrix_parent_inverse with identity basis: direct matrix_world assignment decomposes the reflected donor transform and changed pose, so that attempt was rejected before saving. Initial world matrix error1.19e-7; three wrist motion checks (neutral, +15degrees with25mm lift, -15degrees with15mm lateral/20mm lift) preserve relative pick-to-hand matrix within2.99e-7. Main1957drivers intact. Pinch render viewed: attachment is fixed, but grip remains angular, tip insufficiently exposed, and playing position unresolved. Not final animation or contact acceptance. Next bounded pick-exposure comparison and evaluated-hand wrist positioning; no Modal/Kaggle jobs started.

## 2026-11-08 V539 whole-grip wrist trial rejected

Executed pipeline/trial_v539_playing_wrist.py via live MCP from V538. Bounded rigid wrist search uses evaluated hand vertices and targets pick tip at nearest string plus0.5mm. Best candidate within70degree rotation (-20,-60 axes) still predicts17.74mm penetration of the infinite string plane. Actual rig arm reach clips desired wrist by22.09mm; tip remains19.43mm from string, hand intersects S1/S2/S4 and sampled clearance is negative0.936mm. Saved production_v539_playing_wrist/Character_An_playing_wrist_TRIAL_v539.blend and check.json, pinch/instrument images for diagnosis ONLY; rejected, V538 restored.1957drivers intact. Pinch image reviewed. The image also shows the pick separated toward the cuff: the assumed world rotation of IK-Hand.R does not reproduce the same evaluated donor-hand rotation. Therefore this trial does NOT establish that all rigid grip placements fail. Next derive the pick transform from the actual evaluated DEF-Hand.R before/after matrix, rather than requested control rotation, and resolve reach by moving the playing target along the strings. Then assess finger curl and pick exposure. Do not promote trial or repeat nearest-string rigid translation as solution. Script compiles. Goal incomplete.

## 2026-11-08 V538 pick tip direction

Loaded V537 through live MCP. Rotated existing pick63.37degrees within its contact plane toward nearest string and placed nominal contact12mm behind its actual mesh tip (source vertices0/48). Saved production_v538_pick_tip/Character_An_pick_tip_TRIAL_v538.blend, pinch.png, instrument.png, check.json. Pinch visually reviewed: broad pick back visible above thumb, pointed end only slightly exposed below thumb; not final grip. Evaluated hand has no string centerline crossings and2.304mm sampled clearance. Actual tip remains40.808mm from nearest string and1.024mm from nearest skin. Next must coordinate wrist orientation and reach to bring exposed tip to playing string while preserving skin clearance; do not solve with pick translation alone.1957 drivers retained, V537 pick restored live. Script compiles. Host18GiB available,swap2.6GiB; no cloud work. Full goal incomplete.

## 2026-11-08 V536–V537 opposing contact trials

V536 Jacobian fit stopped with 12.65mm contact residual; rejected. V537 bounded coordinate descent of four thumb and three index angles reduces coarse fixed skin-patch residual to 0.456mm, separation1.516mm for 0.840mm pick thickness plus clearance; opposing-normal dot -0.897. All1957 main drivers preserved. Saved production_v537_opposed_contact/Character_An_opposed_contact_TRIAL_v537.blend with contact.json, pinch.png and instrument.png. Both V537 images visually inspected: thumb/index opposition improved, but pick barely exposed and not yet oriented/positioned for string attack; index has a sharp bent silhouette. These coarse patch metrics do not establish final subdivided surface contact, collision clearance or animation acceptance. NOT promoted. Live V535 restored after script. Next orient pick tip and coordinated wrist toward intended string, verify evaluated contacts/clearance, then resolve bilateral hand scale mismatch; full character remains incomplete. User permits modest optional Kaggle compute; no Kaggle job/upload started, no Modal use.

## 2026-11-08 V534–V535 reachable picking wrist

V534 outward-only wrist correction remained intersecting S1/S2/S3. Live rig inspection identified IK-M-Hand.R Limit Distance targeting ROOT-UpperArm.R, with nearly straight elbow and control beyond reach. V535 places IK-Hand.R at an outward/upward target within 98% of current shoulder-wrist distance, preserving constraints and all1957drivers. Actual wrist target error0.000000849m; delta approximately(0.17,-16.76,34.91)mm. Evaluated hand BVH reports no string centerline crossings and minimum sampled string-surface clearance2.304mm. Instrument and pinch renders visually reviewed: clearance improved, but pick remains incorrectly supported near index nail, not accepted opposing pad/lateral-index contact. Pick is also above playing position; do not promote as final grip. Separate saved trial production_v535_reachable_wrist/Character_An_wrist_clearance_TRIAL_v535.blend; images instrument.png,pinch.png,character.png; report check.json. Live scene restored V533 after execution. Next coordinate wrist orientation, thumb and index with pick tip near intended string, retaining reachable arm target; unequal bilateral hand proportions remain unresolved. No cloud jobs; modest optional Kaggle permission retained. Modal unavailable.

## 2026-11-08 V532–V533 explicit thumb pad and nail recovery

Live MCP confirmed all V528 hand polygons were material0, including nails. Recovered nail vertices by exact source-coordinate KD matching against V519 donor material5 (source skin9); V532/V533 now restore nail material in saved copies. Selected95 thumb pad vertices opposite the source nail radial direction, excluding65 distal nail vertices. V532 bounded fit still has1.253mm coarse target gap and visibly wrong pick orientation. V533 seats rigid pick using a12vertex palmar patch and transformed surface normal, rather than nearest arbitrary thumb vertex; visually pick moves off thumbnail toward pad side. Images production_v533_pick_seating/pinch.png and instrument.png reviewed. Still NOT accepted: index contact unverified, string intersections remain, pick extent/orientation needs coordinated grip review. Separate full scene trial production_v533_pick_seating/Character_An_thumb_surface_TRIAL_v533.blend saved. Main1957drivers preserved; original V528 thumb, pick, material assignments and camera restored after execution. Scripts compile and MCP success. Next correct wrist clearance and coordinated index/curl pose around seated pick; do not claim final contact based on coarse vertex distance. Original material loss likely from clearing material slots before remapping source polygon indices in integration script; future integrations must snapshot indices before clear. No additional cloud jobs.

## 2026-11-08 V531 surface fit rejected after visual review

Saved reversible trial production_v531_thumb_surface/Character_An_thumb_surface_TRIAL_v531.blend and instrument.png/pinch.png using pipeline/trial_v531_thumb_surface.py. Bounded thumb opposition and flexion reduced nearest coarse thumb vertex target gap to 0.716mm, preserving 1957 main drivers. Live V528 pose restored in finally. NOT accepted: pinch closeup shows pick beside/across dorsal thumbnail rather than verified opposing thumb pad and lateral index contact; strings visibly intersect curled fingers. Nearest-vertex distance is insufficient and must not be presented as contact acceptance. Next grip correction must identify palmar pad surface and its normal, coordinate thumb/index/pick orientation, and clear the string plane before promotion. Do not repeat unconstrained nearest-surface optimization. Modal unavailable; user permits modest optional Kaggle GPU work, but no Kaggle job or upload has been started. Existing bounded GitHub Actions preview remains the verified offload route.

## 2026-11-08 GitHub backup and bounded processing

Private repository: https://github.com/Ajuntanaga/character-asset-an . Commit1330329 uploaded build scripts, references, attribution and handoff. Release checkpoint-v528 has all four assets confirmed uploaded: current-v528.blend (358071211 bytes), preserved-v514.blend (357867321 bytes), native-hand-v522.blend (732537 bytes), SHA256SUMS. Full scene assets are release downloads, not Git/LFS objects. Local github_release assets are hardlinks: do not modify them in place.

Manual preview submitted: https://github.com/Ajuntanaga/character-asset-an/actions/runs/42549091532 . Two CPU threads, 512px,8samples, reduced subdivision/hair,20minute timeout, one concurrent job,7day artifact retention. Initial run failed at Blender download with HTTP403. Switched to the NLUUG mirror listed by Blender, retaining the exact SHA256. Retry https://github.com/Ajuntanaga/character-asset-an/actions/runs/42549182718 completed successfully. Downloaded and visually inspected github_results/run-42549182718/blender-preview-2/instrument-preview.png: remote Cycles render works; pinch remains unresolved and guitar finish reads overly metallic. Report confirms Blender5.2.2 LTS,169objects,1957main drivers,zero missing images. This is reduced-detail preview proof only, not deformation or final-quality acceptance. No schedules or paid GPU runner. Private account remaining included minutes could not be queried with current token; account limits govern billing. Modal remains unavailable. Kaggle permitted only for modest occasional compute; no Kaggle job or data upload started.

## 2026-11-08 V530 bounded thumb review and remote processing

Restored V528 via live MCP. V530 three native hinge-axis thumb trial saved and viewed: root spike avoided, but endpoint error22.25mm and no convincing pinch; not promoted. V528 live pose restored, main1957drivers preserved. GitHub private backup and bounded Actions CPU processing being prepared; Modal unavailable. User allows occasional modest Kaggle GPU compute, no broad batches.

## 2026-11-08 local-only resumption

User states Modal is no longer available. Use local Blender MCP and bounded sequential Workbench previews; no Modal jobs. Live bridge responded with V405 loaded, no render active,1957drivers,no V529 objects. V529 interrupted process handle is gone; only partial images/JSON exist, no full scene save. Viewed instrument image: thumb develops a severe root spike; reject unconstrained nine-axis endpoint solve. Restoring saved V528 trial to continue from its intact donor hand and cuff correction. Next thumb fit must constrain hinge axes and inspect skin deformation, not optimize endpoint distance alone. V514 remains preserved original; V528 is a trial, not final accepted anatomy.

## V525–V528 donor reach and cuff trials (2026-11-04)

V525 reflects the source left donor palm depth for right handedness and uses .205m world open wrist-to-middle-tip length (rest scale .82535). Full character view exposed mismatch with older oversized fretting hand, and donor forearm protruding behind cuff. Diagnostic verifies donor wrist anchor matches main DEF-Hand.R within 0.00000064m: attachment transform itself is correct. Native MCP positions are much closer to wrist than old scaffold, requiring arm reach correction rather than doubling hand size.

V526 rejected: pick object origin is remote from its geometry; using matrix_world.translation sends arm away. V527 uses evaluated pick vertex world centroid, translates IK-Hand.R while preserving pick world matrix. V528 trims donor proximal extension at source wrist minus .012m along native palm axis using bmesh bisect (only trial mesh), and four bounded reach corrections. Reviewed instrument and whole-character renders: forearm protrusion largely removed and hand reaches pick region. Still NOT accepted: fingertip bone tail remains about10.6mm from pick centroid; thumb is native open, contact not solved, cuff still irregular, hand sizes unequal, no full collision or animation validation. Need fit actual finger PAD and lateral thumb surface to opposite pick faces, not bone endpoint to centroid. Do not claim correct pinch. Consider bilateral native anatomical replacement rather than enlarging right donor to match old left.

Separate full scene trial: production_v528_native_integration/Character_An_native_hand_integration_TRIAL_v528.blend. Latest images instrument.png and character.png there. Main1957drivers and donor12 retained. Scripts compile and MCP succeeded. All trials restore original IK matrix, pick world matrix, old hand visibility, remove donor objects; V514 remains live/source. Native donor foundation V522 remains intact. Goal incomplete across hands, face/hair, guitar, reference fidelity and animation.

## V523–V524 native rig integration trial (2026-11-04)

Created separate full scene trial production_v524_native_integration/Character_An_native_hand_integration_TRIAL_v524.blend. Native mesh and skeleton share a uniform similarity transform (rest scale1.6019364) mapping wrist/middle and index-pinky palm frames, rig bone-parented to existing DEF-Hand.R, mesh child of donor rig. Twelve donor axis-angle flex drivers read existing FK rotation_euler.x. Thumb remains native open. Main1957drivers retained, donor12. Original hand hidden only inside trial copy; original V514 live restored with trial objects removed. V523 renders incorrectly framed because temporary scene matrix was not evaluated before bbox calculation; V524 updates temporary scene before calculating points, fixes framing. Viewed V524 across_b: thickness retained but oversized-looking palm/forearm and thumb not fitted. CRITICAL next check: source Antonia uses .L donor but target is .R; proper-rotation frame fit may map dorsal to palmar (across_b appears dorsal). Resolve chirality with consistent reflection of mesh+skeleton rather than merely rotating hand. Then inspect in whole-character/guitar view and set scale against references; current scale derived from old palm may perpetuate broad-palm error. Do not promote trial. Both scripts compile/MCP completed. No grip/clearance/animation acceptance yet. Goal incomplete.

## V522 native donor deformation foundation saved (2026-11-04)

Built separate 16-bone donor deform rig at exact Antonia metarig head/tail/roll positions, retaining unwarped source mesh and normalized native sparse weights. Rendered open, positive curl, and negative curl from both palm-plane sides through live MCP. Viewed open_1, curl_positive_-1, curl_negative_1: native positive curl preserves thickness/palm shape substantially better than V520/V521 landmark warp; negative bends backward and is diagnostic only. Nonthumb joint angles40/65/30 degrees around local transformed normal.cross(bone direction). Thumb remains native open and untested. Saved standalone production_v522_native_donor/Antonia_native_hand_rig_v522.blend in neutral pose with armature modifier and native weights; source attribution retained. Six renders and review.json; all three poses finite;1957 main rig drivers preserved. Source joint data production_v520_donor_fit/source_bones.json. Script pipeline/trial_v522_native_donor_rig.py syntax checked and executed successfully. Original character scene restored and untouched V514. Next align donor mesh AND its skeleton together using a uniform similarity transform to character wrist/palm, preserving native lengths/thickness; then drive donor joints through existing controls with axis conversion, fit thumb/index to pick, attach wrist, compare whole-character scale. Native pose quality is a foundation, NOT final reference anatomy or integrated grip. Goal incomplete.

## V520–V521 donor fitting rejected (2026-11-04)

V520 fitted Antonia donor to existing digit joint scaffold through 22-landmark polyharmonic interpolation and transferred normalized native weights. Dorsal review showed excessive wrist flare and broad palm. V521 derives depth from actual source/target palm planes, adds paired depth landmarks and proximal wrist constraints. Live MCP rendered open and playing dorsal/palmar views and saved isolated Antonia_fitted_hand_v521.blend. Viewed open dorsal and playing palmar: wrist flare reduced, but curled geometry severely flattened with broad smooth palm and thin finger sections. NOT accepted replacement; no character promotion. Original scene, twelve FK matrices and original hand restored; 1957 drivers reported. V514 remains authoritative. V521 script compiled before execution. Next preserve donor native joint layout and thickness with similarity alignment and separate donor deformation skeleton driven by current controls; do not repeat fitting donor anatomy into old joint landmarks. Need explicitly compare source rest axes and driven bone rotations before animation. Full character remains incomplete.

## V519 alternative anatomical hand staged (2026-11-04)

Compared local CharMorph Antonia and MB-Lab male hand crops through live MCP Workbench renders. MB-Lab broadside has pronounced artificial ring-like joints; Antonia has cleaner tapered fingers/thumb web but still needs reference-specific joint definition. Selected Antonia as donor for substantive replacement trial, NOT accepted final hand. Staged separate production_v519_source_anatomy/Antonia_hand_donor_v519.blend (3376 vertices,3361 faces), preserved UVs and source polygon material indices in mesh/map, original vertex IDs in antonia_vertex_map.json for native weights transfer. Source config credits Olaf Delgado-Friedrichs et al, CC-BY3.0; attribution embedded. Donor is positive-X source hand cropped x>.57, open wrist boundary; source-space orientation retained. Next fit donor and native joint/weight data to existing right rig, then compare open/curled anatomy and guitar contacts before any promotion. Current character untouched V514;1957drivers. Four initial comparison images plus mb_male_dorsal/palmar reviewed; latter report overwrote initial review.json but images retained. Pipeline scripts syntax passed. Full character goal remains incomplete.

## V518 whole finger section trial rejected (2026-11-04)

Live MCP modified318 right-hand base vertices with dorsal soft-square sections,10percent side taper,12percent dorsal depth reduction, blended root/tip transitions, nail exclusion and2mm displacement cap. Reviewed open/curled dorsal and curled palmar renders: smooth tubular silhouette remains; insufficient improvement. Original coordinates and12FK matrices restored;1957drivers retained. No blend saved;V514 authoritative. Script syntax valid. Evidence production_v518_finger_sections. Procedural radial/crease micro-adjustments have exhausted useful returns: next use substantive reference sculpt or a better anatomical source mesh fitted to existing rig, not another minor profile trial. Preserve current rig/driver data and compare both open and curled deformation before promoting replacement. Overall character remains incomplete.

## V517 dorsal joint support rejected (2026-11-04)

Live MCP confirmed V514 with Armature then Multires (viewport2,total3), no existing crease_edge. Applied temporary 0.55 edge crease to 33 dorsal PIP/DIP ring edges across four right fingers, rendered playing/open views, and restored attribute absence and original12 FK matrices;1957drivers retained. Viewed dorsal open/curl: rounded finger segments persist and open knuckles become bumps rather than reference planes. Direct effect check shows maximum evaluated change3.611mm across13194vertices, so this is not an ignored modifier attribute. REJECTED; no new blend. Script syntax passed. Evidence production_v517_joint_support including changes/restored/effect JSON. V514 stays authoritative. Next substantive geometry work must reshape phalangeal cross-sections and joint transitions as an anatomical whole; stop isolated creases, local bumps, and pose-only trials. Character goal remains incomplete.

## V515–V516 hand trials rejected (2026-11-04)

V515 inner joint crease trial was visually insufficient; coordinates/pose restored with 1957 drivers. Numeric flex probe resolves inside surface as predominantly positive mesh-local Y. No blend saved. V516 live MCP compared coordinated Middle/Ring/Pinky flex distributions: distributed (25/65/45,30/70/45,35/75/45) remains string-clear at sampled +0.577552mm but visually tubular/stubby; relaxed (20/45/30,25/50/35,30/55/40) exposes more finger length but crosses S4/S5 (margin -0.651462mm). Viewed both palmar renders. Original nine matrices restored in finally; 1957 drivers retained. Both scripts syntax parsed. V514 remains authoritative. Do not repeat pose-only curl or tiny joint crease experiments: next repair must address mesh joint anatomy/topology using the supplied hand reference, then test open and curled deformation plus actual guitar contact. Whole character remains incomplete.

## V514 bilateral linear skinning candidate saved (2026-11-04)

Previous goal turn was assessment only. Compared right preserve-volume and linear deformation in actual playing and rigged open poses via live MCP. Viewed paired dorsal/palmar playing images and linear open: linear reduces sharp thumb-web fold; soft finger anatomy persists. Saved separately as production_v514_right_skinning/Character_An_bilateral_linear_skinning_v514.blend, now live/authoritative candidate; V508 preserved. Right Armature preserve-volume now false (left already false), no coordinates/weights/pose/driver edits. Check:13194 finite evaluated vertices,1957drivers,no string centreline crossings,sampled clearance+0.577552mm. Scripts syntax passed. This is a deformation improvement, NOT accepted anatomy/pinch or full animation validation. Read-only joint agent found one8vertex mixed ring at Middle PIP/DIP, so diffuse weights not supported; suggested pose-driven inner-fold corrective. Its radial.y<0 palmar convention conflicts with prior geometry scripts calling that dorsal: resolve using visible surface before implementing any sign-dependent corrective. Next substantive work remains reference joint shape and coordinated picking grip; full face/hair/guitar/fretting/animation scope incomplete. Do not repeat global length or palm-depth trials.

## V513 rigged length comparison rejected (2026-11-04)

Rig-active open comparison is a material correction to V512 interpretation: existing FK1Y1.25 already yields long fingers; armature-disabled images omit that scaling. Tested FK1Y1.4 on four right digits, rendered baseline open/trial open/trial playing. Viewed all three: additional length stretches open digits without fixing smooth tubular curl. Original12matrices restored;1957drivers; no blend saved. V508 remains authoritative. Do not pursue palm shortening solely from V512 rest image. Fresh current_mesh.json exports current base coordinates/weights/faces. Next inspect joint-local deformation, not overall size.

## V512 palm-depth comparison rejected (2026-11-04)

Live MCP tested 25 percent central metacarpal depth reduction with sine blend to unchanged wrist/MCP and thumb exclusion. Rendered baseline rest, trial rest, and trial curl; inspected rest dorsal pair and curl palmar. Flattening barely changes the disproportionate palm-to-visible-finger silhouette and does not resolve joint definition. REJECTED; original coordinates restored exactly, 1957 drivers retained, no blend saved. V508 authoritative. Evidence production_v512_palm_depth; script syntax passed. Next address longitudinal palm/finger-root proportions with corresponding rig placement, not further depth-only or shaft-thinning trials. Rest render has armature disabled (so FK length scaling is absent): compare in a neutral rigged pose before choosing final proportional correction. Full project remains incomplete.

## V511 lateral pick trials reviewed (2026-11-04)

Tested Index X45/55/8 with root Z +/-10 degrees and expanded rigid pick seating. Full-frame trial found two sampled mesh-clear placements, but selected pick remains separated from thumb by 1.596mm and index by 0.592mm; S1 still crosses, clearance margin -1.116278mm. Viewed full-frame side and palmar images: broad smooth palm, crowded rounded fingers and poor pinch remain. REJECTED as finished grip; do not promote clearance-only seating. Scripts restored original pose/pick; restored.json reports true and 1957 drivers. No blend saved, V508 remains authoritative. Evidence production_v511_full_pick_frame and sibling V511 directories. Next substantive work is palm/finger anatomy and coordinated thumb/index pinch, followed by string clearance; global enlargement is not a demonstrated solution.

## V510 isolated index-support comparison (2026-11-04)

Live MCP rendered baseline hand plus pick dorsal/palmar/side in production_v510_grip_review. Tested Index X45/55/8 degrees (root/PIP/DIP), retaining Y/Z, via pipeline/trial_v510_index_support.py. Rendered and viewed side/palmar in production_v510_index_support: less PIP hook but index crowds middle and pick remains obscured; not an accepted grip. Script finally restored original three matrices; MCP status ok and1957drivers retained. No blend saved; V508 authoritative. Syntax passed. Previous goal turn was visual diagnosis only; this turn completed reversible comparison. Independent read-only route identifies actual lateral pair Thumb3 vertex36 and nearest Index3 surface from V503, ~2.412mm gap; V504 vertex2036 was20.6mm away and wrong target. New trial nearest pair shifts toThumb3 vertex975 gap1.974mm, so do not reuse stale coordinates. Next fit pick as rigid bridge between lateral index and thumb surfaces using root spread/opposition, not fingertip coincidence or independent wrist sweep. Full anatomy, fretting, face/hair/guitar and animation scope unfinished.

## V509 loose picking pose rejected; V508 restored (2026-11-04)

Compared hand reference, V500 open hand, live V508. Trial Middle22/38/18 Ring28/42/20 Pinky34/46/22 makes length more visible but crosses S5 and negative clearance at S3. Finite-difference4mm guitar-normal adjustment Ring/Middle still crosses S5.25-case middle MCP/PIP sweep found4 sampled string-clear poses; nearest delta(-20,-10) yields +0.577525mm margin but viewed clear.png shows dangling middle finger inconsistent with reference. REJECTED, exact original9 FK matrices restored and checked (<1e-5),1957drivers intact. NoV509blend saved. V508 remains authoritative. Evidence in production_v509_loose_pick_pose. Stop independent three-finger loosening and clearance-only pose optimization: whole hand orientation and thumb/index/pick pinch need coordinated reference fit; surface polish/global size changes do not resolve anatomy. Full character scope remains unfinished.

## V508 hand surface candidate saved (2026-11-04)

Saved production_v508_hand_surface/Character_An_hand_surface_candidate_v508.blend via live MCP. Copied hand materials, added restrained fine furrows/pigment variation and irregular fold coordinates. No geometry, pose or rig changes. Viewed instrument.png (800x700, Cycles64): modest surface improvement only; broad palm and soft rounded curled fingers still read poorly. NOT an anatomy or playing-grip acceptance. Both evaluated hands finite;1957drivers preserved. V507 remains separate. Next priority substantive reference palm/finger/knuckle proportions and actual thumb/index/pick contact, not more surface polish or global hand enlargement. Full character scope remains unfinished.

## V507 curl clearance candidate saved (2026-11-04)

Saved production_v507_curl_clearance/Character_An_curl_clearance_candidate_v507.blend via live MCP; 1957 drivers preserved. V506 middle fingertip violated lowest-string clearance. Adjusted only right Middle three FK flex angles to 38.975063/62.514934/26.545396 degrees. Evaluated mesh finite, no string centreline crossings, sampled clearance +0.577525mm including buffer. Rendered and viewed instrument.png: proximal curl retained; broad palm, soft joints and thumb/index/pick fit remain visibly unfinished. This is NOT accepted grip, anatomy, self-collision or animation validation. Original pose and fit/check/status JSON in output directory. Next address reference hand anatomy and actual pick pinch/contact; do not repeat global enlargement or wrist-only contact sweeps. Left fretting, face/hair, guitar and animation requirements remain unfinished.

## V506 proximal picking curl candidate (2026-11-04)

Previous turn yielded useful rejection evidence: V505 webs do not solve stubby hands; exact V501 geometry restored. This turn inspected rest mesh and hand reference. Moved curl from distal hooks toward MCP: Middle40/60/25, Ring45/60/25, Pinky50/60/25 degrees MCP/PIP/DIP. Original9 FK matrices in production_v506_proximal_curl/original_pose.json. Viewed dorsal/palmar isolated images and instrument.png. Retained as working pose direction, NOT an accepted playing grip or anatomy result. String check: no centreline crossings but sampled clearance -1.07404mm (includes0.25mm buffer), so collision margin fails. Bilateral finite mesh check and1957drivers at save. Separate Character_An_proximal_curl_candidate_v506.blend; status.json records save. No mesh/weight/driver edits. Knuckles and skin remain too soft; thumb/index/pick unresolved. Next correct coordinated grip/contact using new proximal curl, without reverting to string-safe but hooked distal pose. Left fretting and full face/hair/guitar/animation scope remain unfinished. Scripts compile.

## V503-V505 trials rejected; live V501 restored (2026-11-04)

V503 pick seating sweep found mesh-clear positions but no passing anchored wrist/string placement. V504 distal pad fitting (Index3 vertex2036 instead of near-joint7664), then surface-normal and joint thumb/index fits failed to produce a usable pinch. restore_v504_pinch.py restored original index/thumb matrices and true V501 pick world matrix from V503/frame.json. V505 recessed bilateral interdigit web valleys (96 vertices each, maximum4.986mm); rest and curled reviews still show broad palm and stubby, rounded anatomy. Rejected after palmar review. restore_v505_web_recess.py restored exact original mesh coordinates on both hands; MCP returned success and1957 drivers confirmed. No new blend saved. V501 remains an imperfect candidate, not an accepted grip. Scripts syntax checked. Stop treating incremental web bumps or point-contact convergence as resolution of hand proportions. Reference-quality anatomy, picking contact, left fretting, face/hair, and animation remain unresolved.

## V502 picking contact trial rejected (2026-11-04)

Previous turn assessment only. Confirmed pick tip vertices0/1/48 embedded0.8–1.64mm in Middle3. Swept27 middle curls; smallest change MCP0/PIP65/DIP50 gives1.474mm signed tip clearance. Repeated121 anchored-pick wrist rotations (X/Y±50degrees) targeting actual S4 spline: zero passing string-clearance cases. Rendered and viewed middle_trial.png: middle opens but still hooked/rounded and grip not convincing. Restored three middle FK matrices from middle_original.json;1957drivers confirmed. No new blend saved, liveV501. Scripts trial_v502_middle_clearance.py and trial_v502_pick_contact.py syntax checked. Do not repeat wrist-only sweep or equate pick-tip clearance with usable grip. Next reposition pick within thumb/index pinch together with digit pose; existing pick placement itself intersects hand. Hand silhouette still needs anatomical correction, full face/hair/guitar/fretting scope remains.

## V501 picking surface refit candidate (2026-11-04)

Previous goal turn was preview assessment only. Connected live V500. Endpoint-only right Index5DOF refit failed clearance. Surface-fit restores evaluated Index3 pad vertex7664 to prior short-index location (Thumb3 vertex5953 nearest), preserves distal direction, keeps firstFK Y1.25. Deltas rootX-9.83184deg, PIP+30.09468,DIP-20.26349; pad residual0.000285mm. Still strings1,3 crossed. Swept33 wrist poses about guitar-local(.635,-.020,.051), Yrotation±25deg andZlift0/2/4mm; only-25deg/+4mm cleared with>0.3mm. Final half-mm sampling clearance0.577553mm,nocentrelinecrossings,13194finiteverts,1957drivers. IMPORTANT: pick is bone-parented to IK-Hand.R; update wrist depsgraph BEFORE assigning transformed pick world matrix, otherwise stale parent doubles movement. Corrected in fix_v501_pick_parent.py and trial_v501_wrist.py. Corrected pick guitarlocalZ .036089..066321; Actual S4 target at this X is Z.028369 including radius and0.1mm gap; tip needs7.72mm drop plus8.008mm lateral shift. Earlier15.64mm used an incorrect constant string height. Thumb-index nearest signedgap2.411mm. NOT accepted playing grip. Surface target recovers inherited imperfect pinch; further work must explicitly fit pick surfaces/playing contact while preserving whole-hand collision clearance. Do not declare clearance alone success. Scripts in pipeline/trial_v501_{bone_fit,surface_fit,wrist}.py and fix/save_v501_pick_refit.py. Backup original_pose.json and wrist_pick_original.json in production_v501_pick_refit. Candidate save/status and corrected.png identify latest result. V500/V497 preserved. Full anatomy, fretting, face/hair/guitar/animation requirements remain unfinished.

## V500 finger proportion WIP saved (2026-11-04)

Previous turn rejected V499 and restored V497. Live rig query established proximal FK Y scale inherits uniformly through ALIGNED children: V484 proximal1.12 had lengthened all three segments12percent, not just proximal. V500 sets ONLY first FK finger Y to1.25 for bilateral Index/Middle/Ring/Pinky; children unchanged. Thus most fingers increase11.6percent fromV497, RIndex25percent. Backup48matrix_basis in production_v500_finger_proportions/original_pose.json. Viewed open and playing right dorsal Workbench images; open fingers read longer, curled anatomy remains soft. Saved separate Character_An_proportion_candidate_v500.blend; V497 preserved. Mesh coordinates,weights,drivers unchanged. Both meshes finite;1957drivers. IMPORTANT WIP CONTACT REGRESSION: picking hand crosses string centrelines2,3; sampled clearance-1.05675mm. This is NOT accepted grip. Next fix actual right thumb/index pinch and wrist placement to new proportions, retain curl and test instrument contact; left fret positions still unresolved. Do not treat saved candidate as finished or revert solely to pass old contact at cost of proportions. Scripts trial_v500_finger_proportions.py/save_v500_candidate.py. Full face/hair/guitar/animation scope remains.

## V499 joint plane trial rejected (2026-11-04)

Previous turn answered user tiny-hands question without asset progress. Inspected actual middle finger edge-ring coordinates. Trial flattened dorsal joint crowns of four digits bilaterally (52 vertices each, max1.463mm), preserving nails, weights, pose and drivers. Rendered and viewed true rest and playing dorsal views in production_v499_finger_contours. No meaningful resolution of short/soft silhouette. Rejected; restore_v499_joint_planes.py restores exact V497 coordinates. No new blend saved. Stop repeating localized knuckle adjustments: next substantive trial must coordinate finger-to-palm proportions and rig lengths, preserving endpoint contact through pose correction. V484 all-segment scale compounded and was rejected; do not repeat that method. Full reference, face/hair/guitar/fretting and animation scope remains unfinished.

## V498 knuckle shoulder trial REJECTED (2026-11-04)

Previous turn saved V497 shaft taper. Trial added localized dorsal shoulder lobes around Index/Middle/Ring/Pinky joints:1.2mm amplitude,6mm axial Gaussian, lateral peaks±4.5mm,width3mm,weight blend.110verts each,max1.121mm. Rest and curled right dorsal renders viewed: insufficient visible improvement in joint silhouette. REJECTED; restore_v498_knuckle_shoulders.py restored exact bilateral coordinates from production_v498_knuckle_shoulders/original_coordinates.json; MCP confirmed1957drivers. No new blend saved; live/savedV497. Images and trial script retained. Next correction must shape joint cross sections/edge rings directly rather than repeating small Gaussian bumps or shaft narrowing. Hand anatomy, left fretting and full character likeness remain unfinished.

## V497 finger shaft contour candidate (2026-11-04)

Previous turn established rest-shape defect. Narrowed Index/Middle/Ring/Pinky proximal and intermediate shaft X radial width13percent and dorsal Y5percent with sin² longitudinal falloff weighted by existing groups. Endpoints, distal segments, nails, thumb, topology, weights, rig and pose unchanged.225baseverts per hand,max1.365mm. Backup production_v497_finger_contours/original_coordinates.json. Viewed rest/across_a and playing/across_a: modestly more distinct shaft taper; knuckles still too soft. Saved separately as Character_An_finger_contours_v497.blend after bilateral finite evaluation and picking string clearance check.1957drivers preserved. V495 preserved. Scripts trial_v497_finger_contours.py/save_v497_finger_contours.py syntax passed. This is a small geometry refinement, not resolved hand anatomy or animation readiness; left contacts and face/hair/guitar remain incomplete. Next: substantive reference knuckle and web shaping; do not repeatedly narrow shafts further without a reference comparison.

## V496 true rest-shape review (2026-11-04)

Previous turn saved V495 left linear skinning candidate. Temporarily disabled RIGHT Armature viewport/render visibility and rendered evaluated rest mesh through Multires from local dorsal/palmar directions; finally restored original modifier visibility. No geometry, pose, weights or file changes. MCP status ok,1957drivers asserted. Viewed references/hands/hand_pose_sheet_v1.png and production_v496_rest_shape/across_a.png: fingers have rounded near-uniform contours and indistinct knuckles already in rest mesh; defect is not solely pose/skinning. Hand render includes forearm stump and is upside down; do not mistake stump length for palm length. Saved V495 remains authoritative. Script pipeline/review_v496_rest_shape.py syntax passed. Next actual correction should target reference knuckle/shaft/web geometry with rest and curled comparisons, not further global enlargement or repeated modifier diagnostics. No claim of animation readiness.

## V495 left linear skinning candidate saved (2026-11-04)

Previous turn was assessment only. Compared left preserve-volume versus linear skinning with the V494 Armature-before-Multires stack in playing, open and curl poses. Viewed paired open/curl palmar-oblique images: linear reduces palm bulge without obvious additional collapse at that angle. Retained left-only linear skinning as separate production_v495_left_volume/Character_An_left_linear_skinning_v495.blend; V494 preserved, right preserve-volume unchanged. Pose restored, no mesh/weight edits. Four open/curl cases finite13194vertices;1957drivers intact. Scripts review_v495_volume_poses.py and save_v495_left_volume.py syntax checked. This is a candidate, not anatomical or animation-wide acceptance. Palm remains broad/flat and joints overly soft; fretting contacts unresolved. Next substantive work: compare base/rest hand silhouette to supplied hand reference, correct palm/finger geometry rather than further global size changes. Face/hair/guitar and animation remain incomplete.

## V494 bilateral deformation order saved (2026-11-04)

Previous turn saved right-hand deformation improvement. Tested left hand with Armature before Multires versus original in playing/open poses; four cases finite13194vertices,1957drivers. Viewed playing original/trial palm and trial dorsal plus open trial palm/original dorsal. Original has severe folded palm ridge; trial substantially reduces ridges but retains unnatural palm bulge and soft anatomy. Retained bilateral modifier order in separate live/saved production_v494_left_deform/Character_An_bilateral_deform_order_v494.blend. V493 preserved. No pose, base geometry or weight edits. Both evaluated meshes finite13194;1957drivers confirmed at save. Temporary review scenes removed. Scripts trial_v494_left_deform.py and save_v494_left_deform.py syntax passed. Fretting contact remains wrong; no animation-wide acceptance. Next: investigate left palm bulge against neutral/rest shape and Hand-versus-finger weights; this remains an actual deformation defect, not a material problem. Full character likeness and guitar work remain in scope.

## V493 right-hand deformation order saved (2026-11-04)

Previous turn progressed via isolated views identifying thumb web pinching. Tested Armature BEFORE Multires on right hand, compared same curled palmar/dorsal views plus open palm against original order. Visibly reduced thumb-web pinch and softened collapsed inner curl transitions; retained as separate candidate. Live/saved production_v493_deform_order/Character_An_hand_deform_order_v493.blend. Original V491 preserved. Right hand only; no mesh/weight/pose edits. Saved direct check: 13194 finite vertices,1957 drivers, no string centreline crossings,0.719850mm sampled clearance. Scripts trial_v493_deform_order.py, review_v493_open.py, save_v493_deform_order.py syntax passed. Temporary review scenes removed and original character scene restored. Images across_a/b.png, open_original/across_b.png and open_trial/across_b.png inspected. Remaining anatomy overly smooth/rounded; left hand order unchanged and fret placement unresolved. Next compare left hand deformation with this order before bilateral adoption; then substantive shape/skin work and face/hair likeness. No self-collision or animation-wide acceptance.

## V492 isolated evaluated hand review (2026-11-04)

Previous turn was assessment only. Connected to live V491 via MCP; no render active. Created disposable scene with evaluated right-hand mesh, rendered four orthographic Workbench views, removed temporary scene/data and restored original character scene. Script pipeline/review_v492_isolated_palm.py; outputs production_v492_palm_review/{side_a,side_b,across_a,across_b}.png and report.json. 1957 drivers preserved; source blend unchanged. Across views expose actual dorsal and palmar surfaces (bone X viewing direction); initial bone Z views were lateral and cropped wrist. Findings: broad flat palm, short-looking proximal finger segments, rounded curl joints, deep thumb web pinch and crowded curled silhouette. No self-intersection proof from images alone. V491 remains a pose candidate, not accepted deformation. Next correction should address joint deformation and palm/finger proportions with these isolated views, not global hand enlargement or string-only acceptance. Include neutral/open comparison before choosing geometry versus skinning changes. No asset geometry changed this review; no new blend saved.

## V491 picking curl candidate (2026-11-04)

Previous turn made progress by full-body visual scale review; no further global enlargement warranted. This turn identified saved V490 Ring3 near S7 (0.087mm surface-to-centreline), then swept24 FK curl combinations for Middle/Ring/Pinky, holding thumb/index and wrist fixed.21 met no centreline crossings and >0.3mm sampled clearance. Selected MCP10/14/18degrees, PIP65,DIP50. Live recheck finite13194vertices, minimum clearance0.4699346mm,1957drivers. trial.png rendered and inspected against hand_pose_sheet_v1.png: curl silhouette closer to reference but rounded knuckles/pinched webs remain. Save script produces separate production_v491_pick_curl/Character_An_pick_curl_candidate_v491.blend, retaining V490. Check status.json for completed save. original_pose.json restores9FKmatrices; no mesh/weight/material changes. No palm-side visual or self-collision acceptance. Left fretting/face/hair still unresolved. Next substantive work: anatomical joint/web deformation and palm-side review, then full-body pose comparison; do not repeat uniform scaling. Scripts syntax checked; directory is not a git repository.

## V490 full-body scale review (2026-11-04)

Rendered and visually inspected production_v490_hand_anatomy/full.png (900x1200,24samples) against references/source/approved_character_design_lock.png. Current hands do not appear globally tiny relative to head/body; avoid another uniform scale increase. Picking hand is excessively open/flat compared with curled reference grip; both hands remain smooth and lack convincing mature joint structure. Left fretting contact unresolved. This evidence changes next action from global sizing to actual pose/anatomy/contact correction. Saved V490 unchanged; current camera is full-body. Render terminal confirmed via live bpy job status.1957drivers checked by render helper. Previous isolated hair experiment was restored to V371_DARK_HAIR_UNDERLAY and V449 groom visible; no hair candidate saved. V487 isolated image exists but has not been accepted. Project remains far from completion. Next: reference picking curl with thumb/index contact maintained, resolve clearance by coordinated wrist/pick placement rather than accepting string penetration; preserve originals and inspect full silhouette and close anatomy.

## V490 anatomical geometry candidate saved (2026-11-04)

Previous goal turn made negative progress: V489 web-weight diffusion was rendered and rejected; exact weights restored. This turn changed geometry on BOTH hands: tapered ulnar midpalm by up to3.831mm, flattened central dorsal PIP/DIP crowns and reduced excess palmar phalange depth. Preserved thumb/index, nails, weights, topology and1957drivers. Changed331vertices per hand. Viewed right curl.png and open.png: modestly slimmer palm, continuous open silhouette; still overly soft joints and poor mature-skin detail. Retained as a separate candidate, not accepted reference quality. Curl stress pose still has -.793mm sampled string clearance, no centreline crossings. Restored original playing matrices before saving. Both evaluated hands13194finitevertices. Live/saved production_v490_hand_anatomy/Character_An_hand_anatomy_candidate_v490.blend; accepted V483 and previous V484 preserved. No render running at save. Scripts trial_v490_hand_anatomy.py, review_v490_open.py, finish_v490_candidate.py syntax checked. original_coordinates.json backs up both base meshes for reversal. Original pose backup in this output is the curl stress pose; restore_v488_pick_curl.py is also required to restore the true playing pose after check_v472 restore.

Next: retain full reference scope. Hands still need convincing bony knuckles, skin/nail material detail, bilateral visual review, full-body scale assessment and corrected fret contact. Do not claim the small-hand issue solved by this modest palm correction. Face likeness and hair remain far from reference; V487 underlay repair remains pending. Do not mark project complete.

## V489 local cross-digit web weight trial rejected (2026-11-04)

Found abrupt dominant Middle/Ring/Pinky changes across 24 web vertices. Trial diffused weights over 52 vertices (three iterations; seed blend .45, neighbor .15; nails excluded), preserving mesh and thumb/index. Rendered same V488 relaxed curl camera: modest web smoothing, no meaningful resolution of rounded knuckles, broad palm or undersized appearance. Clearance remains -0.806mm with no string centreline crossings; 1957 drivers. Viewed before and trial. Rejected rather than promoting a marginal change. Restored exact original weights and nine playing-pose matrices using restore_v489_web_weights.py. No blend saved. Outputs production_v489_web_weights. Next: actual anatomical geometry/proportion correction; cross-digit web smoothing alone is insufficient. Live V484 candidate, accepted V483 unchanged.

## V488 picking curl trials rejected (2026-11-04)

Previous goal turn was assessment only. This turn compared hand_pose_sheet_v1.png and tested reference-like M/R/P curl, leaving thumb/index pick controls fixed. trial.png crosses string centrelines S1/S2; sampled clearance -1.127mm. relaxed.png reduces proximal flexion to8/12/16degrees while retaining PIP62/70/75 and DIP38/42/45: no centreline crossings, but clearance -0.806mm including string radius and .25mm sampling allowance. Both renders viewed; relaxed curl exposes rounded joint cross-sections and pinched webs. Neither accepted. Restored all9 controls from original_pose.json, maximum matrix error5.96e-8;1957drivers. No new blend saved, live remainsV484candidate. Scripts trial_v488_reference_pick_curl.py, trial_v488_relaxed_knuckles.py, restore_v488_pick_curl.py. Output production_v488_reference_pick_curl.

Next hand work needs actual anatomical mesh/joint-web correction; repeated pose-only or global-size changes have not resolved the user complaint. Curl tests provide a useful failure pose for judging that correction. V487 underlay script remains unfinished: failed on missing Weight socket in fresh Principled node before material assignment; original underlay/groom untouched. Do not infer new material was applied.

## V485/V486 hair isolation and curl trials rejected (2026-11-04)

Prior turn completed V484 pose review (progress). Current turn rendered hair underlay separately: production_v485_hair_isolation/underlay.png proves visible ribbon shapes originate in groom, while underlay is glossy and lumpy. V485 root-fixed cluster taper and length diversity had insufficient visible effect. V486 regenerated same925guides/85100strands with axial9–16mm instead of20–28mm, turns.85–1.35, closer sides and tapered clusters. Viewed trial.png: spiky clustered silhouette, still artificial; REJECTED. No new blend saved. Both temporary groom objects/data removed by restore_v486_hair_trials.py; V449 visibility restored,1957drivers intact, no running render. Live/saved remains V484 candidate; accepted V483 unchanged.

Next hair work must redesign guide grouping and scalp flow against reference, rather than another uniform clump-length/taper adjustment. Underlay material/geometry also requires correction; isolated render documents it. Hand joint/web anatomy and fretting remain unresolved. References/source/approved_character_design_lock.png re-viewed in this turn; current face remains broad with incorrect eyes and insufficient likeness. Scripts/trial images retained for reproducibility, not production acceptance.

## V484 deformation review completed (2026-11-04)

Viewed open.png and curl.png after candidate proximal length change. Open silhouette is longer; curled pose still has broad rounded knuckles and pinched webs. Review camera shows RIGHT hand only; both hands passed finite-coordinate checks, which is not bilateral visual acceptance. Restored all 30 finger control matrices from review_playing_pose.json; 1957 drivers intact. Live playing pose restored, no render running. Saved candidate remains separate; accepted checkpoint remains V483. Do not promote: asymmetric index proportions, left fretting contacts and joint anatomy unresolved. Next substantive correction should address anatomical joint/web shape and both-hand proportions against references, not another uniform size change.

## V484 — finger length candidate, pending deformation review (2026-11-04)

Live/saved candidate `production_v484_finger_length/Character_An_finger_length_candidate_v484.blend`; accepted checkpoint remains V483. Proximal FK scale.y multiplied1.12 for left Index/Middle/Ring/Pinky and right Middle/Ring/Pinky; right thumb/index unchanged to preserve pick grip. Descendants inherit length increase. No mesh edits.1957drivers; both evaluated hands13194vertices finite. Viewed corrected.png and before.png same close camera: longer slender silhouette, still poor anatomy/contact. This is NOT approved reference anatomy or animation readiness.

Initial trial scaled all three joints and compounded12/25/40percent; rejected/restored. full.png shows rejected trial. original_pose.json backs up21controls. corrected.png shows proximal-only version retained as candidate. save_v484_candidate.py reapplies from backup safely but refuses overwrite. Next inspect OPEN and CURLED poses while preserving candidate scales and restore playing matrices afterward. Do not reuse check_v472 backup filename directly: V484 original_pose.json lacks right thumb/index; use separate review backup. Resolve asymmetric finger proportion and fret contact before promotion. No heavy job running after save.

## V483 — reversible calmer eye pose (2026-11-04)

Saved/live `production_v483_eye_rest/Character_An_eye_rest_pose_v483.blend`; V482 preserved. Head controls Blink.L/R=.23, previously0. Only pose changed; no meshes or drivers edited.1957drivers intact. Viewed before.png, trial.png and blink.png(full1.0). Partial closure reduces startled expression but does not match reference eye contours. Full blink has no visible exposed eyeballs at rendered angle; not animation acceptance. Saved with.23 restored. Original controls backed up. Scripts inspect/trial/check/finish_v483_*.py.

Reference approved_character_design_lock.png inspected against new close face render. Remaining substantial mismatch: craniofacial proportions, heavier lid shapes, skin quality and ribbon-like hair. Do not mistake partial blink for an anatomical fix. Next needs substantive reference-driven head geometry/groom work, not repeated small expression/shader variants. Fretting and hand web/joint anatomy remain unresolved.

## V482 — partial reversal of artificial joint width (2026-11-04)

Saved/live `production_v482_joint_width/Character_An_joint_width_v482.blend`; V481 preserved. Restored original playing pose, 1957 drivers intact. Script trial_v482_joint_width.py reverses V471 transverse inflation at middle/ring/pinky joint ends with cos(pi*t)^4 falloff; shaft midpoint, depth, nails, thumb/index untouched. 243 vertices per hand, maximum1.780mm. Original coordinates/pose backed up in output directory. Open/curl finite checks passed; viewed open, curl and playing renders. Modest slimmer joint transitions retained; broad dorsal MCP ridge and pinched webs remain. No anatomy, contact, or animation acceptance. Fretting and face/hair remain substantially wrong.

Do not repeat small width or shading variations: these have now demonstrated limited effect. Next substantive work needs mesh joint/web topology or a measured anatomical replacement, and full pose/character likeness. Keep prior user-verified fret assignments unchanged.

## V481 — intermediate hand crease shading retained (2026-11-04)

Saved/live production_v481_hand_joint_detail/Character_An_hand_joint_detail_v481.blend, original playing pose restored,1957drivers intact. V478 retained. Copied hand skin materials only: crease distance.00028m,strength.48, dark overlay factor.06; deterministic joint widths*.78–1.04 and offsets±.5mm. No mesh, rig or contact changes. Scripts refine/review/finish_v481_hand_joint_detail.py. materials.json allows restoring V460 materials; original_pose.json stores current right playing pose.

Viewed open.png (before minor joint variation), curl.png and playing.png. Creases readable in open pose, less apparent curled; retained as modest surface-detail WIP. Curl still has rounded MCP ridges and pinched webs, not anatomy acceptance. Joint shader centers match rest-hand bone data within.00009mm, so absent anatomy is not a misplaced shader. Fretting remains incorrect; face/hair remain far from reference. Next needs substantive geometry/deformation or broader character likeness work, not more tiny shading adjustments.

## V480 — alternative hand visual review (2026-11-04)

V478 remains authoritative, unchanged. Appended local Innerscene hand into separate temporary scene, rendered rest mesh in Workbench clay. See production_v480_hand_source_review/source_rest.png, inventory.json, rig.json. Visible pronounced bulbous joints and pinched capped wrist; this view does not establish a superior replacement. Retain current hand; do not substitute this source based on vertex count alone. Imported review objects/scene removed and character scene restored; restored.json verifies1957drivers. No V480 blend saved. Scripts inspect/render/restore_v480_source_hand.py preserve reproducibility. Next substantive anatomy work should target joint cross-section and web topology, with open/curl inspection, rather than repeated uniform scaling or endpoint-only fretting fits.

## V479 — bounded joint fretting trial rejected (2026-11-04)

Saved/live remains V478; all13trialcontrolmatrices restored via pipeline/restore_v479_fretting_palm.py,1957drivers intact. Joint wrist6DOF plus16fingerparameters,24iterations with sampled9mmseparation penalties. Errors reduced47/26/46/33mm to24/5/20/7mm, but index/ring remain far off; splay reached bounds±.45rad and sampled separation fell6.92mm. Viewed trial.png: bunched/overlapping-looking fingers, worse natural silhouette. NoV479blend saved. Data and original matrices in production_v479_fretting_palm.

This excludes the tested local wrist neighborhood (±.65rad,±45mm), not global feasibility. Cannot infer impossible voicing from this optimizer. Next meaningful fretting investigation needs different palm orientation or verified photograph-driven pose, anatomical mesh collision constraint rather than soft sampled bone penalty. Do not relax finger constraints blindly or silently change user-verified ring/pinky assignments. Hand size correctionV478retained.

## V478 — matched hand scales (2026-11-04)

Saved/live `production_v478_hand_symmetry/Character_An_hand_symmetry_v478.blend`; V477 preserved. Measurement found left wrist/middle chain 163.08mm versus right181.20mm. Left IK scale increased 1.1111105 to match right1.416, preserving middle distal bone tail within0.000134mm. Original control matrix in original_pose.json; script pipeline/trial_v478_hand_symmetry.py. All1957drivers intact. Viewed full.png and close.png: improved left hand size/readability, no obvious wrist break in these views. This is proportion WIP, not anatomical/deformation acceptance.

Fretting still WRONG: bone-tail target errors Index47.37,Middle25.98,Ring46.27,Pinky33.31mm (initial.json); middle hover included. Other fingertips shifted with scale; no contact acceptance. Next tackle shared palm/wrist orientation with collision-aware ordered fingers, not isolated endpoint solver (V469 crossed fingers). Face/hair remain far from reference.

## V477 — slotted bridge housings (2026-11-04)

Saved/live `production_v477_bridge_channels/Character_An_bridge_channels_v477.blend`. Replaced visible solid bridge blocks with separate base, side rails, end and recessed adjusters; original objects hidden reversibly, visibility backup in output directory. V476 tuner barrels and all saddle/string endpoints retained. Viewed bridge.png: clear open channels improve reference resemblance. 1,957 rig drivers retained. Not full guitar acceptance; saddle shape and finish remain simplified. Next return to hand/body proportions with a current full-character render; previous full render predates cuff and finger refinements.

## V476 — reference-shaped bridge tuner barrels (2026-11-04)

Saved/live: `production_v476_guitar_review/Character_An_bridge_tuners_v476.blend`. Retains V475 hands and original playing pose. Eight axial ridged tuner barrels added, old bridge blocks shortened toward saddles; string and saddle endpoints unchanged. Original housing transforms saved in bridge_backup.json. Script: `pipeline/refine_v476_bridge_tuners.py`.

Viewed source `references/props/strandberg/strandberg_full_product.jpg`, new front.png and tuners.png. Front view indicates current traced wood silhouette is broadly consistent with photo; more obvious mismatch was cuboid-only tuner hardware. New barrels improve reference resemblance; housings/saddles still simplified. All 1,957 rig drivers retained. No animation acceptance claimed. Render is CPU four threads. Previous V475 preserved.

## V475 — finger shaft taper retained as WIP (2026-11-04)

Current saved/live file: `production_v475_phalange_profile/Character_An_phalange_profile_v475.blend`. Original playing pose restored before saving. Prior V473 preserved.

Reversible base-coordinate taper of middle/ring/pinky shafts on both hands: 226 vertices each, maximum displacement 2.590057 mm; joint endpoints, nails, thumb/index protected. Script: `pipeline/refine_v475_phalange_profile.py`; backups/report in output directory. Viewed `open.png`, `curl.png`, and `playing.png`. Playing silhouette modestly improved; broad MCP ridge and pinched webs remain unresolved. This is not anatomical or animation acceptance.

Right-hand static check: finite 13,194 evaluated vertices, no crossed string centrelines, sampled clearance 0.4699346 mm; 1,957 CloudRig drivers retained. Full animation and left fretting contact remain unvalidated. Do not repeat diagnostic poses without restoring original_pose.json.

Source review found no validated superior local replacement. Innerscene hand-posable-right.blend is denser but would require provenance, visual and rig-integration assessment; do not replace current rig blindly. Next meaningful anatomy work is joint cross-sections and finger-web edge flow, not more uniform scaling/smoothing.

## V474 local pose corrective rejected — 2026-11-04

Saved/live remains V473, original playing pose restored. Tested three per-finger driven shape keys on each hand: up to3mm dorsal MCP compression, activated by FK flexion20–55degrees. Actual800x70024sample curl render `production_v474_joint_study/curl.png` inspected; broad rounded ridge and tubular fingers persist. Driver values verified .999887 and valid, so this is not an inactive-driver result. Removed only new hand shape keys;1957CloudRig drivers preserved. No production blend saved. Scripts `pipeline/trial_v474_joint_corrective.py`, `pipeline/restore_v474_joint_corrective.py`; restore guard prevents repeat.

Next do not repeat local dorsal compression, global smooth, or blind hand enlargement. Hand base topology/joint cross-sections need substantive anatomical rebuilding or a better riggable source hand; review available source mesh against references before another deformation trial. Full character objective remains incomplete. Previous turn was status only; this trial produces evidence ruling out simple pose-driven dorsal compression.

## V473 right cuff refinement saved — 2026-11-04

Current live/saved `production_v473_right_cuff/Character_An_right_cuff_v473.blend`. V471 retained. Coherent right sleeve/cuff/stitches shrink, final effective factor .049 (initial .14 reduced to 35%); button uses rigid mean translation instead of radial deformation. All joined-body shape keys receive same deltas. Original trial deltas `deltas.json`, reduction `reduced.json`. Scripts `pipeline/trial_v473_right_cuff.py`, `/tmp/bca_v473_reduce.py`; do not rerun on saved V473.

Viewed initial full-body and close-up: initial shrink exposed skin and flattened button, rejected. Viewed final reduced `close.png`: visible skin breakthrough resolved and button shape restored. `full.png` is INITIAL REJECTED larger shrink, not final V473. Need final full render later. No full animation/collision acceptance. Driver count remains1957. V472 curl review still reveals rounded MCP ridges/web pinching; next tackle local joint anatomy/weights (avoid rejected global smoothing/preserve-volume toggles) and unresolved fretting targets.

## V472 open/curl review completed — 2026-11-04

V471 right hand reviewed in `production_v472_hand_deformation/open.png` and `curl.png`. Open silhouette continuous; curl reveals broad knuckle ridges and pinched interdigital valleys. Both finite-mesh checks pass but these are NOT anatomical/deformation acceptance. Original playing pose restored through script; 1,957 drivers intact. Saved file remains V471, unchanged. No V472 blend saved.

Next concrete hand work: inspect MCP topology/weights in curled pose to reduce broad ridges and web pinching; prior global CorrectiveSmooth and preserve-volume toggles were rejected, so do not repeat them. Cuff correction must include joined body material6 and right cuff/stitch/button objects coherently (`refine_v444_sleeve_volume.py` names), not only cuff patch. The user complaint remains unresolved at full-body scale; render full body after anatomy/cuff edit.

## V471 finger-volume WIP saved — 2026-11-04

Current live/saved candidate: `production_v471_finger_volume/Character_An_finger_volume_v471.blend`; V468 retained as prior fallback. Both hands Middle/Ring/Pinky weighted radial X enlarged 18%, dorsal Y 10%; 292 base vertices per hand, maximum 2.094 mm local change. Thumb/index unchanged. Script normalizes right bone group suffix to left rest-data names and restores original coordinates before applying, avoiding accumulation. Backup `production_v471_finger_volume/original_coordinates.json`.

Viewed `close.png`: fuller fingers, modest improvement, still smooth/tubular and cuffs oversized. Right evaluated hand finite, 13,194 vertices, no eight-string centreline intersections, sampled clearance 0.4699 mm; all 1,957 drivers retained. This is WIP, not animation acceptance. Next: open/curl deformation visual check of this change, then cuff proportions and anatomical joint definition. Left hand/chord contact and finger collisions remain unresolved. No full-body render for V471 yet. V470 face trial remains rejected/restored.

## V470 face trial rejected and restored — 2026-11-04

Live V470 face edits were reversed using `production_v470_face_proportions/deltas.json`; restore recorded in `restored.json`. Ear pinching and neck discontinuity were visible. Saved authoritative checkpoint remains V468; all 1957 CloudRig drivers survive. Do not rerun the V470 trial or delta restoration without resetting state.

Latest user feedback: hands look tiny. V468 enlargement is provisional; oversized cuffs and slender fingers still undermine apparent size. Correct anatomy and cuff proportions against references before further global enlargement.

Fretting feasibility review found no axis reversal in v2 mapping. Index S6/F11 versus ring S7/F9 creates crossing pressure; V469 endpoint-only fit was rejected. Next pose solve needs shared wrist/palm plus collision constraints. Preserve user-verified ring/pinky assignments. `hand_contact_solver.py` and `photoreal_contract.py` contain older conflicting targets; do not silently use them as v2 authority.

## V469 fretting target fit rejected for crossed fingers — 2026-11-04

Live/saved production remains V468. Fresh 900x700 close render confirms fretting pose is not chord-accurate. Initial distal bone target errors Index46.436mm, Middle25.982mm, Ring44.478mm, Pinky30.329mm. Per-finger bounded five-axis FK solve reached .029/.730/.127/.003mm respectively, but actual trial.png visibly crosses index/ring fingers and has implausible grip. Rejected; restore_v469_fretting.py restored all12 FK matrix bases with max error below1e-6;1957drivers intact. No V469 blend saved. Trial proves bone endpoint accuracy alone is insufficient and current wrist/finger ordering conflicts with target layout. Next solve wrist orientation plus finger surface/collision constraints; do not accept or rerun endpoint-only fitting unchanged. Mapping remains user-authorized IndexS6F11, MiddleS6F10hover, RingS7F9, PinkyS8F11; do not silently change it. Artifacts production_v469_fretting/{initial,trial,original_pose,rejected_pose}.json, before.png, trial.png. Scripts inspect_v469_fretting.py, trial_v469_fretting.py, restore_v469_fretting.py. Previous turn was status-only/no progress; this turn generated decisive rendered evidence and safely restored the baseline. Character quality and animation objective still unfinished.

## V468 larger hand silhouettes saved — 2026-11-04

Saved/live production_v468_hand_readability/Character_An_hand_readability_v468.blend. Compared reference/full-view proportions and enlarged right IK-Hand1.20, left1.08 relativeV466, preserving averageIndex/Thumb distalboneanchor R andMiddle distalL. Arms/cuffs follow rig. Actual720x96024sample full render shows clearly larger picking hand;900x700close render confirms wrist/cuff continuity in this pose. Initial enlargement nearly touchesS1 indexdistal, so raised rightwrist2.6mm alongguitarZ. Check13194finiteevalverts,no8stringcentrelinecrossings,conservativesampledclearance.46993mm;1957drivers. Thumb/indexsignedgap1.01027mm. Centered0.7mmpick plane throughnewpinch byworldtranslation guitar-local(.000746624,.000114350,.000149512); correctmatrix_world sincepickparentrig. Final fullrender final_full.png. OriginalV466rollback intact, originalcontrolmatrices andpickmatrix saved trialfolder. This is INTERMEDIATE silhouette improvement, NOT final anatomical scale or playing acceptance: asymmetric per-side scale must be normalized for animation/rest anatomy, finger anatomy still tubular, fretting targets and complete guitar/hand collision and pickcontact not validated. Do not call project photoreal or complete. Next improve reference curled picking pose and robust fretting/contact; larger face/hair/guitar defects still outstanding. Scripts trial_v468_hand_readability.py, finish_v468_hand_readability.py (includes additional.6mmlift AFTER /tmp/bca_v468_lift.py2mmlift), save_v468_hand_readability.py. PreviousV467turnprogress ruledoutpalm-onlywidening; thisturnsavedvisibleproportionchange.

## V467 palm silhouette trial rejected — 2026-11-04

Previous turn was status-only, no progress. This turn tested right ulnar palm widening on135vertices, maximum6.955mm local, with wrist/MCP falloff and thumb/index protection. Actual720x96024sample full render production_v467_palm_silhouette/full.png inspected: insufficient visible change to small/stubby hand reading. Rejected and original V466 coordinates restored through MCP;1957drivers retained, no production save. V466 remains authoritative. Do not repeat small palm/tendon changes as the route to full-view proportions. Next use reference/full-render wrist, palm, finger silhouette and cuff relationships to make a substantive pose/cuff correction, preserving pick contact. Scripts trial_v467_palm_silhouette.py and restore_v467_palm_silhouette.py. Full character likeness, hair, guitar and animation remain unfinished.

## V466 dorsal hand anatomy — 2026-11-04

Saved/live production_v466_dorsal_anatomy/Character_An_hand_anatomy_v466.blend. Changed 95 base vertices per hand, max1.903mm local, adding dorsal metacarpal tendon and MCP/PIP definition for Middle/Ring/Pinky; thumb/index influenced vertices and nail faces preserved. Multires and armature retained,1957drivers. Actual playing720x640, open/curl800x70024sampleCycles renders inspected: modest visible tendon improvement; smooth tubular fingers and rigid knuckle row remain. This is intermediate anatomy progress, NOT resolution of tiny-hand/full-view proportion or photoreal acceptance. Original playing pose restored before saving, camera set full view but no new full render yet. Playing check:13194finite evaluated vertices, no eight-string centreline crossings, conservative sampled clearance.34852mm. Initial +Y trial changed hidden side and was reverted: evaluated top displacement camera-normal dots negative. Correct visible dorsal side is local-Y; do not infer it from nail center+Y. Source nail normals-Y. Scripts pipeline/refine_v466_dorsal_anatomy.py and pipeline/finish_v466_hand_anatomy.py. V460 preserved rollback. No animation acceptance. Previous turn was no progress/status; this turn produces saved surface improvement and open/curl evidence. Next address full-view hand/cuff proportion decisively, then larger face/hair/guitar/fretting defects; do not loop on tiny surface trials.

## V465 localized MCP weighting comparison — 2026-11-04

Production remains V460. Changed54 base vertex weights on right Middle/Ring/Pinky only, halving MCP blend width24mm to12mm; thumb/index untouched. Actual800x70024sampleCycles curl render visually insufficient to fix tubular fingers or small-hand reading. Rejected, original weights and playing pose restored via pipeline/restore_v465_joint_weights.py;1957drivers intact. Trial pipeline/refine_v465_joint_weights.py and backed-up weights retained. Previous V464 turn progressed by ruling out linear skinning; current trial rules out narrower symmetric MCP transition. Do not keep sweeping global skinning/smoothing/blend widths. Next substantive correction must address anatomical surface form and cuff/hand silhouette, using reference overlays; wider character likeness, groom, guitar and fretting still unfinished. No new production blend.

## V464 linear skinning comparison — 2026-11-04

Current saved/live production remains V460. Compared identical V462 curled pose with Armature preserve_volume=False, actual800x70024sampleCycles render production_v464_linear_deformation/curl.png. Knuckle ridge softens but fingers lose volume and still look tubular; blanket linear skinning is not an adequate fix for small-hand reading. Rejected and restored original volume-preserving modifiers and playing pose through MCP,1957drivers verified. No production blend saved. Prior turn was visual status only; this turn yields matched evidence excluding another global deformation switch. V359 weights use symmetric longitudinal transitions (MCP24mm, PIP/DIP13mm) with no anatomical dorsal/palmar variation; targeted surface shape and joint weight transition remains next action, not further global smoothing or scaling. Trial and restoration scripts retained under pipeline/v464_*; full objective unfinished.

## V463 corrective smoothing rejected — 2026-11-04

Current saved/live production remains V460, original playing pose restored. Tested rest-bound CORRECTIVE_SMOOTH after Multires/Armature on both hands, 404 base vertices per side weighted to four non-thumb fingers. Mild factor.5 iterations6 and strong factor1 iterations30 each rendered actual800x70024sampleCycles curled right hand. Both visually insufficient: broad angular knuckle ridge and tubular fingers persist. Removed both modifiers and temporary groups;1957drivers intact; no new production blend saved. Next do not repeat generic corrective-smoothing tuning. Base hand has831vertices, Multires before preserve-volume Armature. Exported base_hand_weights.json (coordinates,weights,faces,restbones) in production_v463_knuckle_deformation to support targeted joint-shape/weight correction. Trial script pipeline/refine_v463_knuckle_deformation.py; renders production_v463_knuckle_deformation/curl.png and production_v463_knuckle_strong/curl.png. Prior V462 diagnostic turn was progress; current turn rules out a generic smoothing fix with matched visual evidence. Full objective unfinished.

## V462 open/curl deformation review — 2026-11-04

Current saved production remains V460. Live V461 iris contrast trial rejected as visually negligible; both eye slots restored to V374_PROCEDURAL_BROWN_EYE.001. Fresh V460 full-body render at production_v460_hand_skin/v460_full.png inspected. V462 diagnostic open and curled right-hand renders (800x700,24sampleCycles) completed and inspected; original playing pose restored through saved matrix_basis values, no animation cleared,1957 rig drivers retained. Both evaluated meshes13194 finite vertices. Open fingers show plausible length; curled pose produces overly blocky knuckle silhouette and smooth tubular fingers. This shifts next action away from blanket scale enlargement toward anatomical knuckle/skin deformation and silhouette. No claim of animation or collision acceptance; thumb retained playing pose and test poses were near guitar. Script pipeline/check_v462_hand_deformation.py; original_pose.json,open.png,curl.png and checks in production_v462_hand_deformation. No new production blend saved. Next improve knuckle deformation and finger shaping; broader face/groom/guitar/fretting work remains unfinished. Previous turn no state change; current turn yields new full-view and deformation evidence that changes next action.

## V460 softer hand folds — 2026-11-04

Current saved production_v460_hand_skin/Character_An_hand_skin_v460.blend. Material-only change from V459: copied both hand materials, reduced Shallow joint folds distance .55mm to .16mm and strength .75 to .32; bypassed V440 dark stripe overlay. Actual720x64024sampleCycles render inspected: engraved triple grooves now subtle, but skin still too smooth and nails simplistic. Hand geometry, pose, pick and collision relationships unchanged. Rig1957drivers; total scene1964drivers. Script pipeline/refine_v460_hand_skin.py; report and v460_hand.png in output directory. V459 rollback retained. No animation proof or realism acceptance. Next substantive face likeness/eye proportions and full-view comparison, then hand skin/nails and deformation tests; avoid further subpixel cuff or pick adjustments. Previous goal turn progressed saved V459 pick contact; this turn progresses material appearance. Goal unfinished.

## V459 pick reaches string — 2026-11-04

Current saved production_v459_pick_contact/Character_An_pick_contact_v459.blend. From V458, hand unchanged; rebuilt pick outline around existing skin-contact grip, 30.92mm overall length and16mm width. Target uses actual string polyline segment intersection with grip plane (first-to-last string chord was wrong and corrected). Evaluated pick nearest S3 surface gap .2603mm sampled every .2mm; other strings clear. Actual720x64024sample Cycles close render inspected. 1957 drivers preserved. V458 rollback retained. Skin/joint grooves/nails remain artificial; no animation validation, no new hand scaling. V458 static hand clearance remains applicable because hand unchanged. Next full-view proportions and substantive skin/joint shaping; character face/hair/guitar/fretting still unfinished. Script pipeline/refine_v459_pick_contact.py; report and pick_contact.json in output directory. Render complete.

## V458 thumb/index grip fit — 2026-11-04

Current saved/live production_v458_grip_fit/Character_An_grip_fit_v458.blend. V457 rejected and restored V456 before this work. V458 fits distal thumb/index bone targets with proportional step limiting and backtracking; index error .011mm, thumb rigid-target error4.761mm. Further thumb surface-point fit closes actual evaluated thumb/index gap to.842mm; wrist lifted1.5mm fromV456 to prevent string surface overlap. Pick plane rotated/aligned to midpoint of actual skin contacts. Static entire evaluated hand:13194finite vertices, no8stringcentrelinecrossings, conservative sampledmargin.349mm,1957drivers preserved. Actual1000x700wrists and720x640pick-close24sampleCycles renders inspected. Close shows relaxed fingers and pick beneath grip; skin/nails still artificial. Saved viaMCP. NOT accepted exactpick/stringcontact or animation collision clearance. Scripts pipeline/refine_v458_grip_fit.py, finish_v458_grip_fit.py, align_v458_pick.py run sequentially fromV456, not idempotent; check_v458_grip_fit.py and inspect_v458_pinch.py read-only exceptreport. Reports inproduction_v458_grip_fit. No rendering running. V456 rollback retained. Next actualpick/string contact and deformation tests; cuffs/face/hair/guitar likeness remain unfinished. Prior goal turn yielded evidence rejectingV457 and restoredV456; this turn changes saved authoritative grip.

## V456 picking hand approaches strings — 2026-11-04

Current saved/live production_v456_pick_approach/Character_An_pick_approach_v456.blend. From V455: IK-Hand.R translated8mm along negative guitar-localZ, other controls unchanged. All8strings evaluated BVH: no centreline crossings,2.535mm conservative sampled clearance,13194finite vertices,1957drivers.12mm trial crossed S5, rejected. Actual1000x70024sampleCycles v456_wrists.png inspected: relaxed silhouette retained, no obvious wrist seam gap in this view. Saved via MCP. Still not accepted pick/string contact (roughly11mm remaining gap from prior tip estimate), no full collision or animation validation. V455 rollback preserved. Next adjust thumb/index grip and pick orientation jointly; further whole-wrist lowering alone hits strings. Script pipeline/refine_v456_pick_approach.py. Initial script property mutation accidentally edited temporary matrix and did not move hand; corrected to assign full matrix before actual trials; report and render now reflect corrected run. Goal unfinished.

## V455 relaxed picking fingers — 2026-11-04

Current saved/live production_v455_relaxed_picking/Character_An_relaxed_picking_v455.blend. From V452: right free-finger FK X angles Middle10/15/8, Ring15/20/10, Pinky20/25/12 degrees; wrist, thumb/index and geometry unchanged. Actual1000x70024sampleCycles v455_wrists.png visually inspected: fingers now visibly longer and more natural, without scaling. Full evaluated hand BVH test against all8 string polylines found no centreline crossings and10.033mm conservative sampled clearance;13194 finite vertices,1957drivers. This is a silhouette improvement only, not accepted pick contact or full animation validation. V452 rollback preserved. Next can use increased string clearance to lower wrist toward actual pick contact, with coupled grip adjustment rather than prior extreme wrist roll. Cuffs remain bulky; face/groom/guitar and fretting remain unfinished.

Current V452 thumb-index skin diagnostic measured nearest signed gap .959mm at guitar-local index point(.636374,-.021557,.059348), normal(.740600,-.035108,.671028). Pick still stale/too high relative to strings. V454 pitch trial about guitarY at±15/25/35/45 all crossed strings and was rejected/restored; no blend saved. V453 rigid guitarX roll already rejected visually. Do not repeat those unchanged strategies. Current render complete, no background render running.

## V453 pick-contact wrist roll rejected — 2026-11-04

Current live restored V452 through MCP. V452 close render confirms clenched/stubby finger silhouette; actual pick lowest guitar-local z .04765 versus strings near .028 gives about20mm reach gap. Tested rigid hand/pick transform bringing lowest pick vertex to S4 plus0.7mm clearance and rolling about guitar longitudinal axis. First passing trial -50deg had4.445mm conservative sampled hand/string margin and1957drivers, but actual1000x70024sample v453_wrists.png visibly hides fingers and excessively twists sleeve. Rejected, no V453 blend saved. This disproves rigid wrist/contact correction as sufficient; rebuild thumb/index grip and pick angle while preserving relaxed wrist and free-finger silhouette. CurrentV452 remains only working checkpoint, not accepted playing pose. Diagnostic script pipeline/refine_v453_pick_contact.py, report production_v453_pick_contact/report.json. Goal unfinished.

## V452 picking wrist and free-finger pose — 2026-11-04

Current live/saved working checkpoint production_v452_picking_pivot/Character_An_picking_pivot_v452.blend. Relaxed right Middle/Ring/Pinky to25/48/22,30/54/25,35/60/28 degrees; rotated IK-Hand.R -10deg about world(.5,0,-.866) around index distal tail and shifted12mm outward(-worldY). Rotating alone failed;2–10mm shifts failed clearance.12mm yields no string-centreline crossings and1.202mm sampled conservative clearance. Actual1000x70024sampleCycles v452_wrists.png inspected: less clenched silhouette, cuff still bulky, no obvious wrist gap in this view.1957drivers preserved. This is an intermediate visual/clearance improvement, NOT accepted playing contact: index pivot shifted12mm and pick reach must be corrected. Thumb/index controls unchanged but world pose changed; no full collision or animation validation. V449 remains rollback. Full character/guitar/likeness objective unfinished. Next inspect actual pick geometry and adjust grip/pick reach before accepting picking pose.

## V451 picking silhouette test rejected — 2026-11-04

Current scene remains V449; original picking finger rotations restored through MCP. Tried relaxing right Middle/Ring/Pinky from approximately48/78/37,51/81/39,54/84/41 degrees to25/48/22,30/54/25,35/60/28. Actual1000x70024sampleCycles v451_wrists.png visually less clenched, but geometric check found string centreline crossings S2/S3 and negative sampled clearance. A35% interpolation removed centreline crossings but retained negative conservative clearance(-1.043mm). Neither candidate accepted or saved as current. Thumb/index/wrist untouched;1957drivers and13194finite evaluated hand vertices preserved. Test script pipeline/refine_v451_picking_silhouette.py intentionally diagnostic, not accepted pose. Next picking correction must jointly orient wrist/palm and free fingers while keeping thumb/index pick contact; simply uncurling fingers drives them toward the strings. Render is rejected diagnostic only. Project unfinished.

## V450 pupil test rejected — 2026-11-04

Current live restored V449 `production_v449_swept_curls/Character_An_swept_curls_v449.blend` through MCP. V450 set both V374_EYE Dilation shape keys from.90 to.35. Actual700x80032sampleCycles render inspected: larger/darker pupil appearance and reduced iris detail, worse. Do not repeat lower Dilation as smaller-pupil assumption; inspect actual key vertex geometry/material regions first. V450 retained diagnostic only, not accepted current state. No face geometry/material changes retained. 1957drivers preserved during test. Skin node inspection found face uses linked V383 roughness/specular/subsurface,55micron bump distance; need inspect those linked values rather than blindly overwrite. Next improve eyelid/iris proportions and face likeness with actual geometry evidence. Full project unfinished.

## V449 shorter swept sides — 2026-11-04

Current saved/live `production_v449_swept_curls/Character_An_swept_curls_v449.blend`. From V448 via `pipeline/refine_v449_swept_curls.py`: spatial side-weight blends flow backward/downward, reduces side curl radius up to68%, axial length30%, turns55%; varied phase progression and taper break repeated helices; hair roughness .44. V448 and V389 preserved hidden. Actual700x80032sampleCycles `v449_face.png` inspected: sides visibly closer to scalp, crown less regular, but still ribbonlike and not reference/photoreal acceptance. 925groups85100strands2127500points,1957drivers retained. Script parsed successfully; MCP confirmed render finished. No new animation or full-view validation. Next substantial likeness work: facial proportions and skin/eyes, groom needs softer natural grouping. Hands/fret targets/guitar still unfinished; no further hand scaling. Goal remains active.

## V448 larger curl groups — 2026-11-04

Current saved/live `production_v448_loose_curls/Character_An_loose_curls_v448.blend`. Built through live MCP from V447; actual previous groom is V389_CURL_GROOM (preserved hidden), not V386. 925 guide groups, 85100 strands, 2127500 points; root spacing8mm, primary curl radii6.5–9mm, axial length20–28mm, .65–1.05turns, 80 primary children. 1957 rig drivers preserved. Actual700x80032sampleCycles CPU4 `v448_face.png` rendered and inspected against approved_character_design_lock.png. Larger curls visible but still overly regular/ribbonlike, side silhouette too bulky; facial likeness/material realism remain unfinished. Working checkpoint only, not groom acceptance. V447 rollback retained. Script syntax passed; render terminal confirmed false. Next shorten/sweep side groom and break repetitive curl geometry; retain hands at existing size until reference proportion check, resolve anatomical playing contact separately. Full goal unfinished.

## V447 cuff with protected wrist band — 2026-11-04

Current saved/live `production_v447_clearance_cuff/Character_An_clearance_cuff_v447.blend`. Derived from V445. First vertex-only signed BVH clearance check missed the V446 visible overlap, so do not treat its zero-regression metric as proof of collision-free geometry. Final candidate preserves vertices within20mm of evaluated hand/body skin, smoothly increases tailoring through50mm. 3710 vertices partially/fully protected, max4.282mm displacement;1957drivers retained; hand geometry and pose unchanged. Actual1000x70024sampleCycles `v447_wrists.png` inspected: prior exposed skin protrusion absent in this view, modest upper cuff reduction. Cuff remains bulky; avoid spending further turns on subpixel tailoring. No animation collision proof. Script syntax passed, no render running. Next prioritize substantive face/groom reference likeness and guitar/playing-pose defects. V445 rollback retained. Full goal unfinished.

## V446 cuff narrowing rejected — 2026-11-04

Restored V445 through live MCP after actual V446 1000x700 /24sample Cycles review exposed a skin protrusion at the outer fretting wrist. V446 narrowed cuff radial16% with sinusoidal rest-z falloff .865–.942; 3258vertices, max6.338mm. Hand geometry/pose unchanged,1957drivers retained. Candidate and render retained as diagnostic only, NOT accepted current state. Current saved/live `production_v445_cuff_fabric/Character_An_cuff_fabric_v445.blend`. Next cuff fitting must use evaluated posed wrist clearance, not another uniform radial contraction. No render running. Full objective unfinished.

## V445 cuff fabric — 2026-11-04

Current saved/live `production_v445_cuff_fabric/Character_An_cuff_fabric_v445.blend`. Copied cuff material to V445_Charcoal_Cuff_Fabric, added charcoal weave albedo (.009–.021 channel range), matched jacket specular .18, sheen .06 and diffuse roughness .3. Geometry and hand pose unchanged; inherited 1957 drivers retained. Actual 1000x700 / 24-sample Cycles CPU4 `v445_wrists.png` completed and visually inspected: cuffs now dark and substantially closer to jacket fabric; oversized/flared cuff silhouette remains, especially fretting wrist. Hands do not read as tiny in this close view; picking fingers remain bunched and fretting contacts unfinished. This is material improvement, not proportion or animation acceptance. MCP reports no render running and V445 loaded. V444 fallback preserved. Next correct cuff silhouette and anatomical playing pose, without further blanket hand enlargement. Full project unfinished.

## V444 forearm sleeve volume — 2026-11-04

Current saved/live `production_v444_sleeve_volume/Character_An_sleeve_volume_v444.blend`. `pipeline/refine_v444_sleeve_volume.py` syntax checked and executed through MCP. Radial tailoring up to20% about rest forearm axes, smoothly faded from z.915 to1.17m, applied coherently to jacket-material vertices in joined body (all shape keys receive same delta) and both visible cuffs. Max body displacement16.727mm, Lcuff10.296mm, Rcuff13.722mm; hand geometry and pose unchanged. Wrist hem below.915 preserved; button/stitches unchanged there. All1957drivers retained. Actual720x96016sampleCycles `v444_full.png` inspected: forearm silhouette slimmer, wrist cuff flares remain, no obvious new gap at this full-view resolution. Not close seam/collision or animation validation. Saved camera remains face fromV443, live camera full-body after render request. No render running. V443 rollback preserved. Next wrist cuff flare and hand presentation, then reference likeness/groom and exact fret contacts. Goal unfinished.

## V443 eye aperture and closed blink review — 2026-11-04

Current saved/live `production_v443_eye_aperture/Character_An_eye_aperture_v443.blend`. Neutralized Head BrowInnerUp from .5 to 0 (V442 render showed little visible difference). Adapted V396 lid geometry to joined V416_BODY_CLEAN_JOIN and boundary-cycle traversal; lower aperture -.0038 versus -.0022m. Actual maximum opening vertex displacement 2.792mm L / 2.631mm R. Body Blink targets unchanged; margins and lashes rebuilt. 1957 drivers retained. Actual 700x800 / 32-sample Cycles open `v443_face.png` and closed `v443_closed.png` inspected. Eyes visibly more open; closed lids cover eyes without obvious exposed iris in this frontal view. Not full animation or multi-angle acceptance; lids remain smooth, iris dark/large, skin plastic in places, groom too uniform. Restored both Blink controls to zero and saved through MCP; no render running. Current camera face close-up. V441 remains fallback. Hands retain prior 18% enlargement; bulky cuffs and playing contacts unresolved. Next improve cuff/sleeve silhouette and hand presentation, then groom/likeness; do not repeatedly enlarge hands to compensate for sleeves. Fret mapping clarification remains pending.

## V441 cuff weave and full character comparison — 2026-11-04

Current saved/live `production_v441_cuff_weave/Character_An_cuff_weave_v441.blend`. Full V440 Cycles render `production_v440_hand_folds/v440_full_review.png` inspected alongside approved_character_design_lock.png. Remaining obvious gaps: smooth oversized sleeves, uniform groom, facial likeness/eye realism, guitar silhouette and precise hand contacts. Hands no longer read as tiny in full view, but this is visual judgment, not final proportion approval.

Live material inspection found body retains V372_RestPosition and existing denim maps; both replacement cuffs instead use V402_Charcoal_Cotton_Cuff without that weave. `pipeline/refine_v441_cuff_weave.py` copies cuff material and mesh, adds V441_CuffRest point positions, existing packed CC0 Poly Haven denim height/roughness box projection at .271m scale, .00018m bump/.45 strength, roughness .7–.9 and sheen .13. Inner hems untouched; 1957 drivers retained; script syntax passed. Actual 700px 32-sample Cycles `v441_lit.png` completed and inspected: change subtle at this view; cuffs still visibly smooth/bulky. Do not claim material fix solves garment realism. No job running. Current blend saved before close-camera request; runtime close camera differs from saved full camera. Fretting mapping question still pending. Next prioritize visible geometry/likeness changes rather than repeatedly tweaking subpixel fabric.

## V440 reversible hand deformation review — 2026-11-04

Ran `pipeline/review_v440_hand_deformation.py` through live MCP; syntax passed. Rendered actual Workbench open (0/0/0 degrees) and curl (45/80/40 degrees) left Index/Middle/Ring/Pinky FK poses. Each evaluated mesh has 13194 finite vertices and all 1957 drivers. Inspected both images: fingers bend without obvious detached nails or exploded geometry in this view; curl bunches fingers and wrist has strong tendon-like ridges. No claim of self-collision-free deformation, thumb/right-hand testing, or animation readiness. Guitar intersections in diagnostic poses are not accepted playing contact. Original rotations and render settings restored in finally; saved V440 unchanged. Evidence `production_v440_hand_folds/deformation_review/{open,curl}.png` and `report.json`. Next: broader hand/wrist motion and character likeness work; fret mapping question remains pending.

## V440 hand folds and actual fret-target measurement — 2026-11-04

Current saved/live `production_v440_hand_folds/Character_An_hand_folds_v440.blend`. Preserves V439 geometry/pose and 1957 drivers. `pipeline/refine_v440_hand_folds.py` strengthens rest-coordinate joint folds (bump distance .00055, strength .75) and adds subtle fold pigment. Actual Cycles 700x700 / 32-sample `v440_lit.png` completed and visually inspected: joint folds visible, open fingers and nails readable; skin still smooth, cuff still bulky. Useful incremental material improvement, not final photoreal acceptance. No render running.

V439 actual string-polyline targets measured against isolated distal finger surfaces: index 42.074 mm, middle 17.041 mm, ring 33.945 mm, pinky 19.137 mm. These are nearest distal-surface distances, not pad-only measurements. Report `production_v439_arch_clearance/assigned_target_review.json`. Current open pose does NOT satisfy saved chord assignments. Async question pending: reference illustration index toward nut/ring farther down neck conflicts with saved index F11/ring F9 order. Preserve mapping until answered; do not silently substitute assignments or repeat fingertip-only fitting that produced crossed/bunched fingers. Full character and animation validation remain unfinished.

## V438/V439 palm placement — 2026-11-04

Current saved/live `production_v439_arch_clearance/Character_An_arch_clearance_v439.blend`. From V436, translated IK-Hand.L world (0,+.020,-.025)m, then bounded inward clearance search selected another +.005m Y. Finger arches retained unchanged. 6–8mm additional offsets crossed strings; 5mm has no centerline crossing and minimum conservative sampled margin0.101mm. Picking hand previously unchanged margin2.662mm. 1957 drivers retained. `pipeline/refine_v439_arch_clearance.py` syntax passed. Workbench and actual Cycles close `production_v439_arch_clearance/v439_lit.png` inspected: open separated fingers and visible nails, better than tight fist; still smooth skin, bulky cuff, assigned fret contacts NOT solved. Contact test is whole-hand clearance, not individual pad matching or full guitar collision. Blender window inventory confirms both windows workspace7. Render finished, no active job. Next measure isolated distal pad contact to each assigned string/fret, reconcile longitudinal reach while retaining anatomy; remaining full character/rig quality work continues.

## V437 curl-depth study rejected — 2026-11-04

Tested bounded anatomical curl with MCP15, PIP35–70, DIP15–40 degrees, retaining lateral axes zero. Actual Workbench preview inspected. It hides nails and bunches fingers again, while index bone endpoint still 14.49mm from desired depth, ring3.45mm, pinky6.09mm. Middle intentional hover depth fits0.116mm. Actual string ray check: no centerline crossings, minimum conservative margin L0.430mm/R2.662mm; this does NOT prove assigned pad contact. 1957 drivers retained. Saved diagnostic `production_v437_arch_contact/Character_An_arch_contact_v437.blend`, not accepted. Restored V436 open arch baseline. Next change palm placement/orientation while maintaining open arches; do not repeat more curl alone. Exact assignment/mapping remains unresolved. Full character unfinished.

## V436 open arch study — 2026-11-04

Saved/live `production_v436_arch_study/Character_An_open_arch_study_v436.blend`. V435 preserved. Fretting index/middle/ring/pinky FK joint rotations reset to X=15/35/15 degrees, Y/Z=0. No further hand scaling or wrist movement. All 1957 drivers retained. Previous rotations in `production_v436_arch_study/before.json`. Actual Workbench close `v436_open_arch.png` inspected against `references/hands/m3_chord_hand_v3_compact.png`: longer separated arches and visible nails substantially improve the apparent hand proportions. This is a pose study, NOT an accepted chord/contact solution: fingertips hover, mapping and surface contact remain to fit. Avoid repeating fingertip-only fits that collapse the hand into a fist. Next adjust palm placement while preserving anatomy, then verify actual pad contact and full character proportions. No render running. Full character unfinished.

## V435 left cuff tailoring — 2026-11-04

Saved/live `production_v435_left_cuff/Character_An_left_cuff_v435.blend`. Fretting cuff midsection narrowed with smooth radial falloff, maximum 22% at midsection / 10.86 mm vertex displacement. Preserved vertices below z=.881 and above .933, including wrist hem and upper attachment. Mesh copied, UVs/weights intact, hands and pose untouched, 1957 drivers retained. V434 picking cuff narrowing retained. Script `pipeline/refine_v435_left_cuff.py` syntax passed. Actual Workbench and Cycles torso previews completed and inspected (`v435_shape.png`, `v435_torso.png`): both cuffs less bulky, no obvious opened seam from frontal view; upper sleeve volume remains. No deformation/contact proof from this image. No job running.

Reference hand image inspected again: open long separated arches versus current tightly bunched fist. Next prioritize pose anatomy; repeated fingertip-only numerical fitting failed. Physical guitar orientation remains unchanged; diagram-top convention must not be treated as world-top. Current pose target index F11 versus ring F9 may require a different palm placement to avoid crossing. Preserve verified assignments, inspect actual surfaces and joint directions. Full character unfinished.

## V434 cuff taper candidate — 2026-11-04

Saved/live `production_v434_cuff_taper/Character_An_cuff_taper_v434.blend`. Right cuff intermediate rings narrowed 14%, 18%, 6% radially; jacket seam and wrist opening unchanged, hands/pose untouched, all 1957 drivers retained. Script `pipeline/refine_v434_cuff_taper.py` syntax checked and executed through MCP. Actual Workbench torso `v434_shape.png` inspected: picking cuff taper cleaner, but upper sleeve still bulky and left cuff very oversized; fretting pose remains an unacceptable tight fist. Needs lit comparison, left cuff correction and anatomical hand pose. No render running. V430 preserved.

CORRECTION to previous orientation conclusion: mapping says S8 top IN THE M3 DIAGRAM. Diagram vertical ordering does not establish physical world-up string ordering. Do NOT reflect mechanical guitar assembly based on that statement alone. No guitar geometry changed. Resolve against physical reference before making a handedness change. Current target solver can still require actual string surface height correction independently.

## V432/V433 rejected; string orientation defect found — 2026-11-04

V430 remains working checkpoint. V432 rotates palm -55 degrees world Y around knuckle centroid, resets fingers, refits with tighter lateral bounds: ring misses 17.1 mm. Actual Cycles render inspected: wrist horizontal to right, tightly folded fingers, wrong reference posture. Rejected. V433 opposite +55 degrees also fails: index 25.7 mm and middle 21.8 mm misses; saved diagnostic only, not rendered or accepted. Scripts syntax checked for V432; both executed through MCP retaining 1957 drivers. Restore V430 before further work.

LOAD-BEARING DISCOVERY: live guitar local +Y (S1 toward S8 per guitar_geometry.py) maps world (0.4539906, -0.00000015, -0.8910065). Thus S8 is below S1, contradicting references/m3/m3_chord_mapping_v2.json specification S8 top. Actual string nut endpoints: S1 (0.440485,-0.2461,1.313079), S8 (0.451441,-0.2461,1.263667). Prior solver therefore fits vertically reversed string ordering relative to supplied specification. Also analytical target height 0.02045 does not match actual string centerline height (V430 notes). Correct instrument string/fret geometry and target transform coherently before any more blind hand fitting; do not merely relabel strings, since multiscale lengths, fret intersections and hardware must agree. Preserve body silhouette and existing source checkpoint. Need inspect inherited root transformation and neck geometry generation to choose narrow correction. Reference illustration versus exact finger mapping may also differ; retain explicit user-verified mapping.

## V431 rejected; restored V430 — 2026-11-04

V431 open-arches experiment saved separately but rejected after actual Cycles image review: crossed fingers, joint-limit saturation, substantial target errors. Fixed world distal direction plus fingertip fitting did not resolve palm orientation. Do not promote V431 or repeat this fit unchanged. Restored V430 via MCP; retains enlarged hands. Current hand appearance still compromised by tightly folded pose and oversized cuffs. Next inspect palm rotation and anatomical joint axes against reference before further fitting; do not enlarge hands repeatedly to compensate for pose.

## V430 fretting clearance — 2026-11-04

Current saved/live `production_v430_fret_clearance/Character_An_fret_clearance_v430.blend`. V429 crossings localized by evaluated mesh polygon weights to Index3 S6, Ring3 S7, Pinky3 S8, all intended contact digits. Actual strings at y about -0.2468 versus analytic target plane -0.24545; prior target plane was not actual string surface. Bounded wrist outward trials 0–3 mm: 3 mm cleared all centerline crossings with conservative minimum surface margin 0.274 mm. Retains 1957 drivers. Script `pipeline/refine_v430_fret_clearance.py` syntax passed; report beside blend. Actual close Cycles render `v430_fretting_close.png` complete and inspected.

Reference `references/hands/m3_chord_hand_v3_compact.png` visually inspected alongside current close render: reference has open long finger arches, visible nails; current fingers excessively folded/overlapping with nails obscured. Clearance correction is useful but pose NOT accepted anatomically. Next use distal orientation as well as tip position in fitting, adjust wrist/palm orientation to create reference arches. Do not continue optimizing only distance. V429 crossing details `crossing_locations.json`. Full character remains unfinished; no render active.

## V429 evaluated finger surface fit — 2026-11-04

Current saved/live `production_v429_pad_contact/Character_An_pad_contact_v429.blend`. Script `pipeline/refine_v429_pad_contact.py` corrects V428 bone targets using measured evaluated digit surfaces. Syntax passed; 1957 rig drivers retained. Actual target-to-digit surface distances: index 0.170 mm, ring 0.053 mm, pinky 0.074 mm; middle intentional hover 9.850 mm. Reports `pad_surface_review.json` and `contact_review.json`. This uses entire digit surfaces, not isolated pads; it does not prove correct pad orientation.

Actual Cycles close render `v429_fretting_close.png` completed and inspected. Fingers appear tightly curled with awkward overlap; anatomical pose remains unacceptable for final. String centerlines cross left-hand mesh on S6/S7/S8, despite near-zero target gaps. Picking hand retains no crossings and 2.662 mm conservative clearance. Next: locate crossing segments on each digit and adjust pad orientation/hand orientation rather than merely chasing target distance. Preserve V427/V428 fallback. Cuffs remain oversized, hand surface too smooth. Full character goal is not complete. No render running at checkpoint.

## V428 fretting candidate — 2026-11-04

Current saved/live: `production_v428_fretting_targets/Character_An_fretting_targets_v428.blend`. Retains 18% hand enlargement and V427 picking clearance correction. Existing left wrist moved (-40, 0, -15) mm and four FK finger chains fitted to authoritative chord targets; 1957 drivers retained. Bone-target residuals index 0.17 mm, middle 0.06 mm, ring 2.82 mm, pinky 0.10 mm. These are NOT evaluated surface contact results.

Actual Cycles render `production_v428_fretting_targets/v428_hands.png` completed and inspected. Hands fuller than original; bulky cuffs still exaggerate narrow wrists. Fretting fingers now compact on intended neck area, but tightly curled pose needs closer pad/contact, thumb and self-intersection checks before acceptance. No claim of finished chord pose or animation readiness. V427 remains fallback; V428 before.json preserves prior left controls. Next: evaluated surface/contact check and close side view, then remaining face, hair, garment and guitar reference work.

## V427 picking clearance — 2026-11-04

Current saved/live: `production_v427_pick_contact/Character_An_pick_contact_v427.blend`. Preserves V426 18% enlarged hands, moves picking IK wrist 4 mm outward. Evaluated mesh check: no string centerline crossings, conservative minimum margin 2.662 mm; all 1957 drivers retained. Actual Cycles close render `v427_hands.png` completed and inspected: fuller hands, cuffs still bulky; fretting pose visibly needs work. Script syntax passed.

Important next work: fretting is not merely hovering. `fretting_targets.json` evaluates authoritative `references/m3/m3_chord_mapping_v2.json` targets with `pipeline/guitar_geometry.py`: index S6/F11, ring S7/F9, pinky S8/F11, middle hover S6/F10. Bone-tip target distances are 101, 21, 43, 48 mm respectively; nearest ANY hand surface at targets 36, 11, 38, 15 mm. Do not interpret nearest-any-surface as finger contact. Need correct individual CloudRig finger pose and verify evaluated pads, thumb behind neck, no mesh interpenetration. Older `probe_v319_hybrid_fretting_matrix.py` resolves target coordinates but uses old Rigify names; do not run its pose/build routines or reopen old scene. Read-only diagnostic `/tmp/bca_v427_fret_targets.py` uses current CloudRig names.

V427 is progress, not finished character or validated chord. Full objective remains active, including facial likeness, hair, garment construction, guitar reference fidelity, and animation/deformation tests.

## V426 hand proportion candidate — 2026-11-04

User called out tiny hands. Enlarged both existing IK hand controls 18%, translated wrists to preserve selected fingertip bone anchors, retained all 1957 drivers. Saved `production_v426_hand_proportions/Character_An_hand_proportions_v426.blend`. Actual Cycles torso render inspected: hands read fuller; cuffs remain bulky. This is a candidate, not accepted contact or final quality.

Direct evaluated-mesh string check: picking R crosses string 1 (minimum conservative margin -1.185 mm); fretting L has no string crossings but minimum margin +3.307 mm, so fretting contact also needs correction. Next: repair surface contact for enlarged hands and inspect cuff connections. Bone anchor preservation did not preserve surface clearance. Check result: `production_v426_hand_proportions/contact_review.json`. Render: `production_v426_hand_proportions/v426_torso.png`.

V425 enlarged botanical shirt motifs 3x and was visually inspected; V426 matches collar motif scale while preserving its skin boundary. V425 remains pre-hand-scale fallback. Face, hair, garment construction, guitar accuracy and animation validation remain unfinished.

## V424 rest-coordinate skin — current working checkpoint

- Saved `production_v424_rest_skin/Character_An_rest_skin_v424.blend`; V423 retained. Both hand materials copied and all three procedural noise nodes per hand linked to existing `V423_rest_position` attribute. Preserves pigment, roughness and pore coordinates through deformation. No geometry or pose edits; 1957 drivers retained.
- Script `pipeline/refine_v424_rest_skin.py` compiles. Wiring assertions passed in Blender. Temporal texture stability has not been rendered.
- Actual Cycles `production_v424_rest_skin/v424_full_character.png` completed and visually inspected against approved design lock. Largest visible gaps: smooth jacket lacking fabric/seam definition, too-small shirt floral motif, rigid uniform hair silhouette and facial likeness. Guitar silhouette/fretting contact need focused comparison. Not photoreal or animation-ready.
- Full render used 720x960, 16 samples, four CPU threads. Render complete. Live camera now full character; saved checkpoint retains prior hand camera. Request JSON contains full-character framing. No pose test or restoration needed this increment.
- Next prioritize reference-scale shirt pattern and jacket surface, then facial likeness/groom and guitar/contact. Avoid continuing tiny hand-only changes at the expense of the full character. Startup service remains stale V405; do not restart into it.

## V423 joint crease material — current working checkpoint

- Saved `production_v423_joint_creases/Character_An_joint_creases_v423.blend` with picking pose. V422 retained.
- Both hands have rest-position and rest-normal mesh attributes and per-hand copied skin materials. A reusable shader group adds shallow tapered folds at 14 finger joints per hand. Bump only; no mesh silhouette, weighting or rig edits.
- Actual Cycles `v423_pick_close.png` inspected: joint folds visible, but too regular. `v423_open_lit.png` inspected: hand coherent; details too subtle at overview scale for strong deformation acceptance. Not photoreal or animation-ready.
- Restored all 19 temporary open-pose controls with zero rotation error; 1957 drivers retained. Saved file was written before temporary open test and retains picking pose. Live also restored. No render active at completion.
- Scripts `pipeline/refine_v423_joint_creases.py`, `pipeline/check_v423_open_lit.py`, `pipeline/restore_v423_pose.py` compile. Pose restoration report beside checkpoint.
- Next improve natural hand detail and ensure all procedural skin variation uses rest coordinates (original V422 noise still uses Object coordinates), then broaden to face/groom/guitar/fretting and animation deliverables. Full project unfinished. Startup service remains V405; do not restart into stale checkpoint.

## V422 hand surface — current working checkpoint

- Saved `production_v422_hand_surface/Character_An_hand_surface_v422.blend`. Original V421 and original skin/nail materials retained.
- Both hands use copied materials with restrained pigment and roughness variation, reduced IOR and softer nail coat. No mesh, pose or rig changes; 1957 drivers retained.
- Actual Cycles `production_v422_hand_surface/v422_pick_lit.png` inspected against V421: reduced broad plastic sheen. Still visibly too smooth; anatomical joint folds/creases remain necessary. Material improvement only, not photoreal acceptance.
- Both Blender windows PID 7901 confirmed on workspace 7. Render used four CPU threads. Startup service remains V405; do not restart into it by mistake.
- Next: anatomically placed hand creases/detail, then remaining face/groom/guitar/fretting and animation work. Full project unfinished.
- Script `pipeline/refine_v422_hand_surface.py` compiles; review recorded beside checkpoint.

## V421 regular sleeve loft — current working candidate

- Current saved file: `production_v421_regular_loft/Character_An_regular_loft_v421.blend`; original V413 and body retained. Startup service remains V405; do not confuse startup with latest working state.
- V416 replaced jagged overlap with a shared cut boundary. V417/V418 smoothing retained fine radial folds. V419 matched loft correspondence and V420 smoothed the shared boundary, but did not adequately remove them.
- V421 rebuilds the taper with 96 evenly spaced vertices per ring, moving unequal-loop stitching to the jacket edge. Actual Workbench picking preview inspected: substantially smoother taper, wristband/stitches/button retained. Small ripples remain near the jacket edge. Not final photoreal quality.
- Visible replacement objects: `V416_BODY_CLEAN_JOIN` and `V421_REGULAR_SLEEVE_CUFF.R`. Original `V357_TRIPO_CHARACTER_BODY_BOUND`, `V411_FITTED_CUFF.R`, and `V416_SHARED_BOUNDARY_CUFF.R` retained hidden.
- 1957 rig drivers retained, hand controls unchanged. Scripts `pipeline/refine_v419_loft_correspondence.py`, `pipeline/refine_v420_boundary_flow.py`, `pipeline/refine_v421_regular_loft.py` compile. Open-hand diagnostic inspected; all 19 controls restored with zero rotation error. Actual Cycles `v421_pick_lit.png` completed and inspected: taper substantially cleaner; upper seam still visible, fabric lacks weave, and hand skin remains smooth/plastic. Next improve hand skin/material detail and tailored seam finish; do not claim photoreal acceptance.
- Full character remains unfinished: face likeness/skin, hair, fretting contact, wardrobe and animation testing still require substantial work. Both live Blender windows (PID 7901) confirmed on workspace 7 through the GNOME extension runtime window inventory during this increment.

## V414/V415 sleeve fit tests rejected — resume V413

- V414 projected the upper 288 cuff vertices onto the preserved cuff and transferred jacket weights. Actual wide Workbench preview showed pinched folds and persistent jagged upper overlap.
- V415 repeated the same geometry with preserved cuff weights; actual preview remained effectively unchanged. This isolates the projected geometry as the main problem in these tests, rather than the choice of weight source.
- Both candidates rejected. Reopened `production_v413_cuff_fastener/Character_An_cuff_fastener_v413.blend`; no unsaved user changes existed before these agent edits. Do not resume V414/V415.
- Next replace the overlapping sleeve/cuff seam with a clean common boundary. Original V353 body removed faces by face-center z below .935, leaving a jagged boundary; cuff extends to .945. Nearest-surface projection of the upper cuff does not solve this and should not be repeated.
- Live body name `V357_TRIPO_CHARACTER_BODY_BOUND`, 232473 vertices, identity world transform, one Armature modifier. Local join sample in `production_v414_sleeve_join/body_join.json` (2090 vertices). Preserve the original body mesh before any boundary reconstruction.
- Latest accepted candidate remains V413, not final quality. Full character remains unfinished.

## V413 cuff normals and fastener — latest working checkpoint

- Found live Blender had restarted into clean V405; restored saved V412 without discarding edits. Current process observed PID 7901.
- Saved `production_v413_cuff_fastener/Character_An_cuff_fastener_v413.blend`. Corrected confirmed inward outer-cuff normals, reseated stitches outside the surface, added a rig-weighted 9.8 mm pressed brass button.
- Actual Workbench picking and open-hand previews inspected: cuff opening/stitches/button coherent. Wider open-hand view reveals conspicuous jagged overlap at upper sleeve join to original jacket; repair that transition next. Placket geometry still absent. Lit material acceptance pending.
- Open-hand diagnostic restored all 19 controls with zero rotation error; all 1957 drivers intact. This tests finger opening only, not wrist flexion or animation readiness.
- Scripts `pipeline/refine_v413_cuff_fastener.py`, `pipeline/check_v413_open_hand.py`; images/report in production directory. Startup remains V405. wmctrl cannot see native Wayland Blender windows, so workspace 7 not freshly verified.
- Next repair upper cuff/sleeve overlap, inspect lit, then continue hand skin detail and full character work. Full goal remains incomplete.

## V412 stitch conformity candidate — latest working file

- V411 tightened the right cuff opening 8 percent and added 288 individual stitches in four rows, with rig weights. Actual Cycles render `production_v411_cuff_stitch/v411_pick_close.png` inspected: continuous rounded opening, but upper rows float above tapered cloth; hand skin remains featureless.
- V412 projects stitch endpoint rings onto the actual unposed subdivided cuff surface and refreshes their rig weights. Saved `production_v412_conform_stitch/Character_An_conform_stitch_v412.blend`. Lit inspection still pending.
- Check cuff outer-face normal orientation before accepting V412: original V410 ring winding may point inward, affecting the 0.23 mm stitch normal offset. Correct outward orientation and inspect close-up before proceeding.
- Scripts compile; 1957 rig drivers retained. Hand pose unchanged. Original cuff and V410 retained hidden. Startup service unchanged.
- Next: verify stitch seating, add reference button/placket, inspect cuff wrist deformation, then improve hand skin/nails. Full character remains unfinished.

## V410 clean cuff candidate — latest working file

- Saved `production_v410_clean_cuff/Character_An_clean_cuff_v410.blend` through the existing Blender MCP connection.
- Replaced the damaged right cuff surface with a smooth quad sleeve taper, rounded opening and inner return. Original `V357_CUFF_PATCH.R` retained hidden; its materials and interpolated deformation weights reused.
- Actual `production_v410_clean_cuff/v410_pick_diagnostic.png` inspected: continuous cuff silhouette without the previous torn-looking folds. Opening remains loose; needs reference-matching structured wristband, stitching and button. Workbench only, not lit material acceptance.
- V408 finger pose untouched; 1957 rig drivers retained. V408 remains fallback. Startup service unchanged.
- Next refine cuff fit/details and inspect lit plus open/curled deformation. Character remains unfinished.
- Script: `pipeline/build_v410_clean_cuff.py`.

# Character Asset_An resume

## Current working checkpoint: V408 clearance margin

- Saved `production_v408_clearance_margin/Character_An_clearance_margin_v408.blend`. Middle/Ring/Pinky MCP/PIP/DIP 48/78/37, 51/81/39, 54/84/41 degrees. Thumb/index unchanged; 1,957 drivers retained.
- Evaluated hand has no string-centerline crossings; conservative minimum surface clearance 1.063 mm, including string radius and half the 0.5 mm sampling step. Static pose only, not strumming/deformation validation. Actual Workbench diagnostic inspected: staggered curl retained.
- V409 cuff boundary flattening was visually rejected: worsened silhouette and did not remove folded/torn-looking geometry. All cuff coordinates restored from `production_v409_cuff_hem/vertices_before.json`, and V408 saved again. Do not resume V409.
- Cuff mesh has 4,253 vertices and two boundary loops (310 at upper join, 220 at wrist); no additional boundary loops suggesting open interior holes. Existing overlapping/folded surface likely needs rebuilding rather than boundary flattening. Ray checks identify `V357_CUFF_PATCH.R` at the defects.
- Startup remains V405. Workspace could not be independently confirmed this increment: default wmctrl lacked DISPLAY and using Blender process display returned no matching title. Existing Blender was not restarted or moved.
- New scripts compile. Next rebuild cuff surface against wardrobe references, improve hand skin and preserve V408 clearance; face, hair, guitar, and animation-quality work remain unfinished.

## Current candidate: V407 unused-finger clearance

- Saved `production_v407_unused_clearance/Character_An_unused_clearance_v407.blend`. Startup remains retained V405.
- Middle/Ring/Pinky MCP/PIP/DIP now 45/75/35, 48/78/37, 51/81/39 degrees. Thumb/index unchanged; 1,957 drivers retained. Original V406 rotations in candidate `pose_before.json`.
- Actual Workbench `v407_pick_diagnostic.png` inspected: unused fingers lifted from strings, wrist continuous. Sleeve holes and synthetic hand skin remain.
- All eight string centerlines clear the evaluated hand in the tested pose. A 0.05 mm sampling check subtracting half the sample spacing and string bevel radius gives minimum conservative surface clearance 0.085 mm (S1), then 0.808 mm (S2). This is a static pose check, not animation clearance. Report: `clearance.json`. Actual Cycles `v407_pick_close.png` completed and visually inspected: static intersections resolved in this view, smooth plastic skin and ragged sleeve still obvious.
- Correction to V406 diagnosis: first-hit-per-segment checks hid Ring/Pinky behind Middle. Enumerating all hits found Middle3, Ring3, Pinky3 on S1 and Middle2/3, Pinky2/3 on S2. Evaluated mesh updates were verified; earlier Middle-only failures did not establish an evaluation bug.
- V406 is rejected for string intersections. V407 is a working static-contact improvement; startup remains V405. Next increase animation clearance margin and improve hand skin and sleeve construction. Character remains unfinished and not photoreal or animation-ready. Both new scripts pass Python compilation. Project directory is not a Git repository, so git diff is unavailable.

## Current retained checkpoint: V405 wrist contour

- Saved `production_v405_wrist_contour/Character_An_wrist_contour_v405.blend`. Startup now targets V405; service backup `.before-v405`, daemon reloaded without restarting Blender. Both Blender windows confirmed on workspace 7 during this increment.
- Reshaped 59 right-hand heel/wrist base vertices, preserving topology and finger geometry. Original coordinates in `vertices_before.json`. Actual Cycles `v405_pick_close.png` inspected: triangular protrusion removed in this view.
- Actual Workbench `v405_open_hand.png` inspected: continuous wrist and no gross hand tears in this open pose. Existing nails are visible when open. All 19 temporary finger-control rotations restored exactly (maximum error 0.0); all 1,957 rig drivers preserved. See `open_pose_check.json`.
- Original V403 weights restored. V404 Multires-before-Armature order retained on both hands: rendered knuckle shape improved, but stack change alone did not fix wrist protrusion. Base-only diagnostic confirmed protrusion in base geometry.
- Scripts: `pipeline/refine_v405_wrist_contour.py`, `pipeline/check_v405_open_hand.py`; both compile successfully. Playing pose restored after diagnostic; saved checkpoint is the playing pose.
- Remaining: overly tight unused-finger curl, quantitative pick/string and finger contact, hand skin/detail, ragged or holey sleeve construction, face likeness and hair. One open pose and one curled view do not establish full animation readiness. Character is not complete or photoreal.

## V404 hand modifier order

- Saved `production_v404_hand_stack/Character_An_hand_stack_v404.blend`; actual render reviewed. Better knuckle definition, wrist protrusion persisted. Retained stack order in V405.
- V403 actual close-up failed to remove protrusion; rejected and all 132 weight changes restored from backup.
- V404 moves Multires before Armature on both hands. All 1,957 drivers preserved.
- Script: `pipeline/refine_v404_hand_stack.py`; exact stack before/after in checkpoint report.

## Rejected experiment: V403 wrist blend

- Saved `production_v403_wrist_blend/Character_An_wrist_blend_v403.blend`; render reviewed and rejected: protrusion persists. Startup remains V401.
- Actual V402 close-up reviewed: pick is shorter, but triangular wrist protrusion remains. Prior cuff-only diagnosis was incorrect: rays at actual protrusion pixels (110,140), (130,150), (150,160) hit the anatomical hand.
- Extended wrist had full DEF-Hand.R weighting up to local z=.045 m. V403 blends hand/forearm weights smoothly across local z=.005 to .075 m for 132 vertices; finger influences and mesh geometry unchanged. Original weights backed up in `weights_before.json`; 1,957 rig drivers verified.
- Script: `pipeline/refine_v403_wrist_weights.py`. Actual `v403_pick_close.png` inspected: protrusion persists. Original weights restored in V404.

## V402 cuff material and pick candidate

- Saved `production_v402_pick_wrist/Character_An_pick_cuffs_v402.blend`; V401 retained. Startup remains V401 until visual review.
- Ray casts at the apparent triangular skin flap in V401 picking close-up hit `V357_CUFF_PATCH.R`, material slot 0, not the hand. Those rays sampled the cuff above the actual protrusion; later V403 investigation corrects this diagnosis. Both cuff outer material slots now use charcoal cotton with fine bump and high roughness. Geometry and skinning untouched.
- Plectrum exposed tip shortened from 22 mm to 15 mm about the existing pinch anchor; width, thickness, bone parenting and negative-axis grip section unchanged. Finger pose untouched, all 1,957 drivers preserved.
- V402 close-up inspected: shorter pick, unresolved triangular wrist geometry, smooth featureless fingers. Cuff material change did not fix protrusion. Script: `pipeline/refine_v402_pick_cuffs.py`. Hand and pick before-data in `before.json`; base posed hand in `base_posed.json`.

## Current: V401 guitar controls and V400 maple perimeter

- Saved: `production_v401_guitar_controls/Character_An_guitar_controls_v401.blend`; V399 and V400 preserved. Startup service now targets V401; prior service backed up as researchos-blender-mcp.service.before-v401 and user daemon reloaded without restarting Blender.
- V400 insets the maple top 2.5 mm using a validated planar buffer, leaving body core, neck, strings, root and pose unchanged. Actual V400 front render reviewed: continuous exposed wood edge without visible cutaway folds. Coordinate backup and inset outline retained in checkpoint directory.
- V401 reduces both control knobs from 31 x 31 x 18 mm to 24 x 24 x 14 mm, preserving their base height. Actual `v401_guitar_front.png` reviewed and retained. Rig retains 1,957 drivers.
- Blender PID 11530 and both windows confirmed on workspace 7. Actual angled close-up `v401_pick_close.png` inspected: triangular skin flap protrudes beneath cuff; fingers lack joint/nail detail; plectrum projects as a long blade. Finger/string surface clearance is not established from this image. Next correct wrist flap and plectrum proportions, then inspect contact from another angle. No hand geometry or pose changed in V400/V401.
- Scripts: `pipeline/prepare_v400_inset.py`, `pipeline/refine_v400_maple_perimeter.py`, `pipeline/refine_v401_guitar_controls.py`, `pipeline/inspect_v401_pick.py`. The preparation script uses Shapely installed only in `/tmp/character-v400-geometry`; generated inset JSON is persistent and Blender needs no Shapely dependency.
- Remaining: hand anatomy/contact, face likeness and skin/eyelids, curl variation, garment construction. This is a working checkpoint, not a completed or photoreal character.

## Current: V399 oral materials working checkpoint

- Saved neutral: `production_v399_oral_materials/Character_An_oral_materials_v399.blend`; earlier checkpoints preserved. Startup service still V394.
- Adjusted oral mucosa, gums and tongue base colors, roughness and subsurface response. Actual `v399_expression_angle.png` reviewed with JawOpen .45 and both smiles .7 from an angled view: more visible interior color/form, lip join remains continuous in this tested pose. V398 angled image also reviewed before the change.
- Remaining visible defects: sharp slit-like eyelid rims, plastic facial surface, stretched sideburn texture, overly regular curls. Mouth and likeness are not final; this is not comprehensive animation validation.
- Neutral save confirmed with 1,957 rig drivers; Blender PID 11530 and both windows confirmed on workspace 7. Both V399 scripts pass Python syntax compilation.
- Scripts: `pipeline/refine_v399_oral_materials.py`, `pipeline/save_v399_neutral.py`; material change report in checkpoint directory. Preserve all 1,957 CloudRig drivers.
- Guitar review: V356 gives V206_FIGURED_TOP the same contour as V206_BODY_CORE. Next test a 2–3 mm inset/rolled maple perimeter while preserving the body core, root, neck, strings and pose. Do not change horn/waist proportions based only on the angled reference: silhouette was traced from a front product image with isotropic calibration. Render the perimeter change before retaining it. Continue hand contact, facial anatomy and garment work.

## Current: V398 lip seam corrected

- Saved neutral: `production_v398_lip_join/Character_An_lip_join_v398.blend`; prior checkpoints preserved. Startup service still V394.
- Fitted lip outer ring to surrounding body surface independently for Basis, JawOpen, Smile.L and Smile.R, with 120 micrometer inward overlap and 30% transition at row 8. All 96 perimeter vertices found body surface for each key. Peak movement .52 mm neutral, .82 mm JawOpen. Inner aperture untouched.
- Actual `v398_neutral.png` and `v398_jaw_open.png` reviewed: curved lower lip-patch line no longer visible in either frontal render; no visible gap in the tested .6 jaw opening. Smile states fitted but not rendered yet.
- Neutral restored and saved with 1,957 rig drivers. Mouth interior remains too dark; anatomical detailing and facial likeness still unfinished. Next: oral interior/side-view expression validation, then guitar contours and hands.
- Scripts: pipeline/refine_v398_lip_join.py and save_v398_neutral.py. Coordinate backup and numeric report in checkpoint folder.

## Current: V397 lip proportions working checkpoint

- Live/saved `production_v397_lip_proportions/Character_An_lip_proportions_v397.blend`; previous V396 preserved. Startup remains V394.
- Broadened vermilion vertically, up to 1.966 mm, with paired upper peaks. Mouth aperture and outer patch boundary unchanged in every shape key; expression deltas preserved within 2e-7 m. All 1,957 rig drivers retained.
- Actual `v397_neutral.png` and `v397_jaw_open.png` visually inspected; JawOpen=.6 separates lips continuously and exposes teeth. This is one frontal pose, not comprehensive animation acceptance.
- Visible defects: curved seam below lower lip (replacement patch perimeter), overly dark oral interior, texture-like beard, synthetic anatomy. Neutral lips fuller but final likeness not achieved.
- `pipeline/save_v397_neutral.py` restores Blink.L/R, JawOpen and Smile.L/R to 0, portrait camera, and saves. No active render after save.
- Next: remove lip patch boundary seam without disturbing expression continuity; improve oral interior; continue face likeness, guitar contour, hand contact and garment construction. Goal remains unfinished.

## Current: V396 lower-lid working checkpoint

- Checkpoint: `production_v396_lower_lids/Character_An_lower_lids_v396.blend`; V395 preserved. Startup service still targets V394.
- Reduced lower aperture arch from 4.15 to 2.2 mm, upper arch now 8 mm. Outer boundary held fixed; closed blink targets unchanged. Eyelid margins and lashes rebuilt to match.
- Actual `v396_front.png` and `v396_halfblink.png` inspected. Less lower sclera in neutral; halfway blink has no gross lid/globe penetration in the frontal image, but a dark sharp rim and artificial smooth lid surfaces remain. This is a working improvement, not animation or photoreal acceptance.
- Neutral-save script: `pipeline/save_v396_neutral.py`; resets both blinks to zero and portrait camera. Keep all 1,957 rig drivers.
- Next: anatomical lid rims and lip proportions against reference, followed by guitar shape and hand intersections. Character remains unfinished.

## Current: V395 facial-hair working checkpoint, 2026-11-03 21:54 PST

- Live/saved: `production_v395_facial_hair/Character_An_facial_hair_v395.blend`. Earlier V394 preserved; startup service still points to V394.
- Added 4,522 short tapered facial-hair fibers, 67,830 vertices, with barycentric body-expression shape keys and DEF-Head parent. Original scan albedo/UV0 used: photo projection deliberately excludes much of beard and gave unsuitable samples.
- Actual `production_v395_facial_hair/v395_front.png` rendered and visually inspected. Modest beard depth increase; still largely texture-like at portrait resolution. Not photoreal or final likeness.
- Direct expression check: JawOpen, Smile.L, Smile.R each .6 produced matching .6 body/hair shape values, then controls restored. This verifies driver coupling, not full deformation quality. All 1,957 rig drivers intact.
- Blender PID 11530 confirmed on workspace 7. Host 21 GiB available, swap 768 KiB. No paid compute. Render completed.
- Scripts: inspect_v395_beard_surface.py, refine_v395_facial_hair.py, check_v395_expression.py. Report in production_v395_facial_hair/expression_check.json.
- Next: facial anatomy/likeness and visible facial-hair refinement; guitar contours and hand contact remain unfinished. Do not treat strand count as quality acceptance.

## Current: V394 neutral checkpoint, 2026-11-03 21:49 PST

Supersedes older live-state notes below. Character remains unfinished.

- Live/saved: `production_v394_eyelashes/Character_An_eyelashes_v394.blend`. Neutral blink 0, eye Dilation .90. 1957 CloudRig drivers verified. One GUI Blender PID 11530 on workspace 7, loopback MCP responsive.
- V391 fixed collar boundary by including center-neck faces with y < .02; previous V390 y < -.035 excluded them. Actual front render confirms smoother continuity. Do not repeat rejected V390.
- V392 enlarged inner iris/cornea 1.18 and contracted pupil with Dilation .90. Neutral checkpoint saved separately.
- V393 rounded lid apertures: upper exponent .52 at 7.45 mm; lower .58 at 4.15 mm; maximum displacement .997 mm. Closed body targets unchanged. Actual open render reviewed.
- V394 added 81 tapered lashes per eye driven by existing blink controls, projected outside facial surface in open/closed states. Lashes remain visually very subtle at preview resolution; do not claim final lash quality. Actual `v394_blink.png` reviewed: closed eyes, no gross exposed globe, tiny seam glint remains.
- Actual `production_v394_eyelashes/v394_front.png` (700 square, 24 samples) reviewed. Collar and iris improvements retained, but eyelids still artificial, beard/mustache largely texture-like, curls too regular. Likeness and photoreal quality not achieved.
- Startup service points to V394; backed up before path edit and daemon-reloaded, not restarted. Workspace 7 confirmed from window inventory. Host had 21 GiB available, zero swap. No paid compute.
- Scripts: pipeline/refine_v393_rounded_lids.py, refine_v394_eyelashes.py, save_v394_neutral.py. Scripts syntax checked; actual Blender MCP execution successful.
- Next substantive work: improve face/lid anatomy and facial-hair volume against reference; inspect guitar body contours and hand contact; garment construction; deformation/animation tests. Preserve rig drivers and older checkpoints. No render currently running after final save.


## Current: V389 reviewed and retained

Updated 2026-11-03 21:38 PST. Supersedes live-state notes below.

- Live/saved: production_v389_surface_ringlets/Character_An_surface_ringlets_v389.blend. Blender PID 11530 on workspace 7; MCP responsive; 1957 drivers intact.
- Actual v389_front.png reviewed: irregular surface-facing ringlets improve repeated edge-on rows. Still not final likeness or production quality.
- V390 collar shader test rendered but did not visibly remove jagged boundary. Rejected; polygon assignments restored and working scene saved back to V389. Do not promote V390. Investigate original texture boundary as well as face assignments next.
- Remaining: neck/collar continuity, eyes and face likeness, clothing structure, guitar contours and hands, deformation/animation validation.
- Startup service points to V389. No new paid compute.

## Active work: V388 cloth preview; V387 guitar and V386 curls reviewed

Updated 2026-11-03 21:33 PST. Supersedes older live-state notes below.

- Live Blender PID 11530 remains on workspace 7; MCP loopback 9876 responds.
  Scene V357_PLAYING_POSE; all 1,957 CloudRig drivers preserved.
- Saved V387: `production_v387_maple_veneer/Character_An_maple_veneer_v387.blend`.
  Actual `v387_guitar_front.png` inspected: irregular gray maple is improved;
  body contours and hand anatomy/contact still need review. Generated maple
  is packed, with source and exact prompt in assets/generated/gray_maple_v387/.
- V386 dense groom saved in production_v386_dense_curls: 127,260 strands,
  2,163,420 points. Actual v386_front.png inspected; no memory-pressure issue,
  but curls are still too uniformly arranged. Superseded grooms removed from
  live scene only after V385 rollback checkpoint. Do not call groom final.
- V383/V383b brows, lip volume, relaxed resting lids and closed blink targets
  retained. V384 CC0 weave maps and V385 generated shirt print retained.
  Face likeness and jagged neck material boundary remain unfinished.
- V388 compresses neutral garment albedo highlights while preserving colored
  buttons/details by saturation. Saved checkpoint:
  `production_v388_cloth_albedo/Character_An_charcoal_cloth_v388.blend`.
  Current render: production_v388_cloth_albedo/v388_guitar_cloth.png.
  Actual render inspected: neutral highlights reduced, brass retained; still
  too smooth and needs seam/weave detail. Retained as working improvement.
- Async renderer pipeline/render_preview_job.py runs 4 CPU threads and leaves
  MCP responsive. Never mutate while bpy.app.is_job_running('RENDER').
  Last host check: 22 GiB available, zero swap. No paid compute started.
- Startup service now points to V388; daemon-reload only, no Blender restart.
- Next: cloth seam/weave detail, irregular curl orientations, face/neck
  continuity, guitar contours and hands, full-body deformation and animation.
  Character is NOT photoreal or production-ready.

## Active work: V379 fabric separation and eye proportions; guitar and expressions next

Updated 2026-11-03 at 15:27 PST. This section supersedes all older live-state
statements below. The character is unfinished and is not photoreal.

- Current saved checkpoint:
  `production_v379_fabric_eyes/Character_An_fabric_eyes_v379.blend`.
  Reuse Blender PID 8713 on workspace 7, loopback MCP port 9876. Scene
  `V357_PLAYING_POSE`, rig `V357_CLOUDRIG_CONTROLS`; all 1,957 drivers retained.
- V374 replaced the eyes with the locally available free procedural eye asset,
  retaining gaze controls and the continuous deformable lids. V376 corrects
  its inversely named Dilation control to 0.75: higher values contract the
  pupil. Actual renders now show brown irises. Eyelid edges and catchlights
  still need refinement; the closed-eye render remains structurally clean.
- V376 replaces the rejected V375 spiky groom with 84,172 tangent-growing
  curl strands, grouped into 3,826 guides. Front and three-quarter Cycles
  renders were inspected: curls now lie close to the scalp. The hairline,
  part and sideburn transitions still need visual refinement. Older grooms
  remain hidden for rollback. Scripts and renders are in the V376 folder.
- V377b projects the fitted V326 photo texture onto a separate UV layer,
  with a corrected lower-face mask that preserves the original mouth/beard.
  Raw V377 has a bad white chin patch: never restore that uncorrected state.
  The donor remains hidden with fake user; do not replace the existing head.
- V378 enlarges the eyelid opening while preserving the closed-eye targets.
  Actual open and closed Cycles renders were inspected; closure is clean.
  V379 reduces iris/cornea width to 78 percent and removes the fill light's
  glossy visibility. Dilation remains 0.75 (larger values contract pupils).
- V379 separates jacket, shirt and pants materials on the existing body mesh,
  preserving skin, buttons and the pen. Actual face and upper-body renders
  are in the checkpoint folder. Clothing still reads too gray/leathery;
  likeness, eyebrows and defined ringlets remain unfinished.
- Next: correct the guitar's high-contrast regular flame shader, then add
  donor-relative brow/smile shapes. A smile must deform body, lip patch and
  cavity rim together; keep dental anatomy on its existing jaw/head parents.
- Preserve V361 hands/cuffs and V356 guitar. Do not regenerate the rig or call
  `animation_data_clear()`. Blender is bounded by MemoryHigh 12 GiB /
  MemoryMax 16 GiB; renders use four CPU threads. No paid Modal job is active.
- Face likeness, skin detail, eyelid anatomy, wardrobe materials, hand detail,
  full-body visual checks and animation validation remain unfinished.
- The Codex routing timeout recovered: account/read succeeded in 1.64 seconds
  and `codex resume` reached its picker in 11.13 seconds. No auth or launcher
  change was needed. Revisit only if a new failure occurs.

## Historical V369 continuous eye sockets

Updated 2026-11-03 at 07:03 PST. This section supersedes the older live-state
statements below. The character is unfinished and is not photoreal.

- Current saved checkpoint:
  `production_v369_socket_retopology/Character_An_socket_retopology_v369.blend`.
  Reuse Blender PID 110054 on workspace 7, loopback MCP port 9876. Scene
  `V357_PLAYING_POSE`, rig `V357_CLOUDRIG_CONTROLS`, all 1,957 drivers preserved.
- V362 added actual eye geometry and gaze controls. V364 added a mouth
  interior and JawOpen shape. Basis, JawOpen, Blink.L and Blink.R are retained.
- V369 replaces the folded scan triangles around both eye openings with a
  regular annulus joined to the surviving scan. Continuous lid rows deform
  with the blink controls. Actual neutral and closed-eye clay renders show
  the torn outer joins are gone. Script: `pipeline/repair_v369_socket_retopology.py`.
- Textured front, three-quarter and blink renders are in the V369 directory.
  They are diagnostic, not final quality: blink UV color stretches into a
  flat patch, eyelids and iris presentation need refinement, complexion is
  too pale, and the baked hair still resembles gray molded waves.
- Next: build a compact black curl groom on the actual current scalp surface,
  preserving the character-left side part and forehead/ear boundaries from
  `references/facial/head_expression_sheet_v2_face_refined.png`.
  The V367 scalp export has old vertex indices; re-export or map coordinates.
- Preserve V361 hands/cuffs and V356 guitar work below. Do not regenerate the
  rig or call `animation_data_clear()`. Blender remains limited to one CPU
  thread, MemoryHigh 8G / MemoryMax 10G, and no paid Modal job is active.
- The Codex routing timeout recovered earlier in this continuation:
  account/read succeeded in 1.64 seconds and codex resume reached its picker
  in 11.13 seconds. No auth or launcher change was needed.

## Historical V361 picking grip and cuffs; V362 facial anatomy

Updated 2026-11-03 at 04:36 PST. This section supersedes the older live-state
statements below. The character is unfinished.

- Current saved checkpoint:
  `production_v361_pick_cuffs/Character_An_picking_grip_cuffs_v361.blend`.
  The scene and character object names still use the V357 prefix. Reuse Blender
  PID 110054 and its loopback MCP bridge on workspace 7; do not start another.
- V356 rebuilt the guitar outline from the supplied Strandberg photograph,
  with grayburst materials, pale fretboard, eight strings and multiscale frets.
  V357 integrated it and posed both arms with the existing CloudRig controls.
- V358 fitted a left-hand E-minor voicing (A7 D9 G9 B8, high E open). Actual
  evaluated FK endpoints agree with the solver within 0.0002 mm. The correct
  finger parent transform is IK-Hand, not the raw six-segment DEF-Hand matrix.
- V359 removed severe automatic-weight leakage between adjacent fingers on
  both CC0 hand meshes. All 831 vertex weights per hand normalize to one;
  original weights and durable rest/control exports are in the V359 directory.
  `pipeline/repair_v359_hand_weights.py` reproduces the repair. Four actual
  Workbench renders were inspected: the fused central finger bulge is gone.
- V360 separates the fretting ring/little fingers and moves the thumb behind
  the neck; only one sampled vertex remains inside the conservative neck box.
  V361 fits the picking thumb/index to a separate nylon pick. Minimum sampled
  thumb/index surface clearance is 0.648 mm; this is not a whole-hand collision
  test. The pick follows a 2-degree wrist rotation by 1.9999 degrees.
- V361 restores and tapers both textured cuffs, removes disconnected cuff
  fragments, and adds a 12 mm wrist transition with blended forearm weights.
  Actual front, side and fretting views were inspected. The guitar selector's
  erroneous parent offset is also fixed. Scripts: `finish_v361_grip.py` and
  `checkpoint_v361_inspect_face.py`; reports and renders are in the V361 folder.
- Hands still need skin detail and knuckle refinement; a flat shaded wrist
  transition remains visible inside the picking cuff. Do not repeat the old
  38 mm wrist extension or apply the superseded V361 thumb fit.
- V362 head close-ups and `head_geometry.json` are exported. The face is still
  a textured closed Tripo surface. Fit real eyes, deformable lids and a mouth
  interior to the actual face landmarks; generic face-bone coordinates are
  wrong for this mesh. Then groom, likeness, final materials and animation.
  The asset is not photoreal or production-ready. Preserve all 1,957 CloudRig
  drivers; never call `animation_data_clear()` on the rig.
- The Codex routing timeout recovered: account/read succeeded in 1.64 seconds,
  and fresh `codex resume` reached its picker in 11.13 seconds. Do not repeat
  that diagnosis without a new failure. No new paid Modal job is active.

## Historical V354: control drivers restored

Updated 2026-11-03 at 02:54 PST. This section supersedes live-state statements
in the historical sections below. The character is unfinished.

- Current saved checkpoint:
  `production_v354_rig_driver_repair/Character_An_CloudRig_drivers_v354.blend`.
  Live scene `V354_CLOUDRIG_DRIVERS`, rig `V354_CLOUDRIG_CONTROLS`.
  Reuse Blender PID 110054 and its loopback MCP bridge; no second instance.
- V353 restored the damaged cuffs from the original textured V350 source,
  welded local UV-seam boundaries, and added an inner hem. Preserved checkpoint:
  `production_v353_cuff_repair/Character_An_CloudRig_cuffs_v353.blend`.
- A wrist deformation check exposed missing CloudRig drivers: V351 and V352
  scripts called `animation_data_clear()`, deleting the generated IK/FK drivers.
  Those scripts now detach only the action. V354 regenerated 1,957 drivers,
  preserving the original finger action, bindings, and all deform rest heads
  (maximum rest-head change zero). No fatal generator warnings; missing facial
  actions remain unresolved.
- Direct V354 mesh tests passed for both hands: finger-curl maximum movement
  91.05/90.63 mm, wrist maximum movement 66.94/66.94 mm, driven wrist-tail
  movement 20.63 mm each. Measurements are in world space. Six actual Workbench
  images and `hand_deformation_report.json` are in the V354 output directory.
  The earlier V353 wrist images used an inactive control path and are invalid
  as deformation evidence; V354 supersedes them.
- Visual review: cuffs are substantially more coherent; a wrist shading seam,
  overly rounded curled knuckles, and unfinished skin detail remain. These
  diagnostic renders do not establish photoreal quality or guitar contact.
- Next: append only the V342 `V206_GUITAR_ROOT` hierarchy, preserving its world
  transform initially; exclude the legacy character. Fit the new body's arms
  and fingers to the real fretboard, then refine deformation. Face anatomy,
  facial skinning, groom, reference likeness, and final materials remain open.

### Host recovery update

The residual-swap launcher rejection was corrected in ResearchOS: occupied swap
alone no longer fails the default health gate; active pressure checks remain.
A fresh 2026-11-03 sample showed about 18 GiB available RAM and 2.3 GiB occupied
swap. No swapoff or cache purge was used. Both other CLI project sessions were
working at the last check. A subsequent `workspace routing discovery timed out`
startup error recovered: direct `account/read` succeeded in 1.64 seconds and a
fresh routed `codex resume` reached its session picker in 11.13 seconds. No auth
or launcher changes were needed for that transient failure. Do not infer the
current governor or desktop-app state from the older incident notes below.

## Historical V352 download and host incident

Updated 2026-11-03. This section supersedes the V350 live-session details below.
The character is unfinished and is not close to final delivery.

- Current local checkpoint:
  `production_v351_cloudrig_fingers/Character_An_CloudRig_hands_before_modal_v351.blend`.
  It contains only scene `V351_CLOUDRIG_HANDS`, retaining the bound body and two
  Blender Studio CC0 anatomical hands. Existing checkpoints remain preserved.
- V351 binds all hand vertices to individual finger bones, but the left finger
  bend axes are wrong. The right curl works better. Both cuffs need cleanup.
- Remote repair and inspection scripts: `pipeline/repair_v352_finger_axes.py`
  and `pipeline/modal_process_v352.py`. The worker regenerates CloudRig on Modal
  CPU, then renders four hand views on an L4. Local processing is only the client
  and file transfer. Run status is in
  `production_v352_modal_finger_repair/modal_run.json` and `modal_run.log`.
- Completed attempt: `ap-wVYXCRF6JHuHbuT2dckqmz`, profile `research`, workspace
  `snorkelai`. Both repaired blend files and four Cycles previews were saved to
  volume `character-asset-an`, directory
  `/processing/v352_71e3337bbd2b2a7f_bec1af88`. The earlier attempt
  `ap-4FLvCr1mwDlJr2EVzH6F0j` failed an overly strict absolute fingertip-distance
  threshold; the retry reused the uploaded input and used a chain-relative check.
  No new render or upload is needed to recover these outputs.
- All four previews were downloaded and visually inspected at 01:09 PST.
  Fingers now curl toward the palms on both sides, but the curled silhouette
  remains rounded and needs deformation refinement. Hands still lack skin detail;
  jacket cuffs have conspicuous jagged openings. These are diagnostic previews,
  not accepted final-quality hands or verified guitar contact.
- The download completed at 01:21 PST: the rest blend is 34,542,704 bytes and
  the posed blend is 34,545,999 bytes, with all four PNGs and the render report
  present. The Modal client exited successfully. V352 has not yet been opened in
  the live Blender session, which remains on V351.
- The downloader now retrieves previews first and uses atomic `.part`
  replacement for future runs. Do not rerun paid processing just to download.

### Host recovery and containment

The user's three other sessions were frozen by the pressure governor, including
when live memory PSI was zero: the health check rejects swap above 25% and the
governor labels that failure `memory_pressure`. The governor service was stopped
temporarily, and these exact scopes were thawed without terminating their processes:

- `researchos-codex-researchos-unicont-8312.scope`
- `researchos-codex-researchos-cli-1-8083.scope`
- `researchos-codex-app-8148.scope`

All three were directly verified at `cgroup.freeze=0`, with advancing CPU usage
and zero OOM events. `researchos-codex-governor.service` is inactive but remains
enabled; starting it with swap above 25% or available RAM below 12 GiB can freeze
the sessions again. No permanent governor configuration was changed. Existing
per-session memory limits remain in place.

Blender PID 110054 was saved/reloaded into the compact V351 checkpoint, reducing
its RSS from about 4.8 GiB to 2.9 GiB. Its actual Snap scope is
`snap.blender.blender-408ce495-348f-485c-9335-3253dc77d30c.scope`; runtime limits
were applied there because the Snap child escaped the launcher's original scope:
CPUQuota=100%, MemoryHigh=8G, MemoryMax=10G, MemorySwapMax=2G, IOWeight=25.
These are live containment, not a persistent launcher fix. Blender is kept in
solid preview with one render thread and no ongoing local render. Reuse its
existing loopback MCP connection; do not launch another Blender instance.

The post-recovery host sample showed 20 GiB used, 15 GiB available, and 3.4 GiB
swap occupied. Occupied swap did not fall to zero; no swapoff or cache purge was
performed. Keep further heavy rig generation and rendering on Modal.

At 01:21 PST, a separate Terminal 2 crash was traced to the UniCont scope's
384-task limit: `pids.peak=384` and `pids.events max=45`. Its Android emulator
and networking helper account for about 166 threads. The Codex frontend and
backend still exist, but the displayed turn contains thread-spawn and event-loop
panics. No task-limit change or session restart has been performed. A proposed
bounded recovery is a runtime-only TasksMax increase to 512 for that exact scope,
followed by recovery of the stalled turn while preserving its history.

The Codex desktop app's stuck Send action has no recorded cgroup task-limit
denials and remains unresolved. Its backend still handles requests. A private
backup of the saved composer state and the UniCont pane transcript is at
`/home/ajuntanaga/.local/state/researchos/recovery/codex-stall-20261103-012100/`.

## Current checkpoint: V350 Tripo character with CloudRig body

This section supersedes the historical V211/V212 status below. The project is
still unfinished; the user has not accepted this candidate as the final asset.

- User-supplied source: `/home/ajuntanaga/Downloads/tripo_model_d1b7f249-d40b-4b1f-843d-2d35c6ac59b8_meshopt.glb`.
  It contained four turnaround figures in one mesh. Figure 4 is the current
  1.8 m character candidate, with its original packed 8192 px texture.
- Correct textured source: `production_v349_tripo_rig_candidate/Character_An_Tripo_candidate_v349.blend`.
  Do not use the old V348 character file for textures: it predates the UV write
  fix (`foreach_set`, not `foreach_get`). The V349 candidate has the corrected UVs.
- Rest body rig: `production_v350_tripo_cloudrig_body/Character_An_CloudRig_body_v350.blend`.
- Posed body rig: `production_v350_tripo_cloudrig_body/Character_An_CloudRig_body_pose_v350.blend`.
- Live scene: `V350_TRIPO_CLOUDRIG_BODY`; character
  `V350_TRIPO_CHARACTER_BODY_BOUND`; controls `V350_CLOUDRIG_CONTROLS`.
  Reuse the existing Blender process and loopback MCP bridge on workspace 7.
- Free rig toolkit: official Blender Studio CloudRig 2.2.31, installed and
  enabled as `bl_ext.user_default.cloudrig`. Download and license are under
  `third_party/cloudrig/`. Reusable generated Sintel controls are saved in
  `production_v348_tripo_figures_cloudrig/CloudRig_Sintel_Control_Rig.blend`.
- V350 has 253,390 vertices and 488,984 triangles. Body skinning was transferred
  from a 12 mm voxel proxy using 31 body deformation bones; zero vertices are
  unweighted. This does not establish production topology or finished weights.
- Native CloudRig chain flattening corrected the arm and leg IK axes. For a
  thigh chain the repair must use `limit_count=4` because CloudRig drops the toe
  after limiting the chain. There are no remaining arm/leg IK warnings.
- Remaining generator warnings: 16 missing facial action constraints and one
  bone color warning. The face and individual fingers are not skinned yet.
- `V350_Body_Control_Test_2s` keys animator FK forearm and head controls at
  frames 1/24/48 (24 fps). Frame 24 moves both hands forward. Actual Modal Cycles
  front and three-quarter renders were inspected: no obvious shoulder/elbow
  collapse in this modest pose. This is not a full motion/deformation approval.
- Render evidence: `production_v350_tripo_cloudrig_body/renders/v350_modal_cycles_asset_front.png`
  and `v350_modal_cycles_asset_three_quarter.png` in the same directory.
  Modal run `ap-SOfYMwoMn7jvrotsXv8zGf` completed; its cleanup warning occurred
  after both PNGs were saved. No render job remains active from this batch.
- Reproduction scripts: `pipeline/fit_v350_tripo_cloudrig.py` and
  `pipeline/pose_v350_cloudrig_body.py`. The pose script repairs generator
  warnings before saving rest and posed checkpoints.

### Located generator

Tripo 3D for Blender v0.7.3 is installed at
`/home/ajuntanaga/.config/blender/5.2/scripts/addons/tripo-3d-for-blender`
and was confirmed enabled in the live Blender session. Files are dated
2026-11-01. Its UI is `View3D > Sidebar > Tripo 3D`; its client calls
`https://api.tripo3d.ai/v2/openapi`. This is an online generation integration,
not evidence of local model inference. Earlier bounded searches missed this
legacy add-on directory. Do not repeat the conclusion that no generator is
installed. No new generation was started in this pass, and the V350 scene's
API-key property was confirmed empty. The saved workstation credential must
not be printed or embedded into project files. Paid generation needs its own
authorization; the supplied GLB is already available for local work.

### Next work

Fit and skin individual fingers, build a usable face with separate eyes and
mouth anatomy, and replace the solid textured hair with a groom. Dense generated
topology needs cleanup/retopology for reliable facial and hand animation. Then
bring this candidate into the preserved guitar scene and redo instrument contact
against the new body. Guitar shape, fretboard hand contact, reference likeness,
and final photoreal material quality remain open. The current renders also have
a visible background horizon that should be removed for presentation.

## Historical checkpoints

## Current production lineage

The earlier V202-V210 procedural character is retained as technical reference,
not as the production character foundation. The user rejected its likeness and
visual quality. Do not describe V210 as photoreal or film-ready.

- Accepted clean base: `production_v211_clean_base/Character_An_clean_base_v211.blend`
- V211 SHA-256: `6f2693049a35217ba7f51bb9c8fc4c1d78fea7220d296fc5541614c44e437e3d`
- Source: Blender Studio Human Base Meshes v1.4.1, `Body Male - Realistic`, CC0.
- V211 validation: `V211_CLEAN_BASE_OK`; 10,582 vertices, 10,590 polygons,
  UVs and Multires preserved, real height 1.800075 m.
- V211 visual evidence:
  `production_v211_clean_base/delivery/v211_alignment_contact.png`.

## Active identity and look-development work

- Active identity file: `production_v212_identity/Character_An_identity_v212.blend`
- Current build marker: `V212_IDENTITY_CANDIDATE_V3_BUILT`.
- Current SHA-256: `e9d69ca88a57eb7c1f392b1efad781256bc820aa78b74168cb92331f9c20f8e3`.
- Structural validation covers topology, Multires, landmarks, and nine renders;
  it does not prove likeness.
- Candidate v1 and v2 were preserved under
  `production_v212_identity/audit/rejected_candidate_v1/` and
  `production_v212_identity/audit/rejected_candidate_v2/`.
- V3 has a less heroic body, fuller neck, cheek-led face width, less pinched
  eyes, more projected broad nose, fuller lips, and broader shorter chin. It is
  still awaiting a reference-comparison acceptance gate.

V213 is diagnostic, not accepted:

- `production_v213_surface_groom/Character_An_surface_groom_v213.blend`
- It proves the new topology can carry skin, explicit iris/pupil geometry, and
  attached curve groom systems.
- The current scalp substrate and curve distribution still read too much like
  a cap/fringe and are not production quality. Replace or substantially refine
  them before accepting V213.

The analytic morph route is near its likeness ceiling. The supplied front,
three-quarter, and profile sheets are suitable for a landmark/photo-fitting
tool. KeenTools FaceBuilder is the preferred next identity experiment, but its
installation requires accepting a third-party EULA and activating a 15-day
trial when a FaceBuilder head is created. Do not accept that agreement or
activate the trial without explicit user authorization. Its official guidance
also recommends an official Blender.org build rather than the current Snap
runtime.

## Continue with Blender MCP

The canonical service is `researchos-blender-mcp.service`; it keeps the bridge
on `127.0.0.1:9876`. Its configured startup file still points to V210 because
V211+ has not passed the identity/look-development gate. Do not restart the
current Blender merely to change that target.

The live Blender window was verified on user-visible Workspace 7 in
`/run/user/1000/researchos-workstation/window-inventory.json`. Use the existing
process and bridge; do not launch a second Blender.

Primary scripts:

- `pipeline/build_v211_clean_base.py`
- `pipeline/tests/blender_validate_v211.py`
- `pipeline/build_v212_identity.py`
- `pipeline/tests/blender_validate_v212.py`
- `pipeline/build_v213_surface_groom.py`

Execution plan:

- `docs/superpowers/plans/2026-10-10-v211-production-rebuild-recovery-plan.md`
- `docs/superpowers/specs/2026-10-03-character-asset-photoreal-rebuild-design.md`

FaceBuilder was explicitly authorized on 2026-10-11. The official KeenTools
2026.3.1 add-on is installed and enabled in Blender 5.2, its EULA acceptance is
persisted, and the trial has not yet been activated because the native Core
Library is still downloading. The authoritative facial sheet has been split
into deterministic neutral front, left-three-quarter, and left-profile plates
under `production_v212_identity/facebuilder_refs/`; see its `manifest.json`.

Downloaded add-on package:

- `third_party/keentools/packages/keentools-2026_3_1-for-blender.zip`
- SHA-256: `2dd4d9fd11bba69b1c9ffc346cf08e2f109f99ff203e89f6b2bdfc4df0b9e451`
- ZIP integrity passed.

The vendor download certificate expired on 2026-10-10, one day before this
installation. The package was fetched from the official URL after recording
certificate SHA-256 fingerprint
`71:4D:59:28:BB:CF:A9:70:14:BD:63:53:E1:CD:B0:D4:19:A4:70:DA:41:E7:3A:93:42:E9:5E:DC:E3:D2:98:36`.
The Core download completed at
`third_party/keentools/packages/keentools-core-2026_3_1-linux.zip`. The host
reported an exact total of 146,529,549 bytes; ZIP integrity passed and SHA-256
is `8448a617e0181a9a86cd235d5c0f17d98ba4bb3801147e5987e7a3190d375ae3`.
KeenTools' own filename parser unexpectedly requires dotted versioning, so
`keentools-core-2026.3.1-linux.zip` is a hardlink to those same verified bytes.
Core installation passed as `PYKEENTOOLS_OK`, version 2026.3.1.
The supported official Blender 4.5.14 fallback download is intentionally
paused (its partial file is preserved) while bandwidth is prioritized for the
Core, because the add-on already passes its basic checks in live Blender 5.2.

The reference-fit automation ran successfully at
`pipeline/build_v215_facebuilder_identity.py`. It creates one FaceBuilder head,
adds the authoritative front/profile/three-quarter neutral plates, runs face
detection and preset-pin solving on all three, records the source paths and pin
counts, and saves
`production_v215_facebuilder_identity/Character_An_facebuilder_identity_v215.blend`.
The approved trial is now active. V215 contains an 18,024-vertex head with
26/12/23 pins for front/profile/three-quarter. The saved file SHA-256 is
`9ac7c0ef137fbc276c7c9f181ecc63726da973d591b744fffe08ed9db297dd04`.

V216 is the first body-conformation candidate:

- `production_v216_conformed_character/Character_An_conformed_v216.blend`
- SHA-256: `9c1fd1b1922302fac5738c8732158a8ad0d0af31d3f1bf0b6931df4bc93dcbc4`
- It scales/aligns the FaceBuilder head to the V212 crown/nose/chin landmarks,
  keeps a wardrobe-covered neck overlap, and adds provisional eye geometry.
- Direct bone parenting reset the fitted transform and was rejected; the
  repaired candidate intentionally leaves final rig attachment pending.
- Visual gate:
  `production_v216_conformed_character/delivery/v216_identity_conformation_contact.png`
- Manifest: `production_v216_conformed_character/audit/v216_manifest.json`
- V216 is not accepted as final likeness. Without reference hair, beard,
  brows, skin texture, and final eyes it remains visibly generic; the body cut
  edge is intentionally unresolved until the shirt/jacket collar is conformed.

V214 body-rig candidate:

- `production_v214_rig/Character_An_rig_v214.blend`
- 706 generated Rigify bones, 73 active body deform bones, 73 normalized
  regional vertex groups, and a 40-frame deformation action.
- Heat weighting was rejected after visible cross-limb collapse. The current
  deterministic region-gated nearest-segment weights remain stable, but the
  shoulder/elbow deformations still require correction and visual acceptance.
- Dual-quaternion volume preservation is now enabled. It reduced volume loss
  in the regenerated pose, but the elbow/axilla result remains rejected.
- Diagnostic renders are under `production_v214_rig/renders/deformation/`.

Next gate: build the reference-matched groom/beard/brows and physically based
skin/eye look on V216, conform the shirt and jacket collar over the neck seam,
then attach the head/eyes/groom to the Rigify head chain with a transform-safe
constraint and rerun deformation tests. Continue refining V214 weights in
parallel; do not accept the present shoulder/elbow deformation as final.

## Protected technical reference

Preserve the V206 guitar and M3 contact mapping as technical evidence only:

- index S5/F9;
- middle S4/F10;
- ring S7/F9;
- pinky S8/F11;
- fingertip pads 18% behind the fret wire;
- contacted strings depressed 1.85 mm;
- thumb behind the neck.

V192, V200, and V205-V210 remain immutable rollback/reference checkpoints.

## 2026-10-11 continuation: V217-V221

- V217 added the first reference-shaped curl groom, beard/brows, skin response,
  and eye geometry. Its silhouette improved, but the dense curve groom, needle
  stubble, duplicate brows, and eye placement were visually rejected.
- V218 imported the old V205 wardrobe blockout. Large gaps, oversized boots,
  and rigid pieces made it a rejected diagnostic only.
- V219 replaced that blockout with continuous body-derived shirt, open jacket,
  trousers, boot shells, collar, lapels, pockets, placket, and buttons. It is a
  usable topology/layout candidate, not a final wardrobe: tailoring, floral
  textile, lapels, pockets, and footwear remain below film quality.
- V220 successfully baked the three solved FaceBuilder plates to a 4096 square
  reference texture and saved
  `production_v220_face_texture/Character_An_face_texture_v220.blend`. The bake
  materially improved likeness but exposed duplicate facial hair and bad eyes.
- V221 hid the rejected strand beard/brows, aligned and reduced the eyes to the
  solved landmarks, reduced groom strand thickness, and saved
  `production_v221_identity_cleanup/Character_An_identity_cleanup_v221.blend`.
  Its front and three-quarter likeness are the current identity baseline. It is
  still not final: hair volume/strand breakup, profile texture seams, neck
  transition, eye wetness/eyelids, and wardrobe all require further work.

Current next gate: rebuild the curl groom over a fitted scalp cap, remove the
profile/neck projection artifacts, create a real eyeball/cornea/tearline setup,
then make the accepted head assembly follow the Rigify head chain without a
transform reset. After that, correct shoulder/elbow weights, tailor wardrobe,
and integrate the V206 guitar/contact mapping with visible deformation tests.

## 2026-10-12 continuation: V222-V229

- V222 tested a fitted upper-head scalp cap plus sparse curl layer. The cap read
  as a rubber helmet and is rejected; V221 remains the groom/identity baseline.
- V223 transform-safely bone-parented the fitted head, eyes, irises, pupils,
  and both groom layers to the Rigify `head` control. Neutral and plus/minus
  18-degree yaw renders prove the complete assembly follows the rig without a
  transform reset. This attachment is accepted.
- V224 appended the independently validated V206 guitar collection. The first
  standalone transform was visibly oversized/misaligned and was rejected.
- V225 placed the guitar at character scale across the lower torso with a
  playable neck angle. This is the current instrument-transform baseline.
- V226 moved the Rigify hand IK controls, but used the wrong blend convention;
  `IK_FK=1` selected FK in this generated rig.
- V227 corrected both arms to `IK_FK=0`. The controls and DEF hands respond,
  but the real pose exposed the existing V214 shoulder/elbow weight collapse.
- V228 added armature modifiers with dual-quaternion preservation to the five
  body-derived V219 garment shells and bone-parented rigid shirt/jacket details.
  Garments now follow the rig. V228 is the current live checkpoint.
- V229 attempted destructive regional nearest-segment arm reweighting. It
  produced holes/unweighted sleeve regions and is rejected. Do not continue
  from V229.

Current live file:
`production_v228_garment_rig_coupling/Character_An_garment_rig_v228.blend`.

Next gate: preserve the V228 full weight field and repair shoulder/elbow
deformation non-destructively (smooth/data-transfer or a corrected source-body
weight solution). Once the arm pose is visually stable, solve the protected
V206 contact mapping on the fretting fingers: index S5/F9, middle S4/F10, ring
S7/F9, pinky S8/F11, pads 18 percent behind the fret wire, 1.85 mm string
depression, thumb behind neck. Do not accept V227/V228 arm deformation as final.

## 2026-10-12 continuation: V230-V240 clean-rig pivot

- V230 reduced the V214 performance-pose amplitude, but the shoulder/elbow
  collapse persisted. It is rejected along with V229.
- V232 proved a useful hybrid architecture by placing the accepted V221
  FaceBuilder identity on the older V198/V197 performance body. It established
  that the identity can be combined with a stable performance rig, but the old
  body, wardrobe, and hands remain visibly below the target quality.
- V233-V235 tested direct, axis-corrected, and landmark-similarity V206 guitar
  transforms. The source/target pickup layouts are not metrically equivalent;
  those intermediate transforms are rejected.
- V236 retained the solved guitar orientation, fixed scale at 0.92, and anchored
  the V206 body center to the old validated performance guitar. This is the
  accepted instrument placement reference, not a final character scene:
  `production_v236_guitar_body_anchor_fit/Character_An_guitar_body_anchor_v236.blend`.
- V237 integrated the validated V207 fretboard-contact construction directly
  under the fitted V206 root. Its audit records exact index S5/F9, middle
  S4/F10, ring S7/F9, pinky S8/F11 world contacts, 1.85 mm depression, and a
  behind-neck thumb. The visible capsule/sphere construction is rejected for
  final rendering, but V237 is now the authoritative guitar/contact reference:
  `production_v237_exact_contact_hand/Character_An_exact_contact_hand_v237.blend`.
- V238 converted those contact coordinates into one continuous implicit hand
  surface and produced an isolated guitar/contact render. It proves the contact
  topology can be represented continuously, but the silhouette is still a
  pose-specific technical proxy rather than an animation-quality hand:
  `production_v238_continuous_fretting_hand/Character_An_continuous_fretting_hand_v238.blend`.
- A read-only checkpoint inventory confirmed there is no stronger existing
  drop-in body/wardrobe/rig. The correct production body is the untouched CC0
  V211 realistic human base; V198 remains motion reference only, and V205/V219
  remain wardrobe design/layout references only.
- V239 restarted deformation from V211 and restored Blender's native automatic
  weights on the untouched separated A-pose instead of V214's failed
  nearest-segment field. Rigify generated 706 bones, 73 deform bones, and 73
  vertex groups. Neutral, front-pose, and three-quarter renders show coherent
  shoulders, elbows, wrists, fingers, torso, hips, knees, and feet. This is the
  accepted body-rig foundation:
  `production_v239_clean_auto_rig/Character_An_clean_auto_rig_v239.blend`.
- V240 masked the generic V211 head above the collar line and transform-safely
  attached the V221 FaceBuilder head, eyes, pupils, irises, and groom to the
  V239 Rigify `head` control. Front and plus/minus 18-degree yaw renders prove
  identity scale and head following. The jagged body cutoff is intentionally
  unresolved until the fitted shirt/jacket collar is rebuilt:
  `production_v240_identity_clean_rig/Character_An_identity_clean_rig_v240.blend`.

Current live file:
`production_v240_identity_clean_rig/Character_An_identity_clean_rig_v240.blend`.

Current architecture decision: V240 is the production character foundation;
V237/V238 remain the protected guitar/contact authority. Do not return to V214
weight repair or treat the V198 hybrid as the final body.

Next gate: rebuild the V205/V219 shirt, open jacket, trousers, and boots against
the V240 clean body; the collar must cover and soften the current neck cutoff.
Then append the V206 guitar using the V236 transform, pose V239 controls toward
the V237 exact-contact landmarks, and replace the pose-specific V238 hand proxy
with the actual V211 hand deformed by Rigify finger controls. After that, run a
full-body performance deformation matrix and close the groom/skin/eye lookdev.

## 2026-10-13 continuation: V241-V250 performance rebuild

- V241-V243 established body-derived rigged wardrobe, collar/lapel details,
  trousers, and explicit Chelsea-boot assemblies. These remain structural
  blockout quality, not film-ready tailoring.
- V244 appended the protected V236 V206-guitar assembly without changing its
  solved root transform.
- V245 placed both arm IK controls into a readable two-hand playing pose.
- V246 proved sub-millimeter Rigify bone-tip contact, but visual review rejected
  it because unconstrained finger twist collapsed the integrated body hand.
- The underlying V239 metarig fitting bug was repaired by mapping immutable
  stock joints and explicitly fitting the downward A-pose arm/hand chain. This
  fixed the arm placement, but the integrated V211 finger skin still tears
  under large curls; do not use it for final fretting.
- V247's hinge-only solve preserved bone anatomy but confirmed the integrated
  hand weight/topology failure. V247 is diagnostic only.
- V248 replaced the integrated fretting hand with the bundled CC0 realistic
  hand topology, masked the old hand, and removed 1,406 A-pose fingertip
  vertices that had accidentally entered the trouser shell. The durable V241
  generator now also constrains trousers to the central lower-body envelope.
- V249 surface-contact and exclusive-weight experiments are rejected. They
  respectively exposed the legacy-skeleton mismatch and created hard weight
  boundaries.
- V250 creates a dedicated 16-deform-bone hand armature fitted to the actual
  realistic-hand centerlines and parents it to `DEF-hand.L`. Neutral and flex
  renders show continuous rounded fingers with no tearing or spikes. This is
  the accepted hand-rig architecture checkpoint:
  `production_v250_dedicated_hand_rig/Character_An_dedicated_hand_rig_v250.blend`
  SHA-256 `9c962d2fca5192a58fa5a5a4c6f8615b1709c4d18f12e4053b98f85a402e3ad6`.

Current live file:
`production_v250_dedicated_hand_rig/Character_An_dedicated_hand_rig_v250.blend`.

Next gate: solve the V250 dedicated finger controls to the protected V237
surface targets, with rendered pad/string/fret contact as the acceptance test;
then build the picking-hand pinch/bridge pose. After hand contact is accepted,
replace the blockout wardrobe/boots with reference-grade tailoring and materials,
finish skin/eyes/groom lookdev, and run full-body deformation and animation tests.

## 2026-10-13 continuation: V251-V254 contact-solver correction

- V251 is rejected. Direct bone-tip fitting reached numerical targets by using
  extreme digit rotations and produced visibly stretched, implausible fingers.
- V252 is rejected. Moving the wrist first improved several target distances,
  but it still optimized bone tails rather than the evaluated skin pads; front
  renders showed isolated fingertip regions piercing through the fretboard.
- V253 added evaluated-surface contact measurement. It verified the correct
  measurement layer and reached 0.245 mm on the middle pad, but the inherited
  hard-coded wrist placement left 16.65 mm index error and 51.32 mm thumb error.
  V253 is diagnostic only.
- V254 jointly optimized wrist translation/orientation before conservative
  local digit refinement. It reached 0.081 mm middle and 0.614 mm ring error,
  but index remained 23.35 mm and the front silhouette is still anatomically
  unacceptable. V254 is diagnostic only; do not promote it.
- The accepted checkpoint remains V250. Its shared hub hierarchy and automatic
  weights are sound; the current blocker is landmark/pose solving, not broken
  parenting or a torn hand mesh.

Current live file:
`production_v254_joint_wrist_contact/Character_An_joint_wrist_contact_v254.blend`
(diagnostic scene; reopen V250 before the next production attempt).

Next ten-phase sequence has begun:

1. Correct fretting-pad landmark selection and wrist-first anatomical solve.
2. Validate pad/string/fret contact and behind-neck thumb from front, oblique,
   and player-side cameras; promote only an intact silhouette.
3. Build and validate the dedicated right-hand/picking-hand rig.
4. Pose pick grip, wrist angle, palm clearance, and bridge/string relationship.
5. Replace blockout jacket/shirt/trousers with reference-fitted garment topology.
6. Add seams, hems, lapel/collar construction, thickness, and deformation tests.
7. Rebuild boots and material response to reference quality.
8. Finish skin, eyes, teeth/mouth, facial hair, scalp, and groom lookdev.
9. Add facial controls and expression/deformation validation for show animation.
10. Run body/hand/face performance clips, collision checks, final lighting, and
    reference-sheet turntable/contact renders.

## 2026-10-13 continuation: V255-V256 pad landmark correction

- A weight-field audit of all 831 vertices proved the previous thumb landmark
  `695` was not a thumb pad: it carries index-chain influence and sits near the
  index base. This invalidated the earlier 52 mm thumb-error interpretation.
- V255 selected and rendered weight-derived distal pad landmarks directly on
  the accepted V250 mesh: index 234, middle 211, ring 14, pinky 225, and
  thumb-back 286. The front marker render confirms the four colored targets sit
  on the fingertip pads. V255 is a landmark-validation scene, not a production
  pose.
- V256 reran evaluated-surface fitting with those corrected landmarks. The
  thumb error dropped from 51.32 mm to 3.04 mm, middle reached 0.198 mm, pinky
  3.71 mm, and ring 8.07 mm. Index remains 16.95 mm away. Front/side renders
  still show fingertips piercing through the fretboard without visible joint
  arcs around the neck edge, so V256 is rejected as a production pose.
- The accepted production checkpoint remains V250. The next solve must add
  explicit fretboard/neck collision and edge-clearance constraints; independent
  point targets are insufficient even when the pad landmarks are correct.

Current live file:
`production_v256_corrected_pad_solve/Character_An_corrected_pad_solve_v256.blend`
(diagnostic scene; reopen V250 for the collision-aware solve).

## 2026-10-13 continuation: V257-V259 guitar-surface and collision evidence

- The V206 guitar was measured in its own transformed coordinates. The
  fretboard top is local Z 0.0155; strings S4/S5/S7/S8 run near local Z
  0.0211-0.0223; the neck back is local Z -0.027. The protected V237 finger
  coordinates lie near local Z 0.025-0.026 and the old thumb coordinate lies at
  local Z -0.0701. They are proxy-sphere centers, not literal skin-surface
  contacts. Exact skin fitting to those centers was therefore geometrically
  wrong.
- V257 preserved the V237 fret/string X/Y assignments but derived pad targets
  from the actual string curves, bevel radii, and 1.85 mm depression. It also
  moved the thumb pad target onto the real neck back. Penetration was reduced,
  but independent pad fitting still allowed phalanges to cross the neck.
- V258 added signed collision penalties sampled along all three finger-bone
  segments against the transformed neck/fretboard volume. It successfully kept
  the full hand outside the wood, proving the collision model, but contact error
  rose because the inherited wrist placement left the collision-safe chains out
  of reach. V258 is diagnostic only.
- V259 applied the mean V258 residual as a wrist translation. It worsened the
  multi-finger fit because the main Rigify hand IK transform is coupled to the
  arm and cannot be corrected by a naive world residual. V259 is rejected.
- The accepted production checkpoint remains V250. The next production solve
  must optimize the main wrist orientation/translation and local finger chains
  jointly under the V258 collision constraint; sequential wrist residual
  correction is not valid for this rig.

Current live file:
`production_v259_collision_wrist_refit/Character_An_collision_wrist_refit_v259.blend`
(rejected diagnostic; reopen V250 before the joint constrained solve).

## 2026-10-13 continuation: V260-V262 constrained-hand conclusion and wardrobe pivot

- V260 alternated joint optimization of the arm-coupled Rigify wrist and all
  five local digit chains under the verified neck collision field. It remained
  collision-safe but could not reduce the multi-finger contact residual; the
  player-side render still exposed a detached distal region. V260 is rejected.
- V261 searched 225 wrist states around the true V206 neck axis (nine angles
  and a five-by-five side/back offset grid). The original V258 wrist state was
  still the best-scoring collision/contact state. This rules out local wrist
  retuning as the missing solution: the provisional V250 hand rig is
  underactuated for the requested chord under real wood collision.
- The bundled Blender Human Base Meshes source contains 407 objects and 227
  meshes but no armatures or actions; there is no hidden production hand rig to
  append. V250 remains the accepted rollback checkpoint, but its local hand rig
  must eventually be replaced or structurally rebuilt rather than retuned.
- Work moved to the independent wardrobe lane instead of repeating the failed
  hand optimization. V262 replaces the short V241 jacket shell with a
  wrist-length, Rigify-weight-selected body-derived jacket, adds subdivision
  before thickness, and introduces a washed-charcoal woven material. The
  sleeves now reach the wrists and follow the playing pose. The old V242 rigid
  collar/piping details remain visibly crude, so V262 is a wardrobe-progress
  checkpoint, not an accepted film-quality garment.

Current live file:
`production_v262_long_sleeve_jacket/Character_An_long_sleeve_jacket_v262.blend`.

Next wardrobe gate: remove the oversized V242 tube seams and rigid collar,
replace them with fitted shirt collar wings, narrow jacket lapels, cuffs,
placket/buttons, and pocket construction, then render neutral and performance
deformation views before promoting the garment branch.

## 2026-10-13 continuation: V263-V264 tailoring cleanup

- V263 hides all nine inherited V242 rigid/tube details and replaces them with
  narrow lapel ribbons, two folded shirt-collar wings, a center shirt placket,
  paired breast pockets and flaps, jacket/shirt button stacks, and a 1.2 mm hem
  stitch. These details are chest-bone parented and remain construction-stage
  geometry; the blocky body-derived jacket silhouette is still not film-ready.
- Visual review exposed the large waist ring as `V243_TROUSER_WAISTBAND`, not a
  jacket seam. V264 hides that toroidal artifact and retunes the trousers to a
  deeper, rougher black. The waist silhouette is now clean in front and
  three-quarter performance views.
- V264 is the current wardrobe-progress checkpoint, but it is not accepted as
  final: shoulders remain inflated, pockets/lapels need conformance, boots and
  rolled cuffs remain blockout quality, and the guitar obscures much of the
  torso in performance renders. A neutral wardrobe inspection pose is required
  before promotion.

Current live file:
`production_v264_waist_cleanup/Character_An_waist_cleanup_v264.blend`.

Next garment gate: create a neutral/A-pose inspection action for the V264
branch, conform lapels/pockets to the jacket surface, reduce shoulder volume,
then rebuild the Chelsea boots and rolled trouser cuffs from reference-profile
silhouettes rather than rounded boxes and elliptical bands.

## 2026-10-13 continuation: V265-V269 neutral inspection and boot reset

- V265 rendered the current character in the rig rest pose with the guitar
  hidden. It exposed the true wardrobe defects: inflated shoulders, torn wrist
  boundaries, floating pocket slabs, blocky tailoring, rigid cuff rings, and
  crude boots. V265 is the clean neutral diagnostic source for replacement
  work, not a final wardrobe checkpoint.
- V266 and V267 tested deletion-based body shells. V266 copied jacket geometry
  onto the hands and lost shoulder coverage; V267 reduced the hand copy but
  retained shoulder holes and wrist tears. Both are rejected. Final garment
  topology must be explicitly modeled rather than cut from the full body mesh.
- V268 tested a lofted Chelsea-boot structure. Visual review rejected its
  oversized bulbous toe, broad shaft, thick platform sole, and toy-like read.
- V269 rebuilt the boots independently from V265 using the reference sheets:
  a substantially narrower low almond toe, close ankle shaft, separate welt,
  thin outsole, modest heel, side gores, and pull tabs, all parented to the
  Rigify foot controls. It is a clear silhouette improvement over V268, but
  the shaft/upper transition, leather detailing, heel shape, and rigid inherited
  trouser cuff still require the V270 production pass.
- The active ten-phase production sequence is recorded in `NEXT_10_PHASES.md`
  (V269-V278) and covers boots, garment topology, tailoring, shirt/trousers,
  identity/lookdev, groom, facial animation, body/hand deformation, and final
  performance/delivery proof.

Current live file:
`production_v269_reference_chelsea_boots/Character_An_reference_chelsea_boots_v269.blend`.

Next gate: V270 must refine boot construction/material response and replace the
inherited rigid cuff rings before the garment-topology reset begins.

## 2026-10-13 continuation: V270 boot finish and cuff diagnostic

- V270 added fine leather roughness/bump response, separate vamp and quarter
  seam guides, and replaced the V243 toroidal cuffs with narrower shaped cloth
  bands parented to the shin controls.
- Direct front/profile/three-quarter review shows improved boot proportion and
  surface response, but also reveals that the shaft is still too cylindrical,
  the seam curves read as bright disconnected dashes, the sole remains too
  rectangular, and the cuff still reads as a padded ring rather than folded
  trouser cloth. V270 is therefore a diagnostic/progress checkpoint, not a
  promoted production result.
- Phase 271 should begin from V269 or V270 only as a boot reference branch;
  final boot/cuff corrections should be integrated after the clean garment
  topology establishes the real trouser hem and ankle overlap.

Current live file:
`production_v270_boot_finish_cuffs/Character_An_boot_finish_cuffs_v270.blend`.

Next gate: start the V271 garment topology reset, hiding the failed V262-V267
shell/details and building explicit jacket panels/sleeves with continuous
shoulder and wrist topology before reintroducing tailoring details.

## 2026-10-13 continuation: V271 garment evidence and V276 facial foundation

- V271 measured the live rest-pose skeleton and body envelope, then replaced
  height-cut body copies with an explicit open torso shell and separately
  weighted sleeve topology. This eliminated copied hand fragments and wrist
  tears, but direct renders still show disconnected shoulders, a boxy torso,
  and exposed underlying shirt/body regions. A shoulder-cap experiment produced
  armor-like spheres and was removed from the authoritative script. V271 is
  rejected as a visual production garment, but its measurement and weighting
  evidence remains useful.
- The official Human Base Meshes bundle contains anatomy only. A CC0 open-lapel
  jacket was located in the 3DAssets Clothing Rail catalog and recorded under
  `third_party/3dassets_clothing_rail/v1/SOURCE.md`, but the current shell could
  not resolve the asset CDN, so no external binary entered the project.
- A face-animation audit found that the Rigify facial controls exist, but the
  visible V216 head has no shape keys and is rigidly head-bone parented. V276
  therefore added non-destructive `CTRL_JawOpen`, `CTRL_Smile`, and
  `CTRL_BrowRaise` shape keys plus a keyed proof sequence on frames 1-40.
- Two blink implementations were visually rejected. The eyeballs protrude
  beyond the current head surface, so head-only coordinate deformation cannot
  produce a credible eyelid closure. The failed blink keys were removed from
  the saved V276 checkpoint; a proper solution requires separate lid geometry
  or a facial mesh with real eyelid loops/weights.
- V276 is a partial facial-animation foundation, not an accepted final face
  rig. Jaw and smile are readable but still require mouth interior, lip volume,
  and identity-preserving corrective sculpture.

Current live file:
`production_v276_facial_shape_system/Character_An_facial_shapes_v276.blend`.

Next gates: obtain or model production garment topology without primitive
patches; build real eyelid geometry and mouth interior before expanding the
facial control set; keep V270 as the integration source until those lanes pass
their own visual gates.

## 2026-10-13 continuation: V276b-V276c eyelid diagnostics

- V276b added independently driven lid and mouth-overlay geometry. The controls
  worked mechanically, but the eyelids rendered as flat brown ovals and the
  mouth remained a pasted-on aperture. V276b is rejected.
- V276c copied the head's own UV-textured orbital polygons into separate driven
  eyelid meshes. This fixed the obvious material mismatch, but direct neutral,
  bilateral-blink, and unilateral-blink renders show a dark smeared crease,
  incomplete anatomical closure, and visible brow/orbital pulling.
- Tightening V276c to the immediate eye region did not solve the structural
  defect. The visible head has no true eyelid loops or facial deformation
  weights, so further coordinate-collapse overlays would only polish the wrong
  architecture. V276c is retained as diagnostic evidence and is not promoted.
- The clean partial facial checkpoint remains V276. A production facial pass
  must start from a mesh with actual eyelid and lip loops, a mouth cavity, and
  deformation-ready topology; it must then transfer or reconstruct the V221
  identity without relying on surface overlays.

Diagnostic file:
`production_v276c_texture_matched_lids/Character_An_texture_matched_lids_v276c.blend`.

Current facial checkpoint:
`production_v276_facial_shape_system/Character_An_facial_shapes_v276.blend`.

## 2026-10-13 continuation: V277-A clean-body deformation matrix

- V277-A began Phase 277 from the accepted V239 clean body/rig rather than the
  rejected garment, facial-overlay, or dedicated-hand branches. It creates a
  90-frame action covering neutral, shoulder elevation, left/right elbow flex,
  wrist flex/pronation, lower-body bend, ankle bend, torso twist, a guitar-safe
  upper-body pose, and an exact neutral return.
- The first live matrix exposed a hidden V239 rig defect: FK controls changed,
  but the deform bones did not. Inspection proved that each generated
  `ORG-*` limb bone had both its FK and IK copy-transform constraints at full
  influence, so the later IK constraint overwrote the FK chain regardless of
  the `IK_FK` property.
- V277-A repairs that defect only in its own branch by removing the broken
  influence drivers and explicitly selecting the first/FK constraint on the
  upper-arm, forearm, hand, thigh, shin, and foot chains on both sides. The
  rerun produced real deformations from 107 mm to 1.158 m and returned to the
  evaluated neutral surface with 0.0 m vertex drift.
- Direct render review rejects the current poses as production deformation:
  shoulder elevation collapses the deltoid/axilla and swings the arms behind
  the torso, elbow/wrist tests inherit the same bad local-axis interpretation,
  the guitar-safe pose folds both arms behind the back, and the ankle proof
  camera no longer contains the displaced feet. These are now measured rig and
  pose-space defects rather than untested assumptions.
- V277-A is therefore a successful diagnostic and constraint-repair checkpoint,
  not a promoted animation-ready body. The next body pass must derive rotations
  in each control's actual local basis (or pose by target matrices), then add
  shoulder/elbow/wrist correctives only after the intended anatomical arcs are
  visible.

Current diagnostic file:
`production_v277a_deformation_matrix/Character_An_deformation_matrix_v277a.blend`
(SHA-256 `55c5ff8c50a86a627d666b89a24e49bac0e50f3a2e1054dfb05ec1988fe41612`).

Current accepted clean body/rig remains:
`production_v239_clean_auto_rig/Character_An_clean_auto_rig_v239.blend`.

## 2026-10-13 continuation: V276-D official animation-head candidate

- V276-D appended Blender Human Base Meshes' official
  `Head (Animation) - Realistic` collection into a disposable V270-derived
  stage and aligned its head envelope to the V216 reference-fitted head.
- The primary mesh is a compact animation topology with 3,242 vertices, 6,474
  edges, 3,234 polygons, and a UV map. Separate iris and sclera meshes are
  present. It has no materials or shape keys in the source, so identity,
  texture, facial shapes, and rig binding still have to be authored.
- Front, three-quarter, and profile renders show genuine eyelid and lip edge
  flow and a much more suitable deformation surface than V276b/V276c overlays.
  The default identity is generic and does not yet match the reference.
- The requested `Jaw - Realistic` name was not available as a collection in
  the library append operation, and one eye component is visibly displaced
  below the neck after shared-envelope alignment. V276-D is therefore a source
  topology candidate, not a promoted head.
- Next facial step: resolve the eye parenting and locate/append the jaw object
  by exact object or mesh datablock name, then build a landmark-preserving
  conformation from this topology toward V216/V221 before adding blink, jaw,
  lip, brow, gaze, and phoneme shapes.

Current facial-topology candidate:
`production_v276d_animation_head_candidate/Character_An_animation_head_candidate_v276d.blend`
(SHA-256 `9ab55474f79463b1563109fc59a219973c1820ed68c49debda4132becce686bb`).

## 2026-10-13 continuation: V276-E through V276-H facial topology proof

- V276-E rebuilt the official animation head from V270 while preserving its
  authored hierarchy. Transforming only the root head fixed V276-D's doubled
  eye transforms: sclera centers now sit at approximately x +/-37.5 mm,
  y -97.8 mm, z 1.668 m with their iris children intact. The official
  `Jaw - Realistic` object was appended directly; it contains 5,294 vertices,
  5,058 polygons, teeth, gums/mandibular geometry, and a UV map.
- The jaw source used a different internal mesh offset. V276-F measured and
  seated it behind the closed lips at center `(0, -0.045, 1.565)`. It no longer
  renders below the neck or protrudes through the chin.
- V276-F also tested nearest-surface identity conformation. Correcting the BVH
  coordinate space reduced the mean source/target distance to 13.44 mm, but the
  result pinched the nose and mouth into visible creases. Nearest-surface
  conformation is rejected and V276-F remains diagnostic.
- V276-G replaced shrinkwrap with an 18-landmark smooth warp covering nose,
  lips, lids, brows, cheeks, chin, temples, head width, crown, and back of head.
  Two false jaw correspondences were discovered and removed. The final warp
  moves vertices by 10.71 mm mean / 31.23 mm maximum, preserves smooth eyelid
  and lip topology, aligns the eye hierarchy, and keeps the dental asset seated.
  V276-G is the current accepted structural facial-topology checkpoint, but its
  lower-face identity is still generic and requires reference-guided sculpture.
- V276-H adds relative animation shapes on top of the identity warp:
  independent left/right blink, jaw open, smile, and brow raise, plus a real
  jaw hinge that rotates the dental asset. It records a keyed proof sequence on
  frames 1-60 and returns to neutral.
- Direct review shows jaw, smile, and brow controls are readable and stable.
  The final blink is localized to 284 left / 262 right vertices and closes to a
  very narrow slit without V276c's brow/nose smearing, but a thin sclera line
  remains. V276-H is a legitimate partial facial-rig checkpoint, not the final
  Phase 276 promotion. Final work still needs a sealed blink with lid volume,
  gaze controls, lip seal/corners, frown, phonemes, correctives, identity sculpt,
  and production skin/eye/oral materials.

Current structural face checkpoint:
`production_v276g_landmark_identity/Character_An_landmark_identity_v276g.blend`
(SHA-256 `80344bc85406ebc2c065607f863143880e13fbe54f88c1be6a97603102209c45`).

Current facial-deformation proof:
`production_v276h_facial_deformation_proof/Character_An_facial_deformation_v276h.blend`
(SHA-256 `4466871ec1804eae59882c531b90abd9cb1aee50d13745e2386606f8ce435e1f`).

## 2026-10-13 continuation: V276-I/J facial controls, V277-B/C IK matrix, V274-A/B lookdev

- V276-I executed the queued extended facial-control pass from V276-H. It
  added frown, O/E/M phonemes, cheek puff, and gaze tests, but direct render
  review rejected it: the M shape pulled the chin, E over-stretched the mouth,
  cheek puff was weak, and gaze was visually unreadable.
- V276-J rebuilt those additions from V276-H with tighter mouth-region masks,
  an animator-facing `CTRL_FACE_GAZE` object, and reduced speech ranges. The M
  shape no longer drags the chin, E/frown remain local, and cheek volume is
  readable. The official eye assembly still presents gaze poorly and the head
  identity remains generic, so V276-J is a safer partial facial-control
  checkpoint, not a Phase 276 promotion.

Current corrected partial facial checkpoint:
`production_v276j_corrected_facial_controls/Character_An_corrected_facial_controls_v276j.blend`
(SHA-256 `c517b4822bb6de8892e783b81d61c0d5c39e9c9b66c1bf5483f8d0cdfc0fcf02`).

- V277-B repaired all twelve V239 `ORG-*` arm/leg chains with FK
  `COPY_TRANSFORMS=0` and IK `COPY_TRANSFORMS=1`, then drove hand, foot, elbow
  pole, and knee pole controls with world-space matrices. Target authority and
  exact neutral return were proven, including the intended guitar hand target
  positions, but the render gate rejected the extreme pole depth, compressed
  elbows, floating knee test, and inherited down-facing guitar wrists.
- V277-C reduced pole depth and bend ranges, kept the knee test within about
  36 mm of the neutral foot height, and gave both guitar hands explicit
  orientations. It returns to neutral with 0.0 m evaluated vertex drift and is
  materially better than V277-A/B. It remains diagnostic: raised-arm
  deltoid/axilla collapse and guitar-specific shoulder/forearm shapes require
  corrective sculpting, and the clean-body test contains no instrument.

Current body/IK diagnostic checkpoint:
`production_v277c_refined_ik_matrix/Character_An_refined_ik_matrix_v277c.blend`
(SHA-256 `9c603bd123ca56bda5eda27004af6f3199a65ba0e9826c7dee2383bfd96dd2f9`).

- V274-A/B applied a fresh lookdev pass to V276-J using only the useful parts
  of the older V203/V204 approach: random-walk skin, separated sclera/iris/
  pupil materials, surface-sampled curls, brows, beard, moustache, and the
  three glabella marks. The old projected V221 face texture and cap-like V217
  groom were not reused.
- V274-B adds two render levels of subdivision, less orange skin response,
  lower-energy portrait lighting, denser/longer groom curves, and smaller iris
  discs. Direct front/three-quarter/profile review still rejects it as final:
  the groom is frizzy and lacks the reference's dense curl mass and corner
  part, the eye assembly remains dark and flat, and geometry is not yet a
  convincing likeness of the supplied character.

Current lookdev diagnostic checkpoint:
`production_v274b_refined_lookdev/Character_An_refined_lookdev_v274b.blend`
(SHA-256 `8cf3825e48e4f4c5650d6eb6b1e49de3e939194c9d59d24c821e2d668aa7fe95`).

Next highest-value work:

1. Replace the current eye presentation with correctly scaled brown iris,
   visible warm sclera, corneal shell/tear line, and a gaze proof where pupil
   displacement is unmistakable.
2. Perform reference-guided identity sculpture on the V276-G/J animation
   topology: broader lower face, stronger brow/glabella, hooded lids, wider
   nose/alar base, fuller lips, and reference-matched chin/profile.
3. Rebuild the groom as clustered curl masses with a defined character-left
   corner part and temple taper; keep short flyaways secondary.
4. Add shoulder/axilla and elbow corrective shapes to V277-C before merging
   any body pose into the character/lookdev branch.
5. Reintroduce the protected guitar collision model and solve hands against
   actual neck/string surfaces; V277-C proves only the main-arm target system,
   not fretboard pad contacts or picking-hand grip.

## 2026-10-14 continuation: native FaceBuilder FACS, wardrobe rebuild, guitar/contact merge

- V278 generated KeenTools FaceBuilder's native 51-shape ARKit-compatible FACS
  set on `V216_REFERENCE_FITTED_HEAD`. Native blink, jaw, smile, brow, and O/M
  tests are materially more coherent than the earlier transferred custom
  shapes and return exactly to neutral.
- V279 merged that native-FACS head onto `V239_CLEAN_CHARACTER_RIG`; all 51
  shapes and the head-bone parent survived. V280/V281 oral overlays did not
  solve the baked-photo mouth smear and must not be treated as a real oral
  cavity.
- V282's primitive wardrobe was rejected as boxy. V283 rebuilt shirt, jacket,
  trousers, and boots from the clean body's anatomical surface and copied the
  Rigify weights. V284 and V285 detail experiments were rejected because trim,
  toe caps, and the waist underlayer separated or read as rigid overlays.
- V286 is the cleanest current wardrobe baseline. It removes detached soles
  and obsolete oral meshes and retains the anatomical, deformable shells. It
  is still an interim: the reference requires trucker-jacket collar/placket,
  chest-flap pockets, seams, a dark floral print, cuffed trousers, and rounded
  Chelsea boots without visible toe anatomy.
- V287 appends the accepted 94-object `V206_GUITAR_REBUILD` collection from
  V236 and applies V277-C's repaired frame-70 upper-body IK pose. The merge is
  correct; contact is explicitly unsolved.
- V288 proved that naively appending the V257/V250 hand hierarchy preserves an
  unevaluated parent transform and places the replacement at the hip. It is
  rejected.
- V289 reinstalls the V257/V250 articulated fretting hand with the evaluated
  V257 hub world matrix and masks 889 native left-hand vertices. This correctly
  places the approved fingertips on the fretboard and removes the open native
  hand. Closeups still show the known V257 failure: phalanges cross the neck,
  so V289 is the stable integration checkpoint, not contact acceptance.
- V290 tested a Rigify picking-hand curl and visible plectrum. Both positive
  and mirrored bend signs produced severe splay/crossing and are rejected. The
  live Blender scene was restored to V289 after that experiment.

Current integrated stable checkpoint:
`production_v289_explicit_hand_transform/Character_An_explicit_hand_transform_v289.blend`
(SHA-256 `105d8bb52c73f5d6ba6d390e3222118c70c95bbf97ac2f270d05fc41e9dd9d85`).

Current clean wardrobe checkpoint:
`production_v286_clean_baseline/Character_An_clean_baseline_v286.blend`
(SHA-256 `597b09a793e2e532699adb2075a5687ab6c6e6c91ac8142842970a05f46eaf44`).

Next highest-value work:

1. Structurally augment the V250 fretting rig with per-finger base translation
   or IK arc controls, then solve pad targets while keeping intermediate
   phalanges outside the V206 neck volume. Require front, oblique, and
   player-side renders plus evaluated collision samples before acceptance.
2. Calibrate the main Rigify right-hand bend axes from small per-axis probe
   renders before attempting another pick grip; V290's assumed X-only bend is
   invalid for this generated rig.
3. Replace V286's interim surface garments with true trucker-jacket panels,
   collar, pockets, cuffs, shirt print, trouser cuffs, and clean Chelsea-boot
   lasts, retaining the working Rigify weights.
4. Replace the photo-baked eye/mouth presentation and rebuild the groom as
   dense curl clumps with the reference's character-left part.

### 2026-10-14 later continuation: calibrated and dedicated picking hand

- V291 rendered signed local-axis probes for the generated Rigify right index
  and thumb. Positive local X curls the second joints; Y/Z mainly spread or
  twist. The diagnostic proved that V290 failed because it applied the same
  assumed bend to every first knuckle.
- Even with calibrated signs, the native right-hand weights visibly collapsed
  and stretched the palm under a multi-finger curl. The native hand is rejected
  for close picking shots.
- V292 mirrors the intact V250 dedicated hand/armature onto `DEF-hand.R`, masks
  889 native right-hand vertices, and preserves coherent finger anatomy under
  curl. This is the new picking-hand architecture.
- V293 runs a 599-evaluation thumb/index pinch solve. It reduces the dedicated
  hand's tip separation from about 45 mm to 2.635 mm without collapsing the
  mesh and replaces the orange source material with `MAT_V211_NEUTRAL_CLAY`.
- V294 translates the solved pinch by `(-7.34, +13.57, +26.48) mm` onto the
  measured bridge-side S4/S5 string endpoint plane. The dedicated hand remains
  coherent and the plectrum is seated at the solved pinch. V294 is the current
  integrated picking-hand checkpoint.
- V295 tested first-bone translation as a new fretting-hand clearance degree
  of freedom. It reduced sampled neck-envelope intersections (for example,
  ring 11 to 2 and pinky 9 to 2) but allowed contact drift up to 23.67 mm and
  visibly moved fingers under the neck. V295 is rejected. Future fretting
  solves must treat sub-millimeter pad contact as a hard constraint rather than
  a weighted objective.

Current integrated stable checkpoint:
`production_v294_pick_string_alignment/Character_An_pick_string_alignment_v294.blend`
(SHA-256 `ab7649cf9fa0cb31cad3fd975998b97855d95587d57652db61808719a53e56d2`).

### 2026-10-14 resumed continuation: hard-contact test and reference guitar body

- V296 projected the V295 bone tails back to their saved contact positions with
  0.001--0.018 mm errors, but this simply restored the original 7/8/11/9
  neck-envelope intersections. Close renders again showed fingertips emerging
  through the fretboard. V296 is rejected.
- V297 replaced the bone-tip objective with evaluated fingertip-pad vertices
  and reprojected the pad after every arc candidate. It held all four real
  surface contacts within 0.297 mm and improved pinky/ring clearance, but the
  dedicated hand's automatic weights split the fingers visibly away from the
  palm under the required correction. V297 is rejected and proves the current
  V248/V250 fretting mesh and weights must be replaced as one unit.
- V298 traced 49 explicit landmarks from the supplied straight-on Strandberg
  product photograph and interpolated them into a 196-point outline. It
  replaced the old 30-vertex V206 body/top pair with a 392-vertex asymmetric
  double-cut body while preserving the validated neck, fan, eight strings,
  frets, pickups, bridges, and character placement.
- V299 moved both knobs and the switch onto reference-relative positions in the
  new outline. V300 reduced the overly graphic procedural figure and hides only
  the still-misoriented output jack and two strap buttons pending a true body-
  edge orientation pass. The new silhouette is an interim accepted improvement,
  not final photoreal guitar lookdev.

Current integrated guitar-body checkpoint:
`production_v300_guitar_visual_acceptance/Character_An_guitar_visual_acceptance_v300.blend`
(SHA-256 `e684c41668c7c23a04b9471aa52f1782b4db41d30144e6124d989e1c2e92b0e0`).

Immediate next work:

1. Replace the V248/V250 fretting hand mesh and automatic weights with a
   continuous production hand topology and bind; then rerun the V297
   surface-locked solve against the V300 instrument.
2. Rebuild the picking-hand wrist transition and validate pick/string contact
   against the V300 body/bridge silhouette.
3. Continue the reference identity/groom and wardrobe passes; the present
   face, curl cap, jacket/shirt, trousers, and boots remain visibly interim.

### 2026-10-14 resumed continuation: continuous-hand route diagnostics

- V301 removed all per-finger root translation and solved only the common hand
  hub plus connected joint rotations. This preserved continuous finger/palm
  deformation, but pad errors remained 3.52--8.84 mm and sampled neck
  intersections remained substantial.
- V302 refined all three local rotation axes. Middle and ring pad errors fell
  to 0.247 mm and 1.171 mm, but index, pinky, and thumb remained 3.37--5.58 mm
  away and the intersection count worsened. V302 is rejected.
- V303 added an explicit anatomical route around the positive-Y neck edge and
  rendered front, player, rear, and edge views. It improved the thumb target to
  0.627 mm and forced the proximal hand outward, but the index missed by 9.78
  mm and the visible fingers splayed sideways instead of forming a credible
  fretting arc. The rear/edge views also confirm that the wrist/hand integration
  is not production-ready. V303 is rejected.
- These tests close the current optimization branch: the V248 hand topology is
  continuous, but its present bind and pose basis cannot satisfy both contact
  and a credible neck wrap. Do not continue tuning objective weights. Rebind or
  replace the hand/armature together, calibrate its curl planes in a neutral
  diagnostic scene, then solve against the V300 surface.

Current accepted overall checkpoint remains:
`production_v300_guitar_visual_acceptance/Character_An_guitar_visual_acceptance_v300.blend`.

Rejected diagnostic:
`production_v303_anatomical_fretting_route/Character_An_anatomical_fretting_route_v303.blend`
(SHA-256 `75d383487fb18c70b40c258eaafa958888400e8809c23332e2ba0caae4bcacb3`).

- V304 audited the bind directly. The mesh is a single connected 831-vertex
  component, but the automatic weights overlap implausibly across digits (for
  example, 272 vertices in `middle_01` and 363 in `ring_01`). A deterministic
  nearest-segment rebind capped every vertex at three groups and reduced the
  palm/root assignment to 264 vertices. The saved diagnostic proves the source
  topology is connected, but the first neutral/curl proof did not produce a
  distinct curl in the isolated render, so V304 is not accepted and must not be
  merged. Next, test modifier/bone deform flags and rest-pose matrices in an
  isolated hand scene before another integrated solve.

Current rebind diagnostic:
`production_v304_fretting_rebind_probe/Character_An_fretting_rebind_probe_v304.blend`
(SHA-256 `95b7c7a63c33613b35dea1d695713fc42e7dfb11b7a7073519f6dd474c66c4bb`).

### 2026-10-14 photoreal identity continuation: FaceBuilder automation and V332

- A photoreal three-view reference triptych was generated from the locked
  character sheets and split into front, three-quarter, and profile views under
  `references/derived/photoreal_facebuilder_v1/`. The character has no glasses.
- V326 automated KeenTools FaceBuilder from all three views: 26 front pins,
  22 three-quarter pins, 12 profile pins, a 4096 px baked texture, and 51 FACS
  blendshapes. This is the first identity branch worth carrying forward.
- V327 integrated V326 with the corrected V322 Rigify male body. V328-V331
  tested color grading, neck masks, wardrobe coverage, and procedural grooming.
  The V328 procedural curl cap and the V329/V330 duplicate-jaw overlap routes
  were visibly rejected and must not be promoted.
- V332 keeps the complete FaceBuilder head, removes the generic body head/jaw
  above the collar, retains 51 FACS shapes, and removes the worst neck seam.
  It is the current photoreal identity foundation, not a finished character.
- V332 is open in the live Blender MCP scene through the loopback bridge.

Current live identity checkpoint:
`production_v332_remove_duplicate_chin/Character_An_remove_duplicate_chin_v332.blend`
(SHA-256 `82a8bf35cdaf7d42db4be152dac5170d2050983f1805adf1fa4e36b209df1e11`).

Known visible work still required:

1. Correct the FaceBuilder under-chin/rear-scalp projection artifacts and
   grade the face from its current pale tone toward the locked medium-brown
   reference without destroying photographic detail.
2. Add separate wet eyeball/cornea geometry and a production scalp-following
   black curl groom with the reference side part. Do not reuse the V328 cap.
3. Replace the rejected flat V325 jacket/collar with tailored deformable
   panels; keep only useful shirt/trouser foundations and the generated dark
   floral base color.
4. Integrate the V318 official-scale Strandberg geometry with corrected finish,
   then transfer the authoritative V315 fingering map to the V322 Rigify body:
   index S6/F11, middle S6/F10 hover, ring S7/F9, pinky S8/F11, thumb behind
   neck. V321 passed proxy collisions but is visually rejected as tangled.
5. Complete footwear, deformation tests, facial rig validation, playing-pose
   contact renders, and final Cycles portrait/full-body/guitar turntables.

### 2026-10-14 groom, eye, and jacket visual iteration (V333-V337)

- V333 built 1,000+ thin procedural curl splines on an ellipsoidal scalp with
  a matte near-black material. It proved the guide-parenting and shading route,
  but the uniform large loops read as a bowl/crocheted cap and were rejected.
- V334 narrowed and thinned the curl footprint and replaced corrupt rear photo
  projection faces with temporary matte scalp/neck assignments. Its front and
  three-quarter silhouette is a useful improvement over V332, but the rear
  per-face material boundary is faceted and not final. Dense rear guides plus
  the final jacket collar must hide/replace that boundary.
- V335 tested complete overlay eyeballs. They sat in front of the closed
  FaceBuilder eyelids and produced a cartoon stare; rejected. V336 tested only
  shallow corneal domes, but these produced bright rings below the lids;
  rejected. A real animation-ready eye system requires deliberate socket and
  eyelid topology, not overlay geometry.
- Web asset research did not yield a clean free jacket worth importing. The
  closest Sketchfab result was labeled CC0 in its title but actually reported
  a ShareAlike license; the polished workwear option was paid. Neither was
  incorporated.
- V337 promoted the old deformable jacket shell without decorative panels and
  added a denim shader. Its opening and silhouette read as a wetsuit, not a
  work jacket; rejected. The jacket must be rebuilt from true front, back,
  sleeve, collar-stand, cuff, hem, and lapel pattern pieces.

Current live MCP checkpoint is V334:
`production_v334_groom_projection_cleanup/Character_An_groom_projection_cleanup_v334.blend`
(SHA-256 `78e8c37da206fdc5004975adabe03994c9cc3e619c8203946c08801204e5fff8`).

Rejected branches that must not be promoted:

- V335 full overlay eyeballs
- V336 corneal overlay domes
- V337 extracted jacket shell

Next production actions:

1. Rebuild the groom with smaller, denser clumps extending around the rear and
   sides, using a nonuniform crown silhouette and a clean side part. Cover the
   temporary V334 scalp material boundary completely.
2. Create proper eye sockets/eyelid rims or transfer compatible production eye
   topology before adding rotatable eyeballs and corneas.
3. Pattern-model the jacket rather than extracting another body shell.
4. Continue with V318 guitar integration and the authoritative V315 fretting
   map after the character foundation is visually coherent.

### 2026-10-20 contour guitar and Modal render offload (V338-V342)

- V338 integrated the complete 70-object V318 guitar hierarchy into V334 and
  replaced the figured/tiger finish with graphite, ebony, black hardware, and
  steel materials. It retained the old blade-like body and was not accepted.
- A project-local OpenCV environment (`pipeline/.venv-contour`) and
  `pipeline/extract_strandberg_product_contour.py` extracted a 30-point product
  silhouette from the locked Strandberg reference. V339's manual polygon was
  rejected for self-intersections. V340 used the image contour but retained
  obsolete overlays; V341 removed `V206_FIGURED_TOP` and `V318_BODY_REVEAL`.
- V342 restored the graphite shader lost when the V340 body mesh replaced the
  old datablock. It is a valid diagnostic scene, but it is not approved: the
  finish still reads too pale and the rear/lower contour spikes are too large.
  The authoritative next guitar step is contour refinement against
  `references/props/strandberg/strandberg_full_product.jpg`, not fretting-pose
  work on this silhouette.

Current live Blender MCP checkpoint:
`production_v342_graphite_contour_guitar/Character_An_graphite_contour_guitar_v342.blend`
(SHA-256 `2704629535f45c13d46e7a40137c26ee4bbcb210711c02b0d97d0f85dd1cf35c`).

- `pipeline/prepare_v342_modal_bundle.py` packed ten external resources into a
  33 MB self-contained blend. `pipeline/modal_blender_render.py` now provides a
  Modal L4 / Blender `bpy==5.2.2` Cycles worker with the Linux runtime libraries
  required by Blender. Four 64-sample GPU Cycles views completed successfully
  under Modal run `ap-0iTou8hte4SV4TEMbOjtnu`; outputs are in
  `production_v342_graphite_contour_guitar/modal/renders/`.
- Modal is authorized for this project. Offload Cycles stills, comparison
  batches, turntables, and deformation frames; keep topology/pose iteration in
  the scene-aware loopback Blender MCP session.
- Mobile progress notifications use ntfy topic `BCA_task`; the continuation
  notification was sent successfully.
- `character-asset-lid-inhibit.service` was renewed as an eight-hour user
  inhibitor for `sleep:handle-lid-switch`; it is temporary and does not alter
  the permanent lid policy.
