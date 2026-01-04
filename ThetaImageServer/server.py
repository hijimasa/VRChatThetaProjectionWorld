# server.py - THETA Image Server with Virtual Camera Output
# RGB画像と深度画像を横に並べてpyvirtualcamで出力
import argparse
import time
import cv2

import sys
import os
import urllib.request
import zipfile

import numpy as np
import torch
from torchvision import transforms

from baseline_models.UniFuse.networks import UniFuse
from utils.Projection import py360_E2C

import pyvirtualcam

np.bool = np.bool_
np.float = np.float32
MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]

# 出力解像度設定
# RGB画像と深度画像を横に並べるため、幅は2倍
OUTPUT_WIDTH = 1024  # 各画像の幅
OUTPUT_HEIGHT = 512  # 各画像の高さ
COMBINED_WIDTH = OUTPUT_WIDTH * 2  # 並べた画像の幅 (2048)
FPS = 30

device = "cuda"

# Check if UniFuse directory exists in ckpt folder
CHECKPOINT_URL = "https://drive.usercontent.google.com/download?id=1yE555x5tvC3zJx_KxyuMKi4ok-joKpdg&export=download&authuser=0&confirm=t&uuid=9cd70cd3-82e1-4921-84cd-82add4216766&at=ALoNOglf-ccUjuZBaqROJcffZPJT%3A1747060462078"
ckpt_dir = os.path.join('checkpoints')
unifuse_dir = os.path.join('checkpoints', 'UniFuse')
if not os.path.exists(unifuse_dir):
    sys.stderr.write("UniFuse directory not found. Downloading checkpoint...\n")

    zip_path = os.path.join(ckpt_dir, 'checkpoint.zip')
    sys.stderr.write(f'Downloading checkpoint from {CHECKPOINT_URL} to {zip_path}...\n')
    try:
        urllib.request.urlretrieve(CHECKPOINT_URL, zip_path)
    except Exception as e:
        sys.stderr.write(f'Error downloading checkpoint: {e}\n')
        sys.exit(1)
    sys.stderr.write('Download complete. Extracting files...\n')
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(ckpt_dir)
    except zipfile.BadZipFile as e:
        sys.stderr.write(f'Error unpacking zip file: {e}\n')
        sys.exit(1)
    # ZIP を削除
    os.remove(zip_path)
    sys.stderr.write('Extraction complete and zip file removed.\n')
else:
    sys.stderr.write('UniFuse checkpoint already exists, skip download.\n')

# set arguments
model_dict = {
    'num_layers': 18,
    'equi_h': 512,
    'equi_w': 1024,
    'pretrained': True,
    'max_depth': 10.0,
    'fusion_type': 'cee',
    'se_in_fusion': True
}
model = UniFuse(**model_dict)
# to device
model.to(device)

# load pretrained weight
ckpt = torch.load("./checkpoints/UniFuse/UniFuse_SpatialAudioGen.pth")
model.load_state_dict(ckpt)
model.eval()

to_tensor = transforms.ToTensor()
normalize = transforms.Normalize(mean=MEAN, std=STD)
E2C = py360_E2C(equ_h=512, equ_w=1024, face_w=512//2)


def process_depth(img_rgb: np.ndarray) -> np.ndarray:
    """RGB画像から深度マップを生成"""
    img_resized = cv2.resize(img_rgb, (OUTPUT_WIDTH, OUTPUT_HEIGHT), interpolation=cv2.INTER_CUBIC)
    rgb_t = normalize(to_tensor(img_resized)).unsqueeze(0).to(device)

    with torch.no_grad():
        cube = E2C.run(img_resized)
        cube_t = normalize(to_tensor(cube)).unsqueeze(0).to(device)
        out = model(rgb_t, cube_t)

    depth = out['pred_depth'].squeeze().cpu().numpy()
    # 深度を0-255にスケール（最大10m）
    #depth = 2.0 / (depth + 1e-6)  # 逆数に変換
    #0.1 = 2.0 / 20.0
    depth_uint8 = (np.clip(depth, 0.0, 20.0) / 20.0 * 255.0).astype(np.uint8)
    #depth_uint8 = (np.clip(depth, 0.0, 5.0) / 5.0 * 255.0).astype(np.uint8)
    return depth_uint8


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--index', type=int, default=0,
                   help="接続された UVC デバイスのインデックス番号（例: 0,1,2…）")
    args = p.parse_args()

    print("=" * 60)
    print("THETA Image Server with Virtual Camera Output")
    print("=" * 60)
    print(f"Output: RGB ({OUTPUT_WIDTH}x{OUTPUT_HEIGHT}) + Depth ({OUTPUT_WIDTH}x{OUTPUT_HEIGHT})")
    print(f"Combined resolution: {COMBINED_WIDTH}x{OUTPUT_HEIGHT}")
    print("=" * 60)

    # カメラを開く
    cap = cv2.VideoCapture(args.index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(args.index, cv2.CAP_MSMF)
    if not cap.isOpened():
        raise IOError(f"Cannot open camera at index {args.index} with DSHOW/MSMF")

    # 最初の１フレームで解像度を確認
    ret, frame = cap.read()
    if not ret:
        cap.release()
        raise IOError("Cannot read a frame from the camera")
    h, w = frame.shape[:2]
    print(f"[INFO] Camera opened at index={args.index}, actual resolution={w}x{h}")

    # 仮想カメラを開く
    cam = pyvirtualcam.Camera(
        width=COMBINED_WIDTH,
        height=OUTPUT_HEIGHT,
        fps=FPS,
        fmt=pyvirtualcam.PixelFormat.RGB
    )
    print(f"[INFO] Virtual camera started: {cam.device}")

    frame_count = 0
    start_time = time.time()

    print("[INFO] Press Ctrl+C to stop")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            # リサイズと反転
            frame = cv2.resize(frame, dsize=(OUTPUT_WIDTH, OUTPUT_HEIGHT))
            frame = cv2.flip(frame, 1)

            # BGR → RGB 変換して深度推定
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            depth = process_depth(frame_rgb)

            # 深度画像を3チャンネルに変換（グレースケール→RGB）
            depth_rgb = cv2.cvtColor(depth, cv2.COLOR_GRAY2RGB)

            # RGB画像と深度画像を横に結合 [RGB | Depth]
            combined = np.hstack([frame_rgb, depth_rgb])

            # 仮想カメラに送信
            cam.send(combined)
            cam.sleep_until_next_frame()

            frame_count += 1

            # 10秒ごとにFPSを表示
            elapsed = time.time() - start_time
            if elapsed >= 10.0:
                fps = frame_count / elapsed
                print(f"[INFO] FPS: {fps:.1f}")
                frame_count = 0
                start_time = time.time()

    except KeyboardInterrupt:
        print("\n[INFO] Stopped by user")
    finally:
        cap.release()
        cam.close()
        print("[INFO] Camera and virtual camera closed")


if __name__ == '__main__':
    main()
