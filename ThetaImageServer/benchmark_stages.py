# benchmark_stages.py - server.py の各処理ステージの時間を計測する(カメラ不要)
#
# 使い方:
#   python benchmark_stages.py                # 自動選択デバイス(CUDAがあればCUDA)
#   BENCH_DEVICE=cpu python benchmark_stages.py   # CPU強制
import os
import time

import cv2
import numpy as np
import torch

from server import (RemapE2C, to_nchw_normalized, build_unifuse,
                    OUTPUT_WIDTH, OUTPUT_HEIGHT)

N = 30
device = os.environ.get("BENCH_DEVICE") or ("cuda" if torch.cuda.is_available() else "cpu")
print(f"device: {device}")

model = build_unifuse(OUTPUT_HEIGHT, OUTPUT_WIDTH).to(device)
E2C = RemapE2C(equ_h=OUTPUT_HEIGHT, equ_w=OUTPUT_WIDTH, face_w=OUTPUT_HEIGHT // 2)

# 疑似カメラフレーム (1920x960 RGB)
rng = np.random.default_rng(0)
raw = rng.integers(0, 255, size=(960, 1920, 3), dtype=np.uint8)


def bench(label, fn, n=N):
    for _ in range(3):
        fn()
    if device == "cuda":
        torch.cuda.synchronize()
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    if device == "cuda":
        torch.cuda.synchronize()
    dt = (time.perf_counter() - t0) / n * 1000
    print(f"{label:42s} {dt:8.2f} ms")
    return dt


total = 0.0

frame = cv2.resize(raw, dsize=(OUTPUT_WIDTH, OUTPUT_HEIGHT))
total += bench("1. resize 1920x960 -> 1024x512 + flip",
               lambda: cv2.flip(cv2.resize(raw, dsize=(OUTPUT_WIDTH, OUTPUT_HEIGHT)), 1))

cube = E2C.run(frame)
total += bench("2. E2C (cv2.remap)", lambda: E2C.run(frame))

total += bench("3. normalize x2 (equi + cube)",
               lambda: (to_nchw_normalized(frame), to_nchw_normalized(cube)))

equi_t = torch.from_numpy(to_nchw_normalized(frame)).to(device)
cube_t = torch.from_numpy(to_nchw_normalized(cube)).to(device)


def infer():
    with torch.no_grad():
        return model(equi_t, cube_t)


out = infer()
total += bench("4. UniFuse inference", infer)
total += bench("5. pred_depth .cpu().numpy()",
               lambda: out["pred_depth"].squeeze().cpu().numpy())

depth = out["pred_depth"].squeeze().cpu().numpy()
total += bench("6. clip/scale + GRAY2RGB + hstack", lambda: np.hstack(
    [frame, cv2.cvtColor((np.clip(depth, 0.0, 20.0) / 20.0 * 255.0).astype(np.uint8),
                         cv2.COLOR_GRAY2RGB)]))

print("-" * 55)
print(f"{'TOTAL (excl. camera read & vcam send)':42s} {total:8.2f} ms"
      f"  -> {1000 / total:.1f} FPS upper bound")

# 参考: 旧実装のscipy版E2C (要scipy)
try:
    from utils.Projection.py360converter import Equirec2Cube as ScipyE2C
    scipy_e2c = ScipyE2C(OUTPUT_HEIGHT, OUTPUT_WIDTH, OUTPUT_HEIGHT // 2)
    bench("ref: legacy E2C (scipy map_coordinates)", lambda: scipy_e2c.run(frame))
except ImportError:
    print("(scipy not installed - legacy E2C reference skipped)")
