Shader "Custom/VertexDisplacementWithColor"
{
    Properties
    {
        _HeightMap("Height Map", 2D)        = "white" {}
        _ColorMap ("Color Map", 2D)        = "white" {}   // ← 追加
        _DisplacementScale("Displacement Scale", Float) = 1.0
        _BaseColor("Base Color", Color)    = (1,1,1,1)
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" }
        Cull Off
        LOD 200

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma target 4.0
            #include "UnityCG.cginc"

            sampler2D _HeightMap;
            sampler2D _ColorMap;                // ← 追加
            float    _DisplacementScale;
            float4   _BaseColor;

            struct appdata
            {
                float4 vertex : POSITION;
                float3 normal : NORMAL;
                float2 uv     : TEXCOORD0;
            };

            struct v2f
            {
                float2 uv  : TEXCOORD0;
                float4 pos : SV_POSITION;
            };

            v2f vert(appdata v)
            {
                v2f o;
                float height = tex2Dlod(_HeightMap, float4(v.uv,0,0)).r;
                float3 displaced = v.vertex.xyz
                                   + v.normal / ((height * 10.0) + 1e-6) * _DisplacementScale;
                o.pos = UnityObjectToClipPos(float4(displaced, 1.0));
                o.uv  = v.uv;
                return o;
            }

            fixed4 frag(v2f i) : SV_Target
            {
                // 360°映像をサンプリング
                fixed4 col = tex2D(_ColorMap, i.uv);
                // 必要ならベースカラーで調整
                return col * _BaseColor;
            }
            ENDCG
        }
    }
    FallBack Off
}