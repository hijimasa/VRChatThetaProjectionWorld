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
- GPU is optional: NVIDIA (CUDA), AMD/Intel (DirectML via ONNX Runtime), or CPU-only all work — see [Inference backends](#inference-backends)

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
python server.py
```

- The server outputs a combined image (2048x512) with RGB and depth images side by side to the OBS virtual camera.
- On first run, the UniFuse model checkpoint will be automatically downloaded.
- Every 10 seconds the server prints the FPS with a per-stage time breakdown.

Options:

| Option | Description |
|---|---|
| `--capture {auto,av,opencv}` | Capture method. `auto` uses PyAV (FFmpeg DirectShow, ~2-3x faster) when installed and falls back to OpenCV |
| `--device-name NAME` | DirectShow device name for PyAV capture (default: `RICOH THETA UVC`) |
| `--index N` / `--camera N` | Camera device index for OpenCV capture (default: 0) |
| `--backend {auto,torch,onnx}` | Inference backend. `auto` picks CUDA → DirectML → CPU |
| `--infer-height N` | Inference input height (width = 2N). Defaults to 512 on GPU, 256 on CPU |
| `--export-onnx` | Export the ONNX models and exit (for non-NVIDIA machines) |

#### Inference backends

The depth model runs on one of the following (picked automatically):

1. **PyTorch + CUDA** — NVIDIA GPUs
2. **ONNX Runtime + DirectML** — any DirectX 12 GPU (AMD / Intel / NVIDIA), e.g. the Radeon iGPU of small laptops like the GPD Pocket 4: `pip install onnxruntime-directml`
3. **ONNX Runtime CPU / PyTorch CPU** — inference resolution is automatically halved (512x256) to keep a usable frame rate

For a machine without PyTorch (e.g. a small laptop), run `python server.py --export-onnx` once on any machine with PyTorch (`pip install onnx` required) and copy the generated `checkpoints/UniFuse/*.onnx` files — then only `onnxruntime-directml` is needed to run.

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
