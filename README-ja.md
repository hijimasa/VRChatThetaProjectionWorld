# VRChatThetaProjectionWorld
[English](README.md) | 日本語
## 概要

![](./figs/test.gif)

このプロジェクトは、THETAカメラによる単眼深度推定の結果をVRChatワールド内で可視化し、カラーマッピングで表示します。主に以下の2つのコンポーネントで構成されています。

- **ThetaImageServer**: THETAカメラからカラー画像と深度画像を生成・配信するサーバープログラム。
- **VRTest**: 配信された画像を受信し、深度データに基づいてメッシュを生成・表示するテストプロジェクト。

VRChatプロジェクトで重要なスクリプト（メッシュ変形など）は `Assets/Scenes` ディレクトリ直下に配置されています。

## はじめに

### 必要条件

- Windows
- Unity 2021.3 LTS 以降
- VRChat SDK3 (Worlds)
- Python 3.8以上（ThetaImageServer用）
- THETAカメラ（Z1またはV推奨）

### 事前準備

1. **THETA Windows向けUVC Driverのインストール**
   - [RICOH THETA UVC Driver](https://support.ricoh360.com/ja/app-download)からWindows版UVCドライバーをダウンロードしてインストールします。
   - THETAカメラをWebカメラとして認識させるために必要です。

2. **TopazChat Player 3.0の配置**
   - [TopazChat Player 3.0](https://booth.pm/ja/items/1752066)をBOOTHからダウンロードします。
   - ダウンロードしたzipファイルを解凍し、中身を `THETAProjectionWorld/Assets` ディレクトリに配置します。
   - TopazChat PlayerはVRChat内で動画ストリーミングを受信するために使用されます。

### セットアップ

1. **このリポジトリをクローン** します。
   ```bash
   git clone https://github.com/yourusername/VRChatThetaProjectionWorld.git
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
   - VRChat SDK3 (Worlds) をインポートします。
   - TopazChat Player 3.0のファイルが `Assets` 内に配置されていることを確認します。

## 使い方

### 1. ThetaImageServerの起動

```bash
cd ThetaImageServer
python server.py --camera 0
```

- `--camera 0`: カメラデバイスID（THETAを接続したデバイスID、通常0または1）
- サーバーが起動すると、RGB画像と深度画像を横に並べた結合画像（2048x512）が仮想カメラ「THETA Depth Camera」として出力されます。
- 初回起動時、UniFuseモデルのチェックポイントが自動的にダウンロードされます。

### 2. VRChatワールドでの表示

1. Unity Editorで `Assets/Scenes` のシーンを開きます。
2. TopazChat Playerで仮想カメラ「THETA Depth Camera」を選択します。
3. Playモードに入ると、深度データに基づくリアルタイムのメッシュ変形が表示されます。
4. Inspectorでパラメータを調整できます：
   - **Depth Scale**: 深度のスケール係数
   - **Sphere Radius**: 投影球の半径
   - **Min Radius**: 最小半径
   - **Flip Y**: 画像の上下反転

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
├── THETAProjectionWorld/      # Unityプロジェクト
│   └── Assets/
│       ├── Scenes/            # メインシーン
│       │   ├── ThetaDepthMeshDeformer.cs      # メッシュ変形スクリプト
│       │   └── ThetaDepthDisplacementShader.shader  # GPU変形シェーダー
│       └── Editor/
│           └── UVSphereMeshGenerator.cs  # メッシュ生成ツール
└── README.md
```

## ライセンス

本プロジェクトはApache 2.0ライセンスの下で公開されています。