# VRChatThetaProjectionWorld
[English](README.md) | 日本語

## 概要

![](./figs/test.gif)

このプロジェクトは、THETAカメラによる単眼深度推定の結果をVRChat内で可視化し、360°映像を深度に応じて変形する球体に投影します。主に以下の2つのコンポーネントで構成されています。

- **ThetaImageServer**: THETAカメラからカラー画像+深度画像の結合映像を生成・配信するサーバープログラム。
- **ThetaProjectionアセット** (`THETAProjectionWorld/Assets/ThetaProjection`): シェーダー・球体メッシュ・マテリアル・Udonビヘイビア(任意)・エディタツールをまとめた自己完結型のUnityアセットフォルダ。**任意のVRChatワールドプロジェクトにそのままコピーして使えます。**

**このリポジトリのワールドをそのまま使う必要はありません。** 推奨される使い方は、`ThetaProjection` フォルダ(またはエクスポートした `ThetaProjection.unitypackage`)を自分のワールドにコピーし、お好みのビデオプレイヤーと組み合わせる方法です。このリポジトリのUnityプロジェクトはサンプル兼開発用ワールドという位置づけです。

TopazChat Playerはサードパーティ製アセットのため、このリポジトリには**含まれていません**(また、改変する必要も一切ありません — `ThetaProjection` アセットは未改変のTopazChat Playerとそのまま組み合わせられます)。

## ThetaProjectionアセットを自分のワールドで使う

