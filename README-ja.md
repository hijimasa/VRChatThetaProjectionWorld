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
python server.py --camera 0
```

- `--camera 0`: カメラデバイスID（THETAを接続したデバイスID、通常0または1）
- サーバーが起動すると、RGB画像と深度画像を横に並べた結合画像（2048x512）が仮想カメラ「THETA Depth Camera」として出力されます。
- 初回起動時、UniFuseモデルのチェックポイントが自動的にダウンロードされます。

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
