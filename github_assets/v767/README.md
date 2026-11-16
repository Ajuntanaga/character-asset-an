# V767 albedo repair trial

Generated with the built-in image_gen edit tool on 2026-11-15. This is a
1254 x 1254 trial, not a verified UV-registered or production-resolution atlas.
The original packed 4096 x 4096 V326 atlas remains in the V766 checkpoint.
Evaluate the mapped Blender render before accepting the replacement.

Edit target: the packed `FBHead_baked_tex.002` image extracted from V739.
Supporting skin/identity reference:
`references/derived/photoreal_facebuilder_v1/character_an_three_quarter_v1.png`.
That generated reference is an interpretation aid; original character sheets
remain authoritative.

Prompt:

> Use case: precise-object-edit. Asset type: a UV-mapped face base-color texture for the existing Blender mesh. Image 1 is the exact edit target, a square unwrapped face/neck atlas; image 2 is ONLY the character skin-color and identity reference, never the desired layout. Repair Image 1 in its existing UV layout, with every feature at exactly its current pixel coordinates and scale. Keep the black outside-island background, the complete island boundaries and stretched peripheral pixels, eyes, eyebrows, beard, lips, ear and hair boundaries unchanged. Change only the skin surface color detail: remove strong baked specular highlights and directional shadows, and reduce the exaggerated rocky pitting and etched creases to subtle natural fine pores. Maintain warm medium-brown skin, subtle mottling/freckles and facial wrinkles of image 2. Delit diffuse albedo, even illumination, no shine. Preserve beard and brow pigment locations, lip pigment, anatomy, mouth opening and all UV registration. No portrait reformatting, no newly arranged UV islands, no beautification, no anatomical changes, no text, no labels. Output the repaired square atlas only at highest feasible resolution.