1. `THETAProjectionWorld/Assets/ThetaProjection` をワールドプロジェクトの `Assets` にコピーします(または `.unitypackage` をインポート)。VRChat SDK3 Worldsが必要です。
2. ビデオプレイヤーを通常どおりワールドにセットアップします。例: [TopazChat Player 3.0](https://booth.pm/ja/items/1752066)(BOOTHから各自入手)。
3. ビデオプレイヤーのスクリーンオブジェクトを選択します(TopazChat Playerの場合はプレハブ内の `Monitor` オブジェクト)。
4. Unityメニューの **Tools > THETA Projection > Convert Selected Screen To Projection Sphere** を実行します。スクリーンのメッシュとマテリアルが投影スフィア用に差し替わります。ビデオプレイヤー側のファイルは一切改変されません。

詳細(他のビデオプレイヤーとの組み合わせ、ワールド内でのパラメータ調整、シェーダーパラメータ、unitypackageのエクスポート)は [`THETAProjectionWorld/Assets/ThetaProjection/README-ja.md`](THETAProjectionWorld/Assets/ThetaProjection/README-ja.md) を参照してください。

## このリポジトリのサンプルワールドを動かす

### 必要条件

- Windows
- Unity 2022.3 LTS(VRChat Creator Companion経由)
- VRChat SDK3 (Worlds)
- Python 3.8以上(ThetaImageServer用)
- THETAカメラ(Z1またはV推奨)
- GPUは任意: NVIDIA(CUDA)、AMD/Intel(ONNX Runtime + DirectML)、CPUのみ、いずれでも動作します — [推論バックエンド](#推論バックエンド)参照

### 事前準備

1. **THETA Windows向けUVC Driverのインストール**
   - [RICOH THETA UVC Driver](https://support.ricoh360.com/ja/app-download)からWindows版UVCドライバーをダウンロードしてインストールします。
   - THETAカメラをWebカメラとして認識させるために必要です。

2. **TopazChat Player 3.0の配置**
   - [TopazChat Player 3.0](https://booth.pm/ja/items/1752066)をBOOTHからダウンロードします。
   - ダウンロードしたzipファイルを解凍し、中身を `THETAProjectionWorld/Assets` ディレクトリに配置します(改変は不要です)。
   - TopazChat PlayerはVRChat内で動画ストリーミングを受信するために使用されます。

### セットアップ

1. **このリポジトリをクローン** します。
   ```bash
   git clone https://github.com/hijimasa/VRChatThetaProjectionWorld.git
   cd VRChatThetaProjectionWorld
   ```

2. **Pythonパッケージのインストール**:
   ```bash
   cd ThetaImageServer
   pip install -r requirements.txt
   ```

3. **OBS Studioまたは仮想カメラソフトウェアのインストール**:
   - OBS Studio (推奨): https://obsproject.com/
   - または、pyvirtualcam対応の仮想カメラドライバー

4. **Unityプロジェクトのセットアップ**:
   - `THETAProjectionWorld` ディレクトリでUnityプロジェクトを開きます。
   - TopazChat Player 3.0のファイルが `Assets` 内に配置されていることを確認します。

## 使い方

### 1. ThetaImageServerの起動

```bash
cd ThetaImageServer
python server.py
```

- RGB画像と深度画像を横に並べた結合画像（2048x512）がOBS仮想カメラとして出力されます。
- 初回起動時、UniFuseモデルのチェックポイントが自動的にダウンロードされます。
- 10秒ごとにFPSとステージ別処理時間の内訳が表示されます。

オプション:

| オプション | 説明 |
|---|---|
| `--capture {auto,av,opencv}` | キャプチャ方式。`auto`はPyAV(FFmpeg DirectShow、約2〜3倍高速)があれば使用し、なければOpenCVにフォールバック |
| `--device-name NAME` | PyAVキャプチャ時のDirectShowデバイス名(既定: `RICOH THETA UVC`) |
| `--index N` / `--camera N` | OpenCVキャプチャ時のカメラインデックス(既定: 0) |
| `--backend {auto,torch,onnx}` | 推論バックエンド。`auto`はCUDA→DirectML→CPUの順で自動選択 |
| `--infer-height N` | 推論入力の高さ(幅は2倍)。既定はGPU:512 / CPU:256 |
| `--export-onnx` | ONNXモデルをエクスポートして終了(非NVIDIA機への配布用) |

#### 推論バックエンド

深度推定モデルは以下のいずれかで動作します(自動選択):

1. **PyTorch + CUDA** — NVIDIA GPU
2. **ONNX Runtime + DirectML** — DirectX 12対応の任意のGPU(AMD / Intel / NVIDIA)。GPD Pocket 4のようなノートPCのRadeon iGPUでも動作します: `pip install onnxruntime-directml`
3. **ONNX Runtime CPU / PyTorch CPU** — フレームレート確保のため推論解像度を自動で半分(512x256)に落とします

PyTorchを入れたくないマシン(小型ノートPC等)向けには、PyTorchのあるマシンで一度 `python server.py --export-onnx` を実行し(`pip install onnx`が必要)、生成された `checkpoints/UniFuse/*.onnx` をコピーしてください。実行側は `onnxruntime-directml` だけで動きます。

### 2. VRChatワールドでの表示

1. Unity Editorで `Assets/Scenes` のシーンを開きます。
2. TopazChat Playerで仮想カメラ「THETA Depth Camera」を選択します。
3. Playモードに入ると、深度データに基づくリアルタイムのメッシュ変形が表示されます。
4. `ThetaProjectionScreen` マテリアル(`Assets/ThetaProjection/Materials`)でパラメータを調整できます：
   - **Depth Scale**: 深度のスケール係数
   - **Minimum Radius**: 球体の最小半径
   - **Flip Y for Depth/RGB**: 画像の上下反転

### 3. VRChatへのアップロード

1. VRChat SDKのControl Panelからワールドをビルド＆アップロードします。
2. VRChat内で、TopazChat Playerの設定で仮想カメラを選択します。

## ディレクトリ構成

```
VRChatThetaProjectionWorld/
├── ThetaImageServer/           # THETA画像処理サーバー
│   ├── server.py              # メインサーバースクリプト
│   ├── requirements.txt       # Python依存パッケージ
│   ├── baseline_models/       # UniFuse深度推定モデル
│   ├── utils/                 # ユーティリティ（Equirectangular変換など）
│   └── checkpoints/           # モデルチェックポイント（自動ダウンロード）
├── THETAProjectionWorld/      # サンプルUnityワールドプロジェクト
│   └── Assets/
│       ├── ThetaProjection/   # ★ 配布用アセット — これを自分のワールドにコピー
│       │   ├── Shaders/       # 深度変形/投影シェーダー
│       │   ├── Materials/     # ThetaProjectionScreen.mat
│       │   ├── Meshes/        # UVスフィアメッシュ
│       │   ├── Udon/          # ワールド内パラメータ調整(任意)
│       │   └── Editor/        # ワンクリックセットアップ/エクスポートツール
│       └── Scenes/            # サンプルワールドシーン
└── README.md
```

## ライセンス

本プロジェクトはApache 2.0ライセンスの下で公開されています。(TopazChat Playerは別途サードパーティの著作物であり、本ライセンスの対象外です。)
