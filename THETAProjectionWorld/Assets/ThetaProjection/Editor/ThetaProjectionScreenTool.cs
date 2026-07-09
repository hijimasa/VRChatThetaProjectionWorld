// Assets/ThetaProjection/Editor/ThetaProjectionScreenTool.cs
// 任意のワールドでビデオプレイヤーのスクリーンをTHETA投影スクリーンへ変換するエディタツール。
// アセットはGUIDで解決するため、ThetaProjectionフォルダをどこに置いても動作する。
using UnityEngine;
using UnityEditor;

public static class ThetaProjectionScreenTool
{
    // Assets/ThetaProjection/Meshes/UVSphere_seg512_ring256_r1.asset
    const string SphereMeshGuid = "202ba8492e3ab39408cdd33dbf09b9de";
    // Assets/ThetaProjection/Materials/ThetaProjectionScreen.mat
    const string ScreenMaterialGuid = "c8068fd3d5dbfb06fbb34e595a9af3cc";

    [MenuItem("Tools/THETA Projection/Convert Selected Screen To Projection Sphere")]
    public static void ConvertSelectedScreen()
    {
        var go = Selection.activeGameObject;
        if (go == null)
        {
            EditorUtility.DisplayDialog("THETA Projection",
                "ビデオプレイヤーのスクリーン(MeshRenderer付きオブジェクト)を選択してから実行してください。\n" +
                "TopazChat Playerの場合は \"Monitor\" オブジェクトを選択します。\n\n" +
                "Select a video player screen object (with a MeshRenderer) first.\n" +
                "For TopazChat Player, select the \"Monitor\" object.", "OK");
            return;
        }

        var meshFilter = go.GetComponent<MeshFilter>();
        var meshRenderer = go.GetComponent<MeshRenderer>();
        if (meshFilter == null || meshRenderer == null)
        {
            EditorUtility.DisplayDialog("THETA Projection",
                $"\"{go.name}\" に MeshFilter / MeshRenderer がありません。\n" +
                "ビデオプレイヤーのスクリーン本体を選択してください。\n\n" +
                $"\"{go.name}\" has no MeshFilter / MeshRenderer.\n" +
                "Select the screen object of your video player.", "OK");
            return;
        }

        var mesh = LoadByGuid<Mesh>(SphereMeshGuid, "UVSphere mesh");
        var material = LoadByGuid<Material>(ScreenMaterialGuid, "ThetaProjectionScreen material");
        if (mesh == null || material == null) return;

        Undo.RecordObjects(new Object[] { meshFilter, meshRenderer }, "Convert To THETA Projection Screen");
        meshFilter.sharedMesh = mesh;
        meshRenderer.sharedMaterial = material;
        EditorUtility.SetDirty(meshFilter);
        EditorUtility.SetDirty(meshRenderer);

        Debug.Log($"[THETA Projection] \"{go.name}\" を投影スフィアに変換しました。" +
                  "ビデオプレイヤーがこのRendererのマテリアル(_MainTex)へ映像を書き込む設定になっていることを確認してください。 / " +
                  $"Converted \"{go.name}\" to a projection sphere. " +
                  "Make sure your video player writes the video texture (_MainTex) to this renderer's material.");
    }

    [MenuItem("Tools/THETA Projection/Create Projection Screen In Scene")]
    public static void CreateProjectionScreen()
    {
        var mesh = LoadByGuid<Mesh>(SphereMeshGuid, "UVSphere mesh");
        var material = LoadByGuid<Material>(ScreenMaterialGuid, "ThetaProjectionScreen material");
        if (mesh == null || material == null) return;

        var go = new GameObject("ThetaProjectionScreen");
        var meshFilter = go.AddComponent<MeshFilter>();
        var meshRenderer = go.AddComponent<MeshRenderer>();
        meshFilter.sharedMesh = mesh;
        meshRenderer.sharedMaterial = material;
        go.transform.position = new Vector3(0f, 1f, 0f);

        Undo.RegisterCreatedObjectUndo(go, "Create THETA Projection Screen");
        Selection.activeGameObject = go;

        Debug.Log("[THETA Projection] ThetaProjectionScreen を作成しました。" +
                  "ビデオプレイヤーの映像出力先(スクリーン)としてこのオブジェクトを指定してください。 / " +
                  "Created ThetaProjectionScreen. Point your video player's screen output at this object.");
    }

    [MenuItem("Tools/THETA Projection/Export ThetaProjection.unitypackage")]
    public static void ExportPackage()
    {
        const string exportPath = "ThetaProjection.unitypackage";
        AssetDatabase.ExportPackage("Assets/ThetaProjection", exportPath,
            ExportPackageOptions.Recurse | ExportPackageOptions.Interactive);
        Debug.Log($"[THETA Projection] Exported {exportPath}");
    }

    static T LoadByGuid<T>(string guid, string label) where T : Object
    {
        string path = AssetDatabase.GUIDToAssetPath(guid);
        var asset = string.IsNullOrEmpty(path) ? null : AssetDatabase.LoadAssetAtPath<T>(path);
        if (asset == null)
        {
            EditorUtility.DisplayDialog("THETA Projection",
                $"{label} が見つかりません。ThetaProjection フォルダを丸ごとインポートしたか確認してください。\n\n" +
                $"Could not find the {label}. Make sure the whole ThetaProjection folder was imported.", "OK");
        }
        return asset;
    }
}
