# VRChatThetaProjectionWorld
English | [日本語](README-ja.md)

## Overview

![](./figs/test.gif)

This project visualizes monocular depth estimation results from a THETA camera in a VRChat world, displaying them with color mapping. It consists of two main components:

- **ThetaImageServer**: A server program that generates and streams both color and depth images from the THETA camera.
- **VRTest**: A test project that receives the streamed images, generates meshes based on the depth data, and displays them.

For the VRChat project, the most important scripts—such as those for mesh deformation—are located directly under the `Assets/Scenes` directory.

## Getting Started

### Prerequisites

- Windows
- Unity 2021.3 LTS or later
- VRChat SDK3 (Worlds)
- Python 3.8+ (for ThetaImageServer)
- THETA camera (Z1 or V recommended)

### Pre-Installation Steps

1. **Install THETA UVC Driver for Windows**
   - Download and install the Windows UVC driver from [RICOH THETA UVC Driver](https://support.ricoh360.com/ja/app-download).
   - This driver is required to recognize the THETA camera as a webcam.

2. **Set up TopazChat Player 3.0**
   - Download [TopazChat Player 3.0](https://booth.pm/ja/items/1752066) from BOOTH.
   - Extract the downloaded zip file and place its contents in the `THETAProjectionWorld/Assets` directory.
   - TopazChat Player is used to receive video streaming within VRChat.

### Setup

1. **Clone this repository**:
   ```bash
   git clone https://github.com/yourusername/VRChatThetaProjectionWorld.git
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
   - Import VRChat SDK3 (Worlds).
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
4. Adjust parameters in the Inspector:
   - **Depth Scale**: Depth scaling factor
   - **Sphere Radius**: Projection sphere radius
   - **Min Radius**: Minimum radius
   - **Flip Y**: Flip image vertically

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
├── THETAProjectionWorld/      # Unity project
│   └── Assets/
│       ├── Scenes/            # Main scene
│       │   ├── ThetaDepthMeshDeformer.cs      # Mesh deformation script
│       │   └── ThetaDepthDisplacementShader.shader  # GPU deformation shader
│       └── Editor/
│           └── UVSphereMeshGenerator.cs  # Mesh generation tool
└── README.md
```

## License

This project is licensed under the Apache 2.0 License.