# ThetaImageServer
[English](README.md) | 日本語

ThetaImageServerは、RICOH THETAカメラで撮影したカラー画像と深度画像を生成し、仮想カメラとして出力するサーバーアプリケーションです。`server.py`を実行することで、RGB画像と深度画像を横に並べた結合画像（2048x512）を「THETA Depth Camera」という名前の仮想カメラとして出力します。

深度画像は [UniFuse](https://github.com/alibaba/UniFuse-Unidirectional-Fusion) を利用して生成されています。

## 特徴

- RICOH THETAカメラからリアルタイムでカラー画像を取得
- UniFuseモデルを用いた高精度な単眼深度推定
- RGB画像と深度画像を横に結合した出力（2048x512）
- pyvirtualcamを使った仮想カメラ出力
- VRChatのTopazChat Playerと連携可能

## 必要条件

- Python 3.8以上
- RICOH THETAカメラ（USB接続）
- THETA Windows向けUVC Driver（[ダウンロード](https://support.ricoh360.com/ja/app-download)）
- `requirements.txt`に記載された依存パッケージ
- OBS Studioまたはpyvirtualcam対応の仮想カメラドライバー

## セットアップ

1. **依存パッケージをインストール**:
    ```bash
    pip install -r requirements.txt
    ```

2. **THETA UVC Driverのインストール**:
   - [RICOH THETA UVC Driver](https://support.ricoh360.com/ja/app-download)からダウンロードしてインストール

3. **OBS Studioのインストール**（推奨）:
   - https://obsproject.com/ からダウンロード
   - pyvirtualcamが仮想カメラとして利用します

4. **THETAカメラを接続**:
   - THETAカメラをUSBでPCに接続
   - カメラがWebカメラとして認識されることを確認

## 使い方

### 基本的な起動

```bash
python server.py --camera 0
```

- `--camera 0`: カメラデバイスID（通常は0または1）
- 初回起動時、UniFuseモデルのチェックポイントが自動的にダウンロードされます
- サーバーが起動すると、「THETA Depth Camera」という名前の仮想カメラが利用可能になります

### 出力フォーマット

- **解像度**: 2048x512ピクセル
- **構成**: `[RGB画像 1024x512 | 深度画像 1024x512]`
- **フレームレート**: 30 FPS（目標）
- **深度画像**: グレースケール（0-255）、0-20メートルの範囲を表現

### TopazChat Playerとの連携

1. server.pyを起動
2. VRChat/Unityで、TopazChat Playerの設定を開く
3. カメラデバイスで「THETA Depth Camera」を選択
4. 結合画像がストリーミングされます

## トラブルシューティング

### カメラが認識されない
- THETA UVC Driverが正しくインストールされているか確認
- デバイスマネージャーでカメラが認識されているか確認
- `--camera` の値を変更してみる（0, 1, 2など）

### 仮想カメラが表示されない
- OBS Studioがインストールされているか確認
- OBS Virtual Cameraが有効になっているか確認
- Pythonを管理者権限で実行してみる

### パフォーマンスが低い
- CUDAが利用可能か確認（GPUアクセラレーション）
- `torch.cuda.is_available()`でGPUが認識されているか確認

## 注意事項

- 深度推定にはGPU（CUDA）を推奨します
- 初回起動時、モデルのダウンロードに数分かかる場合があります
- 仮想カメラは同時に1つのアプリケーションでのみ使用できます

## 謝辞

**本プロジェクトの実現にあたり、以下の研究・コード・データセットに深く感謝いたします。**

- [Depth Anywhere](https://github.com/albert100121/Depth-Anywhere)
- [Depth Anything](https://github.com/LiheYoung/Depth-Anything/tree/main)
- [UniFuse](https://github.com/alibaba/UniFuse-Unidirectional-Fusion)
- [py360converter](https://github.com/sunset1995/py360convert)