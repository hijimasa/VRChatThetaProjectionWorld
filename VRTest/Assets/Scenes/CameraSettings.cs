using UnityEngine;

[ExecuteInEditMode]                   // エディタ上でも動作させたい場合
[RequireComponent(typeof(Camera))]
public class ForceNearClip : MonoBehaviour
{
    [Tooltip("0.001 など、0.01 以下の値を直接入力できます")]
    public float forcedNear = 0.0001f;

    void OnValidate()
    {
        var cam = GetComponent<Camera>();
        cam.nearClipPlane = forcedNear;
    }

    void Awake()
    {
        GetComponent<Camera>().nearClipPlane = forcedNear;
    }
}