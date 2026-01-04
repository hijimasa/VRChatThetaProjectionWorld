// Assets/Editor/UVSphereMeshGenerator.cs
using UnityEngine;
using UnityEditor;
using System.IO;

public static class UVSphereMeshGenerator
{
    [MenuItem("Tools/Procedural Mesh/Create UV Sphere Mesh Asset...")]
    public static void CreateUvSphereMeshAsset()
    {
        // ここを好みに変えてOK（ダイアログ無しでまず動くように固定値）
        int segments = 128;      // 経度
        int rings = 64;         // 緯度
        float radius = 1.0f;
        float boundsScale = 100.0f;

        // 保存先（必要なら保存ダイアログにしてもOK）
        string folder = "Assets/ProceduralMeshes";
        if (!AssetDatabase.IsValidFolder(folder))
        {
            Directory.CreateDirectory(folder);
            AssetDatabase.Refresh();
        }
        string path = AssetDatabase.GenerateUniqueAssetPath($"{folder}/UVSphere_seg{segments}_ring{rings}_r{radius}.asset");

        var mesh = BuildUvSphere(segments, rings, radius, boundsScale);
        AssetDatabase.CreateAsset(mesh, path);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();

        EditorUtility.FocusProjectWindow();
        Selection.activeObject = mesh;

        Debug.Log($"Created UV Sphere Mesh Asset: {path}");
    }

    // UV Sphere: (rings+1) * (segments+1) vertices
    static Mesh BuildUvSphere(int segments, int rings, float radius, float boundsScale)
    {
        segments = Mathf.Max(3, segments);
        rings = Mathf.Max(2, rings);
        radius = Mathf.Max(1e-5f, radius);

        int vertCount = (rings + 1) * (segments + 1);
        int triCount = rings * segments * 2;

        var vertices = new Vector3[vertCount];
        var normals  = new Vector3[vertCount];
        var uvs      = new Vector2[vertCount];
        var triangles = new int[triCount * 3];

        int vi = 0;
        for (int y = 0; y <= rings; y++)
        {
            float v = (float)y / rings;          // 0..1
            float phi = v * Mathf.PI;            // 0..PI

            float sinPhi = Mathf.Sin(phi);
            float cosPhi = Mathf.Cos(phi);

            for (int x = 0; x <= segments; x++)
            {
                float u = (float)x / segments;   // 0..1
                float theta = u * Mathf.PI * 2f + Mathf.PI / segments; // 0..2PI

                float sinTheta = Mathf.Sin(theta);
                float cosTheta = Mathf.Cos(theta);

                // Unityのデフォルト球っぽい向き（Yが上下）
                Vector3 n = new Vector3(
                    sinPhi * cosTheta,
                    cosPhi,
                    sinPhi * sinTheta
                ).normalized;

                vertices[vi] = n * radius;
                normals[vi] = n;

                // UV座標: 境界処理
                // x=segmentsのとき、UV.xを0.0に設定（左端と右端を同じにする）
                float finalU = (x == segments) ? 0.0f : u;
                uvs[vi] = new Vector2(finalU, 1f - v);
                vi++;
            }
        }

        int ti = 0;
        int stride = segments + 1;
        for (int y = 0; y < rings; y++)
        {
            for (int x = 0; x < segments; x++)
            {
                int a = y * stride + x;
                int b = (y + 1) * stride + x;
                int c = a + 1;
                int d = b + 1;

                // winding: Unityは基本的に反時計回りが表
                triangles[ti++] = a; triangles[ti++] = b; triangles[ti++] = c;
                triangles[ti++] = c; triangles[ti++] = b; triangles[ti++] = d;
            }
        }

        var mesh = new Mesh();
        // 6万頂点超える可能性がある設定ならUInt32に
        if (vertCount > 65535)
            mesh.indexFormat = UnityEngine.Rendering.IndexFormat.UInt32;

        mesh.name = $"UVSphere_seg{segments}_ring{rings}";
        mesh.vertices = vertices;
        mesh.normals = normals;
        mesh.uv = uvs;
        mesh.triangles = triangles;

        // Bounds（カリング用）: 必要なら拡大
        float size = radius * 2f * Mathf.Max(0.01f, boundsScale);
        mesh.bounds = new Bounds(Vector3.zero, Vector3.one * size);

        return mesh;
    }
}
