# ThetaImageServer
[English](README.md) | 日本語

ThetaImageServerは、RICOH THETAカメラで撮影したカラー画像と深度画像の両方をストリーミング配信するサーバーアプリケーションです。`server.py`を実行することで、これらの画像にネットワーク経由でアクセスできます。

深度画像は [Depth-Anywhere](https://github.com/albert100121/Depth-Anywhere) のソースコードを利用して生成されています。深度推定コンポーネントの著作権はDepth-Anywhereの作者に帰属します。

## 特徴

- RICOH THETAカメラからリアルタイムでカラー画像を配信
- 最先端の単眼深度推定を用いて深度画像を生成・配信
- シンプルなPython実装（`server.py`）
- ネットワーク経由で他アプリケーションとの連携が容易

## 必要条件

- Python 3.8以上
- RICOH THETAカメラ（ホストマシンに接続）
- `requirements.txt`に記載された依存パッケージ
- Depth-Anywhere用の事前学習済みモデル（ダウンロード方法は公式リポジトリ参照）

## 使い方

1. 依存パッケージをインストールします:
    ```bash
    pip install -r requirements.txt
    ```
2. RICOH THETAカメラをPCに接続します。
3. 必要なDepth-Anywhereのモデルウェイトをダウンロードし、所定のディレクトリに配置します。
4. サーバーを起動します:
    ```bash
    python server.py
    ```
5. ネットワークエンドポイント経由でカラー画像や深度画像のストリームにアクセスできます。

## 注意事項

- 深度推定機能はDepth-Anywhereに基づいています。モデルウェイトや使用方法の詳細は公式リポジトリを参照してください。
- 本リポジトリにはDepth-Anywhereのコードが含まれています。深度推定コードの著作権はDepth-Anywhereの作者に帰属します。

## 謝辞

**本プロジェクトの実現にあたり、以下の研究・コード・データセットに深く感謝いたします。**

- [Depth Anywhere](https://github.com/albert100121/Depth-Anywhere)
- [Depth Anything](https://github.com/LiheYoung/Depth-Anything/tree/main)
- [UniFuse](https://github.com/alibaba/UniFuse-Unidirectional-Fusion)
- [py360converter](https://github.com/sunset1995/py360convert)