# VRChatThetaProjectionWorld
[English](README.md) | 日本語
## 概要

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

### セットアップ

1. **このリポジトリをクローン** します。
2. `VRTest` ディレクトリで **Unityプロジェクトを開きます**。
3. **VRChat SDK** をまだ導入していない場合はインポートします。
4. **ThetaImageServerの設定**:
    - 必要なPythonパッケージをインストールします:  
      ```bash
      pip install -r requirements.txt
      ```
    - THETAカメラを接続し、サーバーを起動します:
      ```bash
      cd ThetaImageServer
      python server.py
      ```
5. `Assets/Scenes` のUnityシーンを実行し、メッシュの可視化をテストします。

## 使い方

- ThetaImageServerを起動して画像配信を開始します。
- UnityでPlayモードに入り、深度データに基づくリアルタイムのメッシュ変形を確認します。
- Unityのインスペクターでメッシュやカラーマッピングのパラメータを調整できます。

## ディレクトリ構成

```
VRChatThetaProjectionWorld/
├── ThetaImageServer/    # Python server for image streaming
├── VRTest/              # Unity project for visualization
└── README.md
```

## ライセンス

本プロジェクトはApache 2.0ライセンスの下で公開されています。