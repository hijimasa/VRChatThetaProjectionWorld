# ThetaImageServer
English | [日本語](README-ja.md)

ThetaImageServer is a server application that streams both color and depth images captured from a RICOH THETA camera. By running `server.py`, you can access these images over the network.

The depth images are generated using source code from [Depth-Anywhere](https://github.com/albert100121/Depth-Anywhere). Copyright for the depth estimation component belongs to the authors of Depth-Anywhere.

## Features

- Streams real-time color images from a RICOH THETA camera.
- Generates and streams depth images using state-of-the-art monocular depth estimation.
- Simple server implementation in Python (`server.py`).
- Easy integration with other applications via network access.

## Requirements

- Python 3.8 or higher
- RICOH THETA camera (connected to the host machine)
- Dependencies listed in `requirements.txt`
- Pretrained models for Depth-Anywhere (see their repository for download instructions)

## Usage

1. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
2. Connect your RICOH THETA camera to your computer.
3. Download the required Depth-Anywhere model weights and place them in the appropriate directory.
4. Start the server:
    ```bash
    python server.py
    ```
5. Access the color and depth image streams via the provided network endpoints.

## Notes

- The depth estimation functionality is based on Depth-Anywhere. Please refer to their repository for details on model weights and usage.
- This repository includes code from Depth-Anywhere. The copyright for the depth estimation code belongs to the authors of Depth-Anywhere.

## Acknowledgement

**We sincerely appreciate the following research, code, and datasets that made this project possible:**

- [Depth Anywhere](https://github.com/albert100121/Depth-Anywhere)
- [Depth Anything](https://github.com/LiheYoung/Depth-Anything/tree/main)
- [UniFuse](https://github.com/alibaba/UniFuse-Unidirectional-Fusion)
- [py360converter](https://github.com/sunset1995/py360convert)

