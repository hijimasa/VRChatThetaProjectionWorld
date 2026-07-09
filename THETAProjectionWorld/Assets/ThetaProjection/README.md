# THETA Projection for VRChat Worlds

English | [日本語](README-ja.md)

Displays a live 360° video + depth stream from a RICOH THETA camera as a
depth-displaced sphere in any VRChat world. This folder is self-contained —
copy it into any VRChat world project (or import the `.unitypackage`) and it
just works. No third-party assets are included or required by this folder
itself; you bring your own video player (e.g. TopazChat Player).

Sender side (PC): see the `ThetaImageServer` in the
[VRChatThetaProjectionWorld](https://github.com/hijimasa/VRChatThetaProjectionWorld)
repository. It streams a 2048x512 combined image (left: RGB 1024x512,
right: depth 1024x512).

## Contents

| Path | Description |
|---|---|
| `Shaders/ThetaDepthDisplacementShader.shader` | Vertex-displacement shader (`ThetaProjection/DepthDisplacement`). Deforms the sphere per-vertex from the depth half of the video. |
| `Shaders/ThetaProjectionShader.shader` | Simple equirectangular projection shader (no displacement). |
| `Materials/ThetaProjectionScreen.mat` | Ready-to-use material for the projection sphere. |
| `Meshes/UVSphere_seg128_ring64_r1.asset` | 128x64 UV sphere mesh used as the screen. |
| `Udon/ThetaProjectionSetup.cs` | Optional UdonSharp behaviour for adjusting shader parameters in-world (sliders/buttons). |
| `Editor/ThetaProjectionScreenTool.cs` | One-click setup menu (see below). |
| `Editor/UVSphereMeshGenerator.cs` | Regenerates the UV sphere mesh with different resolution if needed. |

## Setup in your own world

Requirements: VRChat SDK3 Worlds (UdonSharp included), and any video player
that writes its video texture to the screen renderer's material `_MainTex`
(TopazChat Player, VRChat's AVPro video screen, etc.).

### With TopazChat Player (or any player with a screen object)

1. Import this `ThetaProjection` folder (or the `.unitypackage`) into your
   world project.
2. Set up your video player as usual (for TopazChat Player, get it from
   [BOOTH](https://booth.pm/ja/items/1752066) and place its prefab in your
   scene).
3. Select the player's screen object — for TopazChat Player this is the
   `Monitor` object inside the prefab.
4. Run **Tools > THETA Projection > Convert Selected Screen To Projection
   Sphere**. This swaps the screen's mesh for the UV sphere and its material
   for `ThetaProjectionScreen.mat`. Nothing inside the video player asset is
   modified.
5. Scale/position the screen object as you like (the sphere is what players
   stand inside).

### Without an existing screen object

Run **Tools > THETA Projection > Create Projection Screen In Scene** and point
your video player's screen output (material/renderer target, texture property
`_MainTex`) at the created `ThetaProjectionScreen` object.

### Optional: in-world parameter adjustment

Add the `ThetaProjectionSetup` UdonSharp behaviour to any GameObject and set
its **Target Renderer** to the projection sphere's renderer. It exposes
depth scale, minimum radius and Y-flip toggles, and can be driven by UI
sliders/buttons.

## Shader parameters

| Property | Meaning | Default |
|---|---|---|
| `_DepthScale` | Depth scaling factor (radius = `_DepthScale` / depth) | 0.02 |
| `_MinRadius` | Minimum sphere radius in meters | 0.1 |
| `_FlipY_Depth` | Flip V when sampling the depth half | 0 |
| `_FlipY_RGB` | Flip V when displaying the RGB half | 1 |

## Redistribution

Everything in this folder is original work licensed under Apache-2.0.
To export a package for sharing: **Tools > THETA Projection > Export
ThetaProjection.unitypackage**.
