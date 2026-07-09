# server.py - THETA Image Server with Virtual Camera Output
# RGB画像と深度画像を横に並べてpyvirtualcamで出力
#
# 推論バックエンド:
#   - torch  : PyTorch (CUDA GPUがあれば使用)
#   - onnx   : ONNX Runtime (DirectML対応 = AMD/Intel/NVIDIAの任意のGPU、なければCPU)
#   - auto   : CUDA → DirectML → ONNX CPU → PyTorch CPU の順で自動選択(既定)
# CPU実行時は推論解像度を自動で半分(512x256)に落として速度を確保する。
import argparse
import os
import sys
import threading
import time
import urllib.request
import zipfile

import cv2
import numpy as np
import pyvirtualcam

# 出力解像度設定
# RGB画像と深度画像を横に並べるため、幅は2倍
OUTPUT_WIDTH = 1024  # 各画像の幅
OUTPUT_HEIGHT = 512  # 各画像の高さ
COMBINED_WIDTH = OUTPUT_WIDTH * 2  # 並べた画像の幅 (2048)
FPS = 30

MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

CHECKPOINT_URL = "https://drive.usercontent.google.com/download?id=1yE555x5tvC3zJx_KxyuMKi4ok-joKpdg&export=download&authuser=0&confirm=t&uuid=9cd70cd3-82e1-4921-84cd-82add4216766&at=ALoNOglf-ccUjuZBaqROJcffZPJT%3A1747060462078"
CKPT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "checkpoints")
UNIFUSE_DIR = os.path.join(CKPT_DIR, "UniFuse")
CKPT_PATH = os.path.join(UNIFUSE_DIR, "UniFuse_SpatialAudioGen.pth")

# UniFuse構築引数 (equi_h/equi_w は解像度に応じて実行時に決定)
MODEL_ARGS = dict(num_layers=18, pretrained=False, max_depth=10.0,
                  fusion_type="cee", se_in_fusion=True)

# シェーダー側と合わせた深度エンコード (0-20mを0-255へ)
DEPTH_MAX_METERS = 20.0


def download_checkpoint():
    if os.path.exists(UNIFUSE_DIR):
        sys.stderr.write("UniFuse checkpoint already exists, skip download.\n")
        return
    sys.stderr.write("UniFuse directory not found. Downloading checkpoint...\n")
    os.makedirs(CKPT_DIR, exist_ok=True)
    zip_path = os.path.join(CKPT_DIR, "checkpoint.zip")
    sys.stderr.write(f"Downloading checkpoint from {CHECKPOINT_URL} to {zip_path}...\n")
    try:
        urllib.request.urlretrieve(CHECKPOINT_URL, zip_path)
    except Exception as e:
        sys.stderr.write(f"Error downloading checkpoint: {e}\n")
        sys.exit(1)
    sys.stderr.write("Download complete. Extracting files...\n")
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(CKPT_DIR)
    except zipfile.BadZipFile as e:
        sys.stderr.write(f"Error unpacking zip file: {e}\n")
        sys.exit(1)
    os.remove(zip_path)
    sys.stderr.write("Extraction complete and zip file removed.\n")


class _LatestFrameGrabber:
    """カメラを専用スレッドで読み続け、常に最新フレーム(RGB)だけを保持する。

    メインループの処理速度に関係なくフレームを読み捨てるため、
    バックエンド内にフレームが滞留して映像が遅延することがない。
    """

    def __init__(self):
        self._frame = None
        self._seq = 0
        self._running = True
        self._cond = threading.Condition()
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def _start(self):
        self._thread.start()

    def _store(self, frame_rgb):
        with self._cond:
            self._frame = frame_rgb
            self._seq += 1
            self._cond.notify_all()

    def _loop(self):
        raise NotImplementedError

    def wait_frame(self, last_seq, timeout=1.0):
        """last_seqより新しいフレーム(RGB)が来るまで待って返す"""
        with self._cond:
            self._cond.wait_for(lambda: self._seq != last_seq or not self._running,
                                timeout=timeout)
            if self._seq == last_seq:
                return None, last_seq
            return self._frame, self._seq

    def release(self):
        self._running = False
        with self._cond:
            self._cond.notify_all()
        self._thread.join(timeout=2.0)
        self._close()

    def _close(self):
        pass


