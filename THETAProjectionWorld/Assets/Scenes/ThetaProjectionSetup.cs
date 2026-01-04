using UdonSharp;
using UnityEngine;
using VRC.SDKBase;

namespace ThetaProjection
{
    /// <summary>
    /// THETA投影システムのセットアップヘルパー
    /// シェーダーパラメータの調整やデバッグ表示を行う
    /// </summary>
    [UdonBehaviourSyncMode(BehaviourSyncMode.None)]
    public class ThetaProjectionSetup : UdonSharpBehaviour
    {
        [Header("Projection Settings")]
        [SerializeField] private Material projectionMaterial;
        [Tooltip("ThetaDepthDisplacementシェーダーを使用したMaterial")]

        [SerializeField] private float depthScale = 1.0f;
        [SerializeField] private float maxDepth = 5.0f;
        [SerializeField] private float sphereRadius = 5.0f;
        [SerializeField] private float minRadius = 0.5f;

        [Header("Runtime Adjustment")]
        [SerializeField] private bool enableRuntimeAdjustment = true;
        [Tooltip("実行時にパラメータを調整可能にする")]

        [Header("Debug")]
        [SerializeField] private UnityEngine.UI.Text statusText;
        [SerializeField] private UnityEngine.UI.Slider depthScaleSlider;
        [SerializeField] private UnityEngine.UI.Slider sphereRadiusSlider;

        private bool isInitialized = false;

        void Start()
        {
            if (projectionMaterial == null)
            {
                Debug.LogError("[ThetaProjectionSetup] projectionMaterial is not assigned!");
                return;
            }

            ApplySettings();
            isInitialized = true;

            Debug.Log("[ThetaProjectionSetup] Initialized");
        }

        void Update()
        {
            if (!isInitialized || !enableRuntimeAdjustment) return;

            // スライダーからの入力を反映
            if (depthScaleSlider != null)
            {
                depthScale = depthScaleSlider.value;
            }

            if (sphereRadiusSlider != null)
            {
                sphereRadius = sphereRadiusSlider.value;
            }

            ApplySettings();
            UpdateStatusText();
        }

        void ApplySettings()
        {
            if (projectionMaterial == null) return;

            projectionMaterial.SetFloat("_DepthScale", depthScale);
            projectionMaterial.SetFloat("_MaxDepth", maxDepth);
            projectionMaterial.SetFloat("_SphereRadius", sphereRadius);
            projectionMaterial.SetFloat("_MinRadius", minRadius);
        }

        void UpdateStatusText()
        {
            if (statusText == null) return;

            statusText.text = $"Theta Projection\n" +
                            $"DepthScale: {depthScale:F2}\n" +
                            $"MaxDepth: {maxDepth:F1}m\n" +
                            $"SphereRadius: {sphereRadius:F1}m\n" +
                            $"MinRadius: {minRadius:F1}m";
        }

        // 外部から呼び出し可能なパラメータ設定メソッド
        public void SetDepthScale(float value)
        {
            depthScale = Mathf.Clamp(value, 0f, 5f);
            ApplySettings();
        }

        public void SetMaxDepth(float value)
        {
            maxDepth = Mathf.Clamp(value, 0.1f, 10f);
            ApplySettings();
        }

        public void SetSphereRadius(float value)
        {
            sphereRadius = Mathf.Clamp(value, 1f, 20f);
            ApplySettings();
        }

        public void SetMinRadius(float value)
        {
            minRadius = Mathf.Clamp(value, 0.1f, 5f);
            ApplySettings();
        }

        // ボタン用のインクリメント/デクリメントメソッド
        public void IncreaseDepthScale()
        {
            SetDepthScale(depthScale + 0.1f);
        }

        public void DecreaseDepthScale()
        {
            SetDepthScale(depthScale - 0.1f);
        }

        public void IncreaseSphereRadius()
        {
            SetSphereRadius(sphereRadius + 0.5f);
        }

        public void DecreaseSphereRadius()
        {
            SetSphereRadius(sphereRadius - 0.5f);
        }
    }
}
