# ThetaImageServer
English | [日本語](README-ja.md)

ThetaImageServer is a server application that generates color and depth images from a RICOH THETA camera and outputs them as a virtual camera. By running `server.py`, it outputs a combined image (2048x512) with RGB and depth images side by side as a virtual camera named "THETA Depth Camera".

Depth images are generated using [UniFuse](https://github.com/alibaba/UniFuse-Unidirectional-Fusion).

## Features

- Real-time color image acquisition from RICOH THETA camera
- High-precision monocular depth estimation using UniFuse model
- Combined RGB and depth image output (2048x512)
- Virtual camera output using pyvirtualcam
- Compatible with VRChat's TopazChat Player

## Requirements

- Python 3.8 or higher
- RICOH THETA camera (USB connection)
- THETA UVC Driver for Windows ([Download](https://support.ricoh360.com/ja/app-download))
- Dependencies listed in `requirements.txt`
- OBS Studio or pyvirtualcam-compatible virtual camera driver

## Setup

1. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2. **Install THETA UVC Driver**:
   - Download and install from [RICOH THETA UVC Driver](https://support.ricoh360.com/ja/app-download)

3. **Install OBS Studio** (recommended):
   - Download from https://obsproject.com/
   - pyvirtualcam uses it as a virtual camera backend

4. **Connect THETA camera**:
   - Connect THETA camera to PC via USB
   - Verify the camera is recognized as a webcam

## Usage

### Basic Startup

```bash
python server.py --camera 0
```

- `--camera 0`: Camera device ID (typically 0 or 1)
- On first run, the UniFuse model checkpoint will be automatically downloaded
- Once the server starts, a virtual camera named "THETA Depth Camera" becomes available

### Output Format

- **Resolution**: 2048x512 pixels
- **Layout**: `[RGB image 1024x512 | Depth image 1024x512]`
- **Frame rate**: 30 FPS (target)
- **Depth image**: Grayscale (0-255), representing 0-20 meters range

### Integration with TopazChat Player

1. Start server.py
2. Open TopazChat Player settings in VRChat/Unity
3. Select "THETA Depth Camera" as the camera device
4. The combined image will be streamed

## Troubleshooting

### Camera not recognized
- Verify THETA UVC Driver is properly installed
- Check if the camera is recognized in Device Manager
- Try changing the `--camera` value (0, 1, 2, etc.)

### Virtual camera not appearing
- Verify OBS Studio is installed
- Check if OBS Virtual Camera is enabled
- Try running Python with administrator privileges

### Poor performance
- Verify CUDA is available (GPU acceleration)
- Check if GPU is recognized with `torch.cuda.is_available()`

## Notes

- GPU (CUDA) is recommended for depth estimation
- First run may take several minutes to download the model
- Virtual camera can only be used by one application at a time

## Acknowledgement

**We sincerely appreciate the following research, code, and datasets that made this project possible:**

- [Depth Anywhere](https://github.com/albert100121/Depth-Anywhere)
- [Depth Anything](https://github.com/LiheYoung/Depth-Anything/tree/main)
- [UniFuse](https://github.com/alibaba/UniFuse-Unidirectional-Fusion)
- [py360converter](https://github.com/sunset1995/py360convert)

