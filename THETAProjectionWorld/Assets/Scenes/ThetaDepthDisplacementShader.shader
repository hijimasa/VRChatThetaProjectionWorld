Shader "ThetaProjection/DepthDisplacement"
{
    // GPU側で深度に基づいた頂点変形を行うシェーダー
    // CPU側のメッシュ変形より高速
    //
    // 入力テクスチャ: 2048x512 [RGB 1024x512 | Depth 1024x512]
    // 深度値: 0=遠い(黒), 255=近い(白)
    Properties
    {
        _MainTex ("Combined Texture (RGB|Depth)", 2D) = "white" {}
        _DepthScale ("Depth Scale", Range(0, 5)) = 2.0
        _MinRadius ("Minimum Radius", Range(0.1, 5)) = 0.1
        [Toggle] _FlipY_Depth ("Flip Y for Depth sampling", Float) = 0
        [Toggle] _FlipY_RGB ("Flip Y for RGB display", Float) = 0
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
                UNITY_FOG_COORDS(2)
                float4 vertex : SV_POSITION;
            };

            sampler2D _MainTex;
            float4 _MainTex_ST;
            float4 _MainTex_TexelSize;
            float _DepthScale;
            float _MinRadius;
            float _FlipY_Depth;
            float _FlipY_RGB;

            v2f vert (appdata v)
            {
                v2f o;

                // 深度テクスチャからサンプリング（右半分）
                // Equirectangular境界処理: u=0とu=1は同じ経度
                float u = v.uv.x;
                
                // 境界近傍で左端(u≈0)と右端(u≈1)をブレンド
                float blendWidth = 0.02; // ブレンド幅（2%）
                float depthValue;
                
                if (u < blendWidth)
                {
                    // 左端近傍: 左端(u=0)と右端(u=1)をブレンド
                    float t = u / blendWidth; // 0→1
                    float2 uvLeft = float2(0.5 + u * 0.5, 0.0);
                    float2 uvRight = float2(0.5 + (1.0 - blendWidth + u) * 0.5, 0.0);
                    uvLeft.y = uvRight.y = _FlipY_Depth > 0.5 ? v.uv.y : (1.0 - v.uv.y);
                    
                    float depthLeft = tex2Dlod(_MainTex, float4(uvLeft, 0, 0)).r;
                    float depthRight = tex2Dlod(_MainTex, float4(uvRight, 0, 0)).r;
                    depthValue = lerp(depthRight, depthLeft, t);
                }
                else if (u > 1.0 - blendWidth)
                {
                    // 右端近傍: 右端(u=1)と左端(u=0)をブレンド
                    float t = (u - (1.0 - blendWidth)) / blendWidth; // 0→1
                    float2 uvLeft = float2(0.5 + (u - 1.0 + blendWidth) * 0.5, 0.0);
                    float2 uvRight = float2(0.5 + u * 0.5, 0.0);
                    uvLeft.y = uvRight.y = _FlipY_Depth > 0.5 ? v.uv.y : (1.0 - v.uv.y);
                    
                    float depthLeft = tex2Dlod(_MainTex, float4(uvLeft, 0, 0)).r;
                    float depthRight = tex2Dlod(_MainTex, float4(uvRight, 0, 0)).r;
                    depthValue = lerp(depthRight, depthLeft, t);
                }
                else
                {
                    // 中央部: 通常のサンプリング
                    float2 depthUV = float2(0.5 + u * 0.5, _FlipY_Depth > 0.5 ? v.uv.y : (1.0 - v.uv.y));
                    depthValue = tex2Dlod(_MainTex, float4(depthUV, 0, 0)).r;
                }

                // 深度値（グレースケール、0-20）
                float depthNormalized = depthValue * 20 / 255.0;

                float depthMeters = _DepthScale / (depthNormalized + 0.000001); // avoid division by zero

                // 頂点を深度に基づいて変形
                // 深度が小さい(近い) → 半径を大きく（手前に押し出す）
                // 深度が大きい(遠い) → 半径を小さく（奥に押し込む）
                float3 direction = normalize(v.vertex.xyz);
                float newRadius = depthMeters;
                newRadius = max(newRadius, _MinRadius);

                float3 displacedVertex = direction * newRadius;

                o.vertex = UnityObjectToClipPos(float4(displacedVertex, 1.0));
                o.uv = TRANSFORM_TEX(v.uv, _MainTex);
                o.depth = depthNormalized;
                UNITY_TRANSFER_FOG(o, o.vertex);
                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
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
