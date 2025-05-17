# test.py
import argparse
import threading
import time
import cv2
from flask import Flask, Response

import numpy as np
import torch
from torchvision import transforms

from baseline_models.UniFuse.networks import UniFuse
from utils.Projection import py360_E2C

np.bool = np.bool_
np.float = np.float32
MEAN = [0.485, 0.456, 0.406]
STD  = [0.229, 0.224, 0.225]

app = Flask(__name__)
lock = threading.Lock()
latest_frame = None
scale = 1.0

device = "cuda"

# --- モデル初期化 ---
model_dict = {
    'num_layers': 18,
    'equi_h': 512,
    'equi_w': 1024,
    'pretrained': True,
    'max_depth': 10.0,
    'fusion_type': 'cee',
    'se_in_fusion': True
}
model = UniFuse(**model_dict).to(device)
ckpt = torch.load("./checkpoints/UniFuse/UniFuse_SpatialAudioGen.pth")
model.load_state_dict(ckpt)
model.eval()

to_tensor  = transforms.ToTensor()
normalize  = transforms.Normalize(mean=MEAN, std=STD)
E2C = py360_E2C(equ_h=512, equ_w=1024, face_w=512//2)


def capture_thread(index: int):
    global latest_frame

    # DirectShow → MSMF の順でカメラを開く
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(index, cv2.CAP_MSMF)
    if not cap.isOpened():
        raise IOError(f"Cannot open camera at index {index}")

    # 一度リサイズ＆反転して共有変数に格納
    ret, frame = cap.read()
    if not ret:
        cap.release()
        raise IOError("Cannot read a frame from the camera")
    frame = cv2.resize(frame, (1024, 512))
    frame = cv2.flip(frame, 1)
    with lock:
        latest_frame = frame

    # 以降ループで更新
    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.01)
            continue
        frame = cv2.resize(frame, (1024, 512))
        frame = cv2.flip(frame, 1)
        with lock:
            latest_frame = frame
        time.sleep(0.005)


def make_processed(img: np.ndarray) -> np.ndarray:
    """深度推定して可視化 PNG 用に BGR 画像を返す"""
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    rgb_t   = normalize(to_tensor(img_rgb)).unsqueeze(0).to(device)

    with torch.no_grad():
        cube = E2C.run(img_rgb)
        cube_t = normalize(to_tensor(cube)).unsqueeze(0).to(device)
        out = model(rgb_t, cube_t)
    depth = out['pred_depth'].squeeze().cpu().numpy()
    depth_norm = np.clip(depth, 0.0, 10.0) / 10.0
    max24 = 2**24 - 1
    packed = (depth_norm * max24).astype(np.uint32)
    r = ((packed >> 16) & 0xFF).astype(np.uint8)
    g = ((packed >>  8) & 0xFF).astype(np.uint8)
    b = ( packed        & 0xFF).astype(np.uint8)
    return cv2.merge((b, g, r))


@app.route('/raw.png')
def raw_png():
    """最新フレームをそのまま PNG で返す"""
    with lock:
        if latest_frame is None:
            return Response(status=204)
        img = latest_frame.copy()

    ret, png = cv2.imencode('.png', img)
    if not ret:
        return Response(status=500)
    return Response(png.tobytes(), mimetype='image/png')


@app.route('/processed.png')
def processed_png():
    """深度推定結果を PNG で返す"""
    with lock:
        if latest_frame is None:
            return Response(status=204)
        img = latest_frame.copy()

    proc = make_processed(img)
    ret, png = cv2.imencode('.png', proc)
    if not ret:
        return Response(status=500)
    return Response(png.tobytes(), mimetype='image/png')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--index', type=int, default=0,
                   help="接続された UVC デバイスのインデックス番号（例: 0,1,2…）")
    p.add_argument('--scale', type=float, default=1.0,
                   help="カメラの解像度スケール（例: 1.0, 0.5, 0.25）")
    args = p.parse_args()

    # キャプチャスレッド起動
    if args.index >= 0:
        t = threading.Thread(target=capture_thread,
                         args=(args.index, ),
                         daemon=True)
        t.start()
    else:
        latest_frame = cv2.imread("./data/examples/in-the-wild/rgb2.jpg")
        if latest_frame is None:
            raise IOError("Cannot read rgb1.jpg")
        else:
            latest_frame = cv2.resize(latest_frame, (1024, 512))
            latest_frame = cv2.flip(latest_frame, 1)
            print("Using test image instead of camera input.")

    # Flask サーバー起動
    app.run(host='0.0.0.0', port=5000)
