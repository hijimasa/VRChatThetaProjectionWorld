# THETA Projection for VRChat Worlds

[English](README.md) | 日本語

RICOH THETAカメラの360°映像+深度ストリームを、深度に応じて変形する球体として
任意のVRChatワールドに表示するアセットです。このフォルダは自己完結しており、
任意のワールドプロジェクトにフォルダごとコピー(または `.unitypackage` を
インポート)するだけで使えます。サードパーティ製アセットは含まれておらず、
ビデオプレイヤー(TopazChat Player等)は各自で用意します。

送信側(PC)は
[VRChatThetaProjectionWorld](https://github.com/hijimasa/VRChatThetaProjectionWorld)
リポジトリの `ThetaImageServer` を参照してください。2048x512の結合画像
(左: RGB 1024x512、右: 深度 1024x512)を配信します。

## 内容物

| パス | 説明 |
|---|---|
| `Shaders/ThetaDepthDisplacementShader.shader` | 頂点変形シェーダー(`ThetaProjection/DepthDisplacement`)。映像の深度側半分に基づいて球体を頂点単位で変形 |
| `Shaders/ThetaProjectionShader.shader` | 変形なしの単純なEquirectangular投影シェーダー |
| `Materials/ThetaProjectionScreen.mat` | 投影スフィア用のマテリアル(そのまま使用可) |
| `Meshes/UVSphere_seg512_ring256_r1.asset` | スクリーンとして使う512x256のUVスフィアメッシュ(深度マップ1024x512を2ピクセルごとにサンプリング) |
| `Meshes/UVSphere_seg128_ring64_r1.asset` | 低解像度の128x64スフィア(旧版・低スペック向け) |
| `Udon/ThetaProjectionSetup.cs` | ワールド内からシェーダーパラメータを調整するUdonSharpビヘイビア(任意) |
| `Editor/ThetaProjectionScreenTool.cs` | ワンクリックセットアップメニュー(下記参照) |
| `Editor/UVSphereMeshGenerator.cs` | 解像度を変えたUVスフィアを再生成するツール |

## 自分のワールドへの導入

必要なもの: VRChat SDK3 Worlds(UdonSharp同梱)と、スクリーンのRendererの
マテリアル(`_MainTex`)に映像テクスチャを書き込むタイプのビデオプレイヤー
(TopazChat Player、VRChat標準のAVProビデオスクリーン等)。

### TopazChat Player等(スクリーンオブジェクトを持つプレイヤー)の場合

1. この `ThetaProjection` フォルダ(または `.unitypackage`)をワールド
   プロジェクトにインポートします。
2. ビデオプレイヤーを通常どおりセットアップします(TopazChat Playerは
   [BOOTH](https://booth.pm/ja/items/1752066) から入手し、プレハブをシーンに
   配置)。
3. プレイヤーのスクリーンオブジェクトを選択します。TopazChat Playerの場合は
   プレハブ内の `Monitor` オブジェクトです。
4. メニューの **Tools > THETA Projection > Convert Selected Screen To
   Projection Sphere** を実行します。スクリーンのメッシュがUVスフィアに、
   マテリアルが `ThetaProjectionScreen.mat` に差し替わります。
   ビデオプレイヤー側のアセットは一切改変しません。
5. スクリーンオブジェクトの位置・スケールを好みに調整します(プレイヤーが
   球体の内側に立つ形になります)。

### スクリーンオブジェクトがない場合

**Tools > THETA Projection > Create Projection Screen In Scene** を実行し、
生成された `ThetaProjectionScreen` オブジェクトをビデオプレイヤーの映像出力先
(マテリアル/Rendererターゲット、テクスチャプロパティ `_MainTex`)に指定して
ください。

### 任意: ワールド内でのパラメータ調整

任意のGameObjectに `ThetaProjectionSetup` (UdonSharp)を追加し、
**Target Renderer** に投影スフィアのRendererを指定すると、深度スケール・
最小半径・Y反転をワールド内から調整できます。UIスライダー/ボタンからの操作にも
対応しています。

## シェーダーパラメータ

| プロパティ | 意味 | デフォルト |
|---|---|---|
| `_DepthScale` | 深度スケール係数(半径 = `_DepthScale` / 深度) | 0.02 |
| `_MinRadius` | 球体の最小半径[m] | 0.1 |
| `_FlipY_Depth` | 深度側サンプリング時のV反転 | 0 |
| `_FlipY_RGB` | RGB側表示時のV反転 | 1 |
| `_EdgeClip` | 深度不連続(物体輪郭)をまたいで引き伸ばされた三角形を除去。「ゴム膜」状のスミアが穴に変わる | 1 (有効) |
| `_EdgeClipRatio` | クリップ判定に使う近傍半径比のしきい値。小さいほど積極的に除去 | 1.6 |

## 再配布について

このフォルダの内容はすべてオリジナルの成果物で、Apache-2.0ライセンスです。
配布用パッケージの書き出しは **Tools > THETA Projection > Export
ThetaProjection.unitypackage** で行えます。
