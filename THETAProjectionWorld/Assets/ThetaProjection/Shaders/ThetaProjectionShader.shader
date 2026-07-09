Shader "ThetaProjection/EquirectangularRGBDepth"
{
    Properties
    {
        _MainTex ("Combined Texture (RGB|Depth)", 2D) = "white" {}
        _DepthScale ("Depth Scale", Range(0, 2)) = 1.0
        _MaxDepth ("Max Depth (meters)", Range(0.1, 10)) = 5.0
        _ShowDepth ("Show Depth (0=RGB, 1=Depth)", Range(0, 1)) = 0
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" }
        LOD 100

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
            };

            struct v2f
            {
                float2 uv : TEXCOORD0;
                UNITY_FOG_COORDS(1)
                float4 vertex : SV_POSITION;
            };

            sampler2D _MainTex;
            float4 _MainTex_ST;
            float _DepthScale;
            float _MaxDepth;
            float _ShowDepth;

            v2f vert (appdata v)
            {
                v2f o;
                o.vertex = UnityObjectToClipPos(v.vertex);
                o.uv = TRANSFORM_TEX(v.uv, _MainTex);
                UNITY_TRANSFER_FOG(o,o.vertex);
                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                // 結合画像から適切な部分をサンプリング
                // 左半分: RGB (u: 0-0.5)
                // 右半分: Depth (u: 0.5-1.0)

                float2 rgbUV = float2(i.uv.x * 0.5, i.uv.y);
                float2 depthUV = float2(0.5 + i.uv.x * 0.5, i.uv.y);

                fixed4 rgbColor = tex2D(_MainTex, rgbUV);
                fixed4 depthColor = tex2D(_MainTex, depthUV);

                // 表示モードに応じて出力
                fixed4 col = lerp(rgbColor, depthColor, _ShowDepth);

                UNITY_APPLY_FOG(i.fogCoord, col);
                return col;
            }
            ENDCG
        }
    }
}