class AVGrabber(_LatestFrameGrabber):
    """PyAV(FFmpeg DirectShow)によるキャプチャ。

    OpenCVのMSMFバックエンド(フレーム変換に約60ms)より大幅に速い
    (実測: 97ms/フレーム → 44ms/フレーム)。
    """

    def __init__(self, device_name, width, height, fps):
        super().__init__()
        import av
        import av.logging
        av.logging.set_level(av.logging.ERROR)
        options = {"video_size": f"{width}x{height}",
                   "framerate": str(fps), "rtbufsize": "100M"}
        try:
            self.container = av.open(f"video={device_name}", format="dshow", options=options)
        except OSError:
            # 解像度/フレームレート指定が合わない場合はデバイス既定値で開く
            self.container = av.open(f"video={device_name}", format="dshow",
                                     options={"rtbufsize": "100M"})
        stream = self.container.streams.video[0]
        self.width = stream.width
        self.height = stream.height
        self.name = f"PyAV dshow ({device_name})"
        self._start()

    def _loop(self):
        stream = self.container.streams.video[0]
        for frame in self.container.decode(stream):
            if not self._running:
                break
            self._store(frame.to_ndarray(format="rgb24"))

    def _close(self):
        self.container.close()


class OpenCVGrabber(_LatestFrameGrabber):
    """OpenCV VideoCaptureによるキャプチャ(フォールバック)"""

    def __init__(self, index):
        super().__init__()
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(index, cv2.CAP_MSMF)
        if not cap.isOpened():
            raise IOError(f"Cannot open camera at index {index} with DSHOW/MSMF")
        ret, frame = cap.read()
        if not ret:
            cap.release()
            raise IOError("Cannot read a frame from the camera")
        self.cap = cap
        self.width = frame.shape[1]
        self.height = frame.shape[0]
        self.name = f"OpenCV (index={index})"
        self._start()

    def _loop(self):
        while self._running:
            ret, frame = self.cap.read()  # cap.read()は毎回新しい配列を返す
            if not ret:
                time.sleep(0.005)
                continue
            self._store(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    def _close(self):
        self.cap.release()


def open_grabber(args):
    if args.capture in ("auto", "av"):
        try:
            return AVGrabber(args.device_name, 1920, 960, FPS)
        except ImportError:
            if args.capture == "av":
                sys.stderr.write("ERROR: PyAV is not installed. pip install av\n")
                sys.exit(1)
            sys.stderr.write("[INFO] PyAV not installed, falling back to OpenCV capture. "
                             "'pip install av' is recommended for better FPS.\n")
        except OSError as e:
            if args.capture == "av":
                sys.stderr.write(f"ERROR: cannot open dshow device '{args.device_name}': {e}\n")
                sys.exit(1)
            sys.stderr.write(f"[INFO] dshow device '{args.device_name}' not found, "
                             "falling back to OpenCV capture.\n")
    return OpenCVGrabber(args.index)


class RemapE2C:
    """Equirectangular→キューブマップ変換 (事前計算マップ + cv2.remap)

    scipy map_coordinates版(約31ms/フレーム)と同じサンプリングを
    cv2.remap(約0.5ms/フレーム)で行う。
    """

    def __init__(self, equ_h, equ_w, face_w):
        from utils.Projection.py360converter import Equirec2Cube
        e2c = Equirec2Cube(equ_h, equ_w, face_w)
        self.equ_w = equ_w
        self.map_x = np.ascontiguousarray(e2c.coor_x[..., 0].astype(np.float32))
        self.map_y = np.ascontiguousarray(e2c.coor_y[..., 0].astype(np.float32))

    def run(self, img):
        # py360converterと同じ上下パディング(極の折り返し)を付けてBORDER_WRAPで
        # サンプリングすると、scipyのmode='wrap'と同一の結果になる
        pad_d = np.roll(img[-1:], self.equ_w // 2, axis=1)
        pad_u = np.roll(img[:1], self.equ_w // 2, axis=1)
        padded = np.concatenate([img, pad_d, pad_u], axis=0)
        return cv2.remap(padded, self.map_x, self.map_y,
                         interpolation=cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_WRAP)


def to_nchw_normalized(img_u8):
    """uint8 HWC画像 → 正規化済みfloat32 NCHW"""
    x = img_u8.astype(np.float32) * (1.0 / 255.0)
    x = (x - MEAN) / STD
    return np.ascontiguousarray(x.transpose(2, 0, 1)[None])


def load_unifuse_ckpt():
    import torch
    ckpt = torch.load(CKPT_PATH, map_location="cpu", weights_only=True)
    # sample_gridは解像度依存の固定バッファ(非学習)。現行実装ではstate_dictに
    # 含まれないため、旧形式チェックポイント内のエントリは除外して読み込む
    return {k: v for k, v in ckpt.items() if "sample_grid" not in k}


def build_unifuse(equ_h, equ_w):
    from baseline_models.UniFuse.networks import UniFuse
    model = UniFuse(equi_h=equ_h, equi_w=equ_w, **MODEL_ARGS)
    model.load_state_dict(load_unifuse_ckpt())
    model.eval()
    return model


class TorchBackend:
    def __init__(self, device, equ_h, equ_w):
        import torch
        self.torch = torch
        self.device = device
        self.model = build_unifuse(equ_h, equ_w).to(device)
        self.name = f"PyTorch ({device})"

    def infer(self, equi_u8, cube_u8):
        torch = self.torch
        equi = torch.from_numpy(to_nchw_normalized(equi_u8)).to(self.device)
        cube = torch.from_numpy(to_nchw_normalized(cube_u8)).to(self.device)
        with torch.no_grad():
            out = self.model(equi, cube)
        return out["pred_depth"].squeeze().float().cpu().numpy()


class OnnxBackend:
    def __init__(self, onnx_path, use_dml):
        import onnxruntime as ort
        providers = []
        if use_dml:
            providers.append("DmlExecutionProvider")
        providers.append("CPUExecutionProvider")
        self.sess = ort.InferenceSession(onnx_path, providers=providers)
        active = self.sess.get_providers()[0]
        self.is_gpu = active == "DmlExecutionProvider"
        self.name = f"ONNX Runtime ({'DirectML GPU' if self.is_gpu else 'CPU'})"

    def infer(self, equi_u8, cube_u8):
        depth = self.sess.run(None, {"equi": to_nchw_normalized(equi_u8),
                                     "cube": to_nchw_normalized(cube_u8)})[0]
        return np.squeeze(depth)


def onnx_model_path(equ_h, equ_w):
    return os.path.join(UNIFUSE_DIR, f"unifuse_{equ_w}x{equ_h}.onnx")


def export_onnx(equ_h, equ_w, path):
    """UniFuseをONNX形式にエクスポートする(PyTorchが必要)"""
    import torch
    import torch.nn as nn

    class UniFuseDepth(nn.Module):
        def __init__(self, model):
            super().__init__()
            self.model = model

        def forward(self, equi, cube):
            return self.model(equi, cube)["pred_depth"]

    model = UniFuseDepth(build_unifuse(equ_h, equ_w))
    equi = torch.zeros(1, 3, equ_h, equ_w)
    cube = torch.zeros(1, 3, equ_h // 2, equ_h // 2 * 6)
    sys.stderr.write(f"Exporting ONNX model ({equ_w}x{equ_h}) to {path}...\n")
    torch.onnx.export(model, (equi, cube), path,
                      input_names=["equi", "cube"], output_names=["depth"],
                      opset_version=17)
    sys.stderr.write("ONNX export complete.\n")


def _torch_cuda_available():
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return None  # torch自体がない


def _onnxruntime_info():
    try:
        import onnxruntime as ort
        return "DmlExecutionProvider" in ort.get_available_providers()
    except ImportError:
        return None  # onnxruntimeがない


def create_backend(args):
    """バックエンドと推論解像度を決定して構築する"""
    cuda = _torch_cuda_available()
    dml = _onnxruntime_info()
    has_torch = cuda is not None
    has_ort = dml is not None

    backend = args.backend
    if backend == "auto":
        if cuda:
            backend = "torch"
        elif has_ort:
            backend = "onnx"
        elif has_torch:
            backend = "torch"
        else:
            sys.stderr.write("ERROR: neither PyTorch nor onnxruntime is installed.\n")
            sys.exit(1)

    if backend == "torch":
        if not has_torch:
            sys.stderr.write("ERROR: PyTorch is not installed.\n")
            sys.exit(1)
        device = "cuda" if cuda else "cpu"
        gpu = cuda
    else:
        if not has_ort:
            sys.stderr.write("ERROR: onnxruntime is not installed. "
                             "pip install onnxruntime-directml (GPU) or onnxruntime (CPU)\n")
            sys.exit(1)
        gpu = dml

    # 推論解像度: GPUならフル(1024x512)、CPUなら半分(512x256)で速度を確保
    if args.infer_height:
        equ_h = args.infer_height
    else:
        equ_h = OUTPUT_HEIGHT if gpu else OUTPUT_HEIGHT // 2
    equ_w = equ_h * 2

    if backend == "torch":
        return TorchBackend(device, equ_h, equ_w), equ_h, equ_w

    path = onnx_model_path(equ_h, equ_w)
    if not os.path.exists(path):
        if not has_torch:
            sys.stderr.write(
                f"ERROR: ONNX model not found: {path}\n"
                "Run 'python server.py --export-onnx' once on a machine with PyTorch installed, \n"
                "then copy the .onnx file here.\n")
            sys.exit(1)
        export_onnx(equ_h, equ_w, path)
    return OnnxBackend(path, use_dml=dml), equ_h, equ_w


def main():
    p = argparse.ArgumentParser(description="THETA Image Server with Virtual Camera Output")
    p.add_argument("--index", "--camera", dest="index", type=int, default=0,
                   help="接続された UVC デバイスのインデックス番号（OpenCVキャプチャ時のみ使用）")
    p.add_argument("--capture", choices=["auto", "av", "opencv"], default="auto",
                   help="キャプチャ方式 (auto: PyAVがあればPyAV、なければOpenCV)")
    p.add_argument("--device-name", default="RICOH THETA UVC",
                   help="PyAVキャプチャ時のDirectShowデバイス名")
    p.add_argument("--backend", choices=["auto", "torch", "onnx"], default="auto",
                   help="推論バックエンド (auto: CUDA→DirectML→CPUの順で自動選択)")
    p.add_argument("--infer-height", type=int, default=None,
                   help="推論入力の高さ(幅は2倍)。省略時はGPU:512 / CPU:256")
    p.add_argument("--export-onnx", action="store_true",
                   help="ONNXモデルをエクスポートして終了(非NVIDIA機への配布用)")
    args = p.parse_args()

    download_checkpoint()

    if args.export_onnx:
        for h in ([args.infer_height] if args.infer_height else [OUTPUT_HEIGHT, OUTPUT_HEIGHT // 2]):
            path = onnx_model_path(h, h * 2)
            export_onnx(h, h * 2, path)
        return

    print("=" * 60)
    print("THETA Image Server with Virtual Camera Output")
    print("=" * 60)
    print(f"Output: RGB ({OUTPUT_WIDTH}x{OUTPUT_HEIGHT}) + Depth ({OUTPUT_WIDTH}x{OUTPUT_HEIGHT})")
    print(f"Combined resolution: {COMBINED_WIDTH}x{OUTPUT_HEIGHT}")
    print("=" * 60)

    backend, equ_h, equ_w = create_backend(args)
    print(f"[INFO] Inference backend: {backend.name}, input {equ_w}x{equ_h}")

    E2C = RemapE2C(equ_h=equ_h, equ_w=equ_w, face_w=equ_h // 2)

    grabber = open_grabber(args)
    print(f"[INFO] Camera opened via {grabber.name}, "
          f"actual resolution={grabber.width}x{grabber.height}")

    cam = pyvirtualcam.Camera(width=COMBINED_WIDTH, height=OUTPUT_HEIGHT,
                              fps=FPS, fmt=pyvirtualcam.PixelFormat.RGB)
    print(f"[INFO] Virtual camera started: {cam.device}")
    print("[INFO] Press Ctrl+C to stop")

    frame_count = 0
    start_time = time.time()
    t_wait = t_pre = t_e2c = t_infer = t_post = 0.0
    seq = 0

    try:
        while True:
            t0 = time.perf_counter()
            # 最新フレームを待つ(処理が遅れてもフレームは滞留しない)
            frame, seq = grabber.wait_frame(seq)
            if frame is None:
                continue
            t1 = time.perf_counter()

            # リサイズと反転 (フレームはグラバーからRGBで届く)
            frame_rgb = cv2.resize(frame, dsize=(OUTPUT_WIDTH, OUTPUT_HEIGHT))
            frame_rgb = cv2.flip(frame_rgb, 1)

            # 推論解像度へ縮小(出力解像度と同じ場合はそのまま)
            if equ_h != OUTPUT_HEIGHT:
                equi_in = cv2.resize(frame_rgb, (equ_w, equ_h), interpolation=cv2.INTER_AREA)
            else:
                equi_in = frame_rgb
            t2 = time.perf_counter()

            cube = E2C.run(equi_in)
            t3 = time.perf_counter()

            depth = backend.infer(equi_in, cube)
            t4 = time.perf_counter()

            # 深度を0-255にスケール（最大20m）
            depth_uint8 = (np.clip(depth, 0.0, DEPTH_MAX_METERS) / DEPTH_MAX_METERS * 255.0).astype(np.uint8)
            if depth_uint8.shape != (OUTPUT_HEIGHT, OUTPUT_WIDTH):
                depth_uint8 = cv2.resize(depth_uint8, (OUTPUT_WIDTH, OUTPUT_HEIGHT),
                                         interpolation=cv2.INTER_LINEAR)

            # RGB画像と深度画像を横に結合 [RGB | Depth] して仮想カメラに送信
            depth_rgb = cv2.cvtColor(depth_uint8, cv2.COLOR_GRAY2RGB)
            combined = np.hstack([frame_rgb, depth_rgb])
            cam.send(combined)
            t5 = time.perf_counter()

            frame_count += 1
            t_wait += t1 - t0
            t_pre += t2 - t1
            t_e2c += t3 - t2
            t_infer += t4 - t3
            t_post += t5 - t4

            # 10秒ごとにFPSと内訳を表示
            elapsed = time.time() - start_time
            if elapsed >= 10.0:
                n = max(frame_count, 1)
                print(f"[INFO] FPS: {frame_count / elapsed:.1f} "
                      f"(wait {t_wait / n * 1000:.0f}ms, pre {t_pre / n * 1000:.1f}ms, "
                      f"e2c {t_e2c / n * 1000:.1f}ms, infer {t_infer / n * 1000:.1f}ms, "
                      f"send {t_post / n * 1000:.1f}ms)")
                frame_count = 0
                t_wait = t_pre = t_e2c = t_infer = t_post = 0.0
                start_time = time.time()

    except KeyboardInterrupt:
        print("\n[INFO] Stopped by user")
    finally:
        grabber.release()
        cam.close()
        print("[INFO] Camera and virtual camera closed")


if __name__ == "__main__":
    main()
