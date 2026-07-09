# VRChatThetaProjectionWorld
English | [日本語](README-ja.md)

## Overview

![](./figs/test.gif)

This project visualizes monocular depth estimation results from a THETA camera inside VRChat, projecting the live 360° video onto a depth-displaced sphere. It consists of two components:

- **ThetaImageServer**: A server program that generates and streams a combined color + depth image from the THETA camera.
- **ThetaProjection asset** (`THETAProjectionWorld/Assets/ThetaProjection`): A self-contained Unity asset folder (shaders, sphere mesh, material, optional Udon behaviour, editor tools) that you can drop into **any** VRChat world project.

**You do not need to use this repository's world.** The recommended way to use this project is to copy the `ThetaProjection` folder (or import an exported `ThetaProjection.unitypackage`) into your own world and combine it with your own video player. The Unity project in this repository is just a sample/development world.

TopazChat Player is a third-party asset and is **not** included in this repository (and never needs to be modified — the `ThetaProjection` asset works with an unmodified TopazChat Player).

## Using the ThetaProjection asset in your own world

1. Copy `THETAProjectionWorld/Assets/ThetaProjection` into your world project's `Assets` folder (or import the `.unitypackage`). Requires VRChat SDK3 Worlds.
2. Set up a video player in your world as usual, e.g. [TopazChat Player 3.0](https://booth.pm/ja/items/1752066) (download it yourself from BOOTH).
3. Select the video player's screen object (for TopazChat Player: the `Monitor` object in the prefab).
4. Run **Tools > THETA Projection > Convert Selected Screen To Projection Sphere** from the Unity menu. This swaps the screen's mesh and material for the projection sphere — the video player's own files are left untouched.

See [`THETAProjectionWorld/Assets/ThetaProjection/README.md`](THETAProjectionWorld/Assets/ThetaProjection/README.md) for details (other video players, in-world parameter adjustment, shader parameters, exporting the unitypackage).

## Running the sample world in this repository

### Prerequisites

- Windows
- Unity 2022.3 LTS (via VRChat Creator Companion)
- VRChat SDK3 (Worlds)
- Python 3.8+ (for ThetaImageServer)
- THETA camera (Z1 or V recommended)

### Pre-installation steps

1. **Install THETA UVC Driver for Windows**
   - Download and install the Windows UVC driver from [RICOH THETA UVC Driver](https://support.ricoh360.com/ja/app-download).
   - This driver is required to recognize the THETA camera as a webcam.

2. **Set up TopazChat Player 3.0**
   - Download [TopazChat Player 3.0](https://booth.pm/ja/items/1752066) from BOOTH.
   - Extract the downloaded zip file and place its contents in the `THETAProjectionWorld/Assets` directory (no modification needed).
   - TopazChat Player is used to receive video streaming within VRChat.

### Setup

1. **Clone this repository**:
   ```bash
   git clone https://github.com/hijimasa/VRChatThetaProjectionWorld.git
   cd VRChatThetaProjectionWorld
   ```

2. **Install Python dependencies**:
   ```bash
   cd ThetaImageServer
   pip install -r requirements.txt
   ```

3. **Install OBS Studio or virtual camera software**:
   - OBS Studio (recommended): https://obsproject.com/
   - Or any pyvirtualcam-compatible virtual camera driver

4. **Set up Unity project**:
   - Open the Unity project in the `THETAProjectionWorld` directory.
   - Ensure TopazChat Player 3.0 files are placed in the `Assets` folder.

## Usage

### 1. Start ThetaImageServer

```bash
cd ThetaImageServer
python server.py --camera 0
```

- `--camera 0`: Camera device ID (device ID where THETA is connected, typically 0 or 1)
- The server outputs a combined image (2048x512) with RGB and depth images side by side to a virtual camera named "THETA Depth Camera".
- On first run, the UniFuse model checkpoint will be automatically downloaded.

### 2. Display in VRChat World

1. Open the scene in `Assets/Scenes` in Unity Editor.
2. Select the virtual camera "THETA Depth Camera" in TopazChat Player.
3. Enter Play Mode to see real-time mesh deformation based on depth data.
4. Adjust parameters on the `ThetaProjectionScreen` material (`Assets/ThetaProjection/Materials`):
   - **Depth Scale**: Depth scaling factor
   - **Minimum Radius**: Minimum sphere radius
   - **Flip Y for Depth/RGB**: Flip image vertically

### 3. Upload to VRChat

1. Build and upload the world using VRChat SDK Control Panel.
2. In VRChat, configure TopazChat Player to use the virtual camera.

## Directory Structure

```
VRChatThetaProjectionWorld/
├── ThetaImageServer/           # THETA image processing server
│   ├── server.py              # Main server script
│   ├── requirements.txt       # Python dependencies
│   ├── baseline_models/       # UniFuse depth estimation model
│   ├── utils/                 # Utilities (Equirectangular conversion, etc.)
│   └── checkpoints/           # Model checkpoints (auto-downloaded)
├── THETAProjectionWorld/      # Sample Unity world project
│   └── Assets/
│       ├── ThetaProjection/   # ★ Redistributable asset — copy this into your world
│       │   ├── Shaders/       # Depth displacement / projection shaders
│       │   ├── Materials/     # ThetaProjectionScreen.mat
│       │   ├── Meshes/        # UV sphere mesh
│       │   ├── Udon/          # Optional in-world parameter adjustment
│       │   └── Editor/        # One-click setup & export tools
│       └── Scenes/            # Sample world scene
└── README.md
```

## License

This project is licensed under the Apache 2.0 License. (TopazChat Player is a separate third-party work and is not covered by this license.)
