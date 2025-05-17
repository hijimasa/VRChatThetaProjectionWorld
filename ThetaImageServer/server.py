# test.py
import argparse
import threading, time
import cv2
from flask import Flask, Response

import argparse
import sys
import os
import urllib.request
import zipfile
from typing import List

import numpy as np
import torch
from torchvision import transforms
from tqdm import tqdm

from baseline_models.UniFuse.networks import UniFuse
from utils.Projection import py360_E2C

np.bool = np.bool_
np.float = np.float32
MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]

app = Flask(__name__)
lock = threading.Lock()
latest_frame = None

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
        sys.stderr.write(f'Error downloading checkpoint: {e}\n', file=sys.stderr)
        sys.exit(1)
    sys.stderr.write('Download complete. Extracting files...\n')
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(ckpt_dir)
    except zipfile.BadZipFile as e:
        sys.stderr.write(f'Error unpacking zip file: {e}\n', file=sys.stderr)
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

to_tensor  = transforms.ToTensor()
normalize  = transforms.Normalize(mean=MEAN, std=STD)
E2C = py360_E2C(equ_h=512, equ_w=1024, face_w=512//2)


def capture_thread(index: int):
    global latest_frame

    # 1) DirectShow → MSMF の順で試す
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(index, cv2.CAP_MSMF)
    if not cap.isOpened():
        raise IOError(f"Cannot open camera at index {index} with DSHOW/MSMF")

    # 3) 最初の１フレームで「本当に返ってくる解像度」を確認
    ret, frame = cap.read()
    if not ret:
        cap.release()
        raise IOError("Cannot read a frame from the camera")
    h, w = frame.shape[:2]
    print(f"[INFO] Camera opened at index={index}, actual resolution={w}x{h}")
    cv2.resize(frame, dsize=(1024,512))
    frame = cv2.flip(frame, 1)

    # 4) 共有変数にプッシュ
    with lock:
        latest_frame = frame

    # 5) 以降ループでキャプチャ
    while True:
        ret, frame = cap.read()
        cv2.resize(frame, dsize=(1024,512))
        frame = cv2.flip(frame, 1)
        if not ret:
            time.sleep(0.01)
            continue
        with lock:
            latest_frame = frame
        time.sleep(0.005)


def gen_mjpeg(raw: bool):
    """raw=True ならそのまま、False なら Canny エッジを載せて出力"""
    global latest_frame
    while True:
        if latest_frame is None:
            time.sleep(0.01)
            continue
        with lock:
            img = latest_frame.copy()
        if not raw:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img_rgb = cv2.resize(img_rgb, (1024, 512), interpolation=cv2.INTER_CUBIC)
            rgb_t = normalize(to_tensor(img_rgb)).unsqueeze(0).to(device)   # 1×3×H×W

            with torch.no_grad():
                cube = E2C.run(img_rgb)
                cube_t = normalize(to_tensor(cube)).unsqueeze(0).to(device)
                out = model(rgb_t, cube_t)
            depth = out['pred_depth'].squeeze().cpu().numpy()
            depth = (np.clip(depth, 0.0, 5.0) / 5.0 * 255.0).astype(np.uint8)
            img   = cv2.cvtColor(depth, cv2.COLOR_GRAY2BGR)
        ret, jpeg = cv2.imencode('.jpg', img)
        if not ret:
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               jpeg.tobytes() + b'\r\n')


@app.route('/raw')
def raw_feed():
    return Response(gen_mjpeg(raw=True),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/processed')
def processed_feed():
    return Response(gen_mjpeg(raw=False),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--index', type=int, default=0,
                   help="接続された UVC デバイスのインデックス番号（例: 0,1,2…）")
    args = p.parse_args()


    # キャプチャスレッド起動
    t = threading.Thread(target=capture_thread,
                         args=(args.index, ),
                         daemon=True)
    t.start()

    # Flask サーバー起動
    app.run(host='0.0.0.0', port=5000, threaded=True)
