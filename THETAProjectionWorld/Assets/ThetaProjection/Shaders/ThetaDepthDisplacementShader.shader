Shader "ThetaProjection/DepthDisplacement"
{
    // GPU側で深度に基づいた頂点変形を行うシェーダー
    // CPU側のメッシュ変形より高速
    //
    // 入力テクスチャ: 2048x512 [RGB 1024x512 | Depth 1024x512]
    // 深度値: サーバー(server.py)が送る線形深度 0=0m(黒) 〜 255=20m(白)
    // 半径への変換: radius = _DepthScale / (depthValue * 20 / 255)
    //   (深度値に反比例。_DepthScaleで全体のスケール感を調整する)
    Properties
    {
        _MainTex ("Combined Texture (RGB|Depth)", 2D) = "white" {}
        _DepthScale ("Depth Scale", Range(0, 5)) = 2.0
        _MinRadius ("Minimum Radius", Range(0.1, 5)) = 0.1
        [Toggle] _FlipY_Depth ("Flip Y for Depth sampling", Float) = 0
        [Toggle] _FlipY_RGB ("Flip Y for RGB display", Float) = 0
        [Toggle] _EdgeClip ("Clip Stretched Edges", Float) = 1
        _EdgeClipRatio ("Edge Clip Radius Ratio", Range(1.05, 5)) = 1.6
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" }
        LOD 200

        // 内側から見る場合のためにカリングを無効化
        Cull Off

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog

            #include "UnityCG.cginc"

            struct appdata
            {
                float4 vertex : POSITION;
                float2 uv : TEXCOORD0;
                float3 normal : NORMAL;
            };

            struct v2f
            {
                float2 uv : TEXCOORD0;
                float depth : TEXCOORD1;
                float stretch : TEXCOORD2;
                UNITY_FOG_COORDS(3)
                float4 vertex : SV_POSITION;
            };

            sampler2D _MainTex;
            float4 _MainTex_ST;
            float4 _MainTex_TexelSize;
            float _DepthScale;
            float _MinRadius;
            float _FlipY_Depth;
            float _FlipY_RGB;
            float _EdgeClip;
            float _EdgeClipRatio;

            // 深度テクスチャ(右半分)からサンプリング
            // u,vv はメッシュUV空間([0,1])。Equirectangular境界(u=0/u=1は同じ経度)をブレンド処理する
            float sampleDepthValue(float u, float vv)
            {
                float y = _FlipY_Depth > 0.5 ? vv : (1.0 - vv);
                float blendWidth = 0.02; // ブレンド幅（2%）

                if (u < blendWidth)
                {
                    // 左端近傍: 左端(u=0)と右端(u=1)をブレンド
                    float t = u / blendWidth; // 0→1
                    float2 uvLeft = float2(0.5 + u * 0.5, y);
                    float2 uvRight = float2(0.5 + (1.0 - blendWidth + u) * 0.5, y);

                    float depthLeft = tex2Dlod(_MainTex, float4(uvLeft, 0, 0)).r;
                    float depthRight = tex2Dlod(_MainTex, float4(uvRight, 0, 0)).r;
                    return lerp(depthRight, depthLeft, t);
                }
                else if (u > 1.0 - blendWidth)
                {
                    // 右端近傍: 右端(u=1)と左端(u=0)をブレンド
                    float t = (u - (1.0 - blendWidth)) / blendWidth; // 0→1
                    float2 uvLeft = float2(0.5 + (u - 1.0 + blendWidth) * 0.5, y);
                    float2 uvRight = float2(0.5 + u * 0.5, y);

                    float depthLeft = tex2Dlod(_MainTex, float4(uvLeft, 0, 0)).r;
                    float depthRight = tex2Dlod(_MainTex, float4(uvRight, 0, 0)).r;
                    return lerp(depthRight, depthLeft, t);
                }
                else
                {
                    // 中央部: 通常のサンプリング
                    float2 depthUV = float2(0.5 + u * 0.5, y);
                    return tex2Dlod(_MainTex, float4(depthUV, 0, 0)).r;
                }
            }

            // 深度値 → 変形後の半径
            float radiusAt(float u, float vv)
            {
                float depthValue = sampleDepthValue(u, vv);
                float depthNormalized = depthValue * 20 / 255.0;
                float depthMeters = _DepthScale / (depthNormalized + 0.000001); // avoid division by zero
                return max(depthMeters, _MinRadius);
            }

            v2f vert (appdata v)
            {
                v2f o;

                float u = v.uv.x;
                float newRadius = radiusAt(u, v.uv.y);

                // 頂点を深度に基づいて変形
                // 深度値が小さい → 半径大、深度値が大きい → 半径小 (radius = _DepthScale / depth)
                float3 direction = normalize(v.vertex.xyz);
                float3 displacedVertex = direction * newRadius;

                // 深度不連続(物体輪郭)の検出:
                // 深度テクスチャ2テクセル分だけ離れた近傍と半径を比較し、
                // 比が大きい箇所 = 前景と背景をまたいで引き伸ばされる三角形をマークする。
                // フラグメント側で_EdgeClipRatioを超えた部分をclipして「ゴム膜」状の
                // スミアを除去する(単一視点キャプチャの隠蔽領域なので正しい色は存在しない)
                float du = 4.0 * _MainTex_TexelSize.x; // 深度2テクセル (メッシュu空間)
                float dv = 2.0 * _MainTex_TexelSize.y; // 深度2テクセル (メッシュv空間)
                float rL = radiusAt(frac(u - du + 1.0), v.uv.y);
                float rR = radiusAt(frac(u + du), v.uv.y);
                float rD = radiusAt(u, saturate(v.uv.y - dv));
                float rU = radiusAt(u, saturate(v.uv.y + dv));
                float rMin = min(newRadius, min(min(rL, rR), min(rD, rU)));
                float rMax = max(newRadius, max(max(rL, rR), max(rD, rU)));
                o.stretch = rMax / max(rMin, 0.0001);

                o.vertex = UnityObjectToClipPos(float4(displacedVertex, 1.0));
                o.uv = TRANSFORM_TEX(v.uv, _MainTex);
                o.depth = sampleDepthValue(u, v.uv.y) * 20 / 255.0;
                UNITY_TRANSFER_FOG(o, o.vertex);
                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                // 深度不連続をまたいで引き伸ばされた三角形を除去
                // (頂点シェーダーで計算したstretch=近傍半径比がしきい値を超えた部分)
                if (_EdgeClip > 0.5)
                {
                    clip(_EdgeClipRatio - i.stretch);
                }

                // RGB画像をサンプリング（左半分）
                // Equirectangular境界処理: u=0とu=1は同じ経度
                float u = i.uv.x;
                float blendWidth = 0.02; // 深度と同じブレンド幅
                fixed4 col;
                
                float y = _FlipY_RGB > 0.5 ? i.uv.y : (1.0 - i.uv.y);
                
                if (u < blendWidth)
                {
                    // 左端近傍: 左端(u=0→x=0.0)と右端(u=1→x=0.5)をブレンド
                    float t = u / blendWidth; // 0→1
                    float2 uvLeft = float2(u * 0.5, y); // 現在位置
                    float2 uvRight = float2(0.5 - (blendWidth - u) * 0.5, y); // 右端から対応する位置
                    
                    fixed4 colLeft = tex2D(_MainTex, uvLeft);
                    fixed4 colRight = tex2D(_MainTex, uvRight);
                    col = lerp(colRight, colLeft, t);
                }
                else if (u > 1.0 - blendWidth)
                {
                    // 右端近傍: 右端(u=1→x=0.5)と左端(u=0→x=0.0)をブレンド
                    float t = (u - (1.0 - blendWidth)) / blendWidth; // 0→1
                    float2 uvRight = float2(u * 0.5, y); // 現在位置
                    float2 uvLeft = float2((u - 1.0) * 0.5, y); // 左端から対応する位置
                    
                    fixed4 colLeft = tex2D(_MainTex, uvLeft);
                    fixed4 colRight = tex2D(_MainTex, uvRight);
                    col = lerp(colRight, colLeft, t);
                }
                else
                {
                    // 中央部: 通常のサンプリング
                    float2 rgbUV = float2(u * 0.5, y);
                    col = tex2D(_MainTex, rgbUV);
                }

                UNITY_APPLY_FOG(i.fogCoord, col);
                return col;
            }
            ENDCG
        }
    }
    FallBack "Diffuse"
}
