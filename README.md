# VRChatThetaProjectionWorld
English | [日本語](README-ja.md)

## Overview

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

### Setup

1. **Clone this repository** to your local machine.
2. **Open the Unity project** in the `VRTest` directory.
3. **Import the VRChat SDK** if not already present.
4. **Configure the ThetaImageServer**:
    - Install required Python packages:  
      ```bash
      pip install -r requirements.txt
      ```
    - Connect your THETA camera and run the server:
      ```bash
      cd ThetaImageServer
      python server.py
      ```
5. **Run the Unity scene** in `Assets/Scenes` to test the mesh visualization.

## Usage

- Start the ThetaImageServer to begin streaming images.
- Enter Play Mode in Unity to view the real-time mesh deformation based on depth data.
- Adjust mesh and color mapping parameters in the Unity Inspector for customization.

## Directory Structure

```
VRChatThetaProjectionWorld/
├── ThetaImageServer/    # Python server for image streaming
├── VRTest/              # Unity project for visualization
└── README.md
```

## License

This project is licensed under the Apache 2.0 License.