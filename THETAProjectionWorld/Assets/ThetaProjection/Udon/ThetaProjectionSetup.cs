using UdonSharp;
using UnityEngine;
using VRC.SDKBase;

namespace ThetaProjection
{
    /// <summary>
    /// THETA投影システムのセットアップヘルパー（任意設置）
    /// ThetaProjection/DepthDisplacement シェーダーのパラメータをワールド内から調整する
    ///
    /// targetRenderer に投影スフィアの Renderer を指定すると、
    /// 実行時にそのマテリアル（ビデオプレイヤーが生成するインスタンスを含む）を自動で取得する。
    /// projectionMaterial を直接指定した場合はそちらを優先する。
    /// </summary>
    [UdonBehaviourSyncMode(BehaviourSyncMode.None)]
    public class ThetaProjectionSetup : UdonSharpBehaviour
    {
        [Header("Projection Target")]
        [Tooltip("投影スフィアのRenderer（推奨）。実行時にマテリアルを自動取得する")]
        [SerializeField] private Renderer targetRenderer;

        [Tooltip("ThetaDepthDisplacementシェーダーを使用したMaterialを直接指定する場合")]
        [SerializeField] private Material projectionMaterial;

        [Header("Projection Settings")]
        [SerializeField] private float depthScale = 0.02f;
        [SerializeField] private float minRadius = 0.1f;
        [SerializeField] private bool flipYDepth = false;
        [SerializeField] private bool flipYRGB = true;

        [Header("Runtime Adjustment")]
        [SerializeField] private bool enableRuntimeAdjustment = true;
        [Tooltip("実行時にパラメータを調整可能にする")]

        [Header("Debug")]
        [SerializeField] private UnityEngine.UI.Text statusText;
        [SerializeField] private UnityEngine.UI.Slider depthScaleSlider;
        [SerializeField] private UnityEngine.UI.Slider minRadiusSlider;

        private bool isInitialized = false;

        void Start()
        {
            if (ResolveMaterial() == null)
            {
                Debug.LogError("[ThetaProjectionSetup] Neither targetRenderer nor projectionMaterial is assigned!");
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

            if (minRadiusSlider != null)
            {
                minRadius = minRadiusSlider.value;
            }

            ApplySettings();
            UpdateStatusText();
        }

        // ビデオプレイヤーが実行時にマテリアルを差し替える場合があるため、毎回Rendererから取得する
        Material ResolveMaterial()
        {
            if (projectionMaterial != null) return projectionMaterial;
            if (targetRenderer != null) return targetRenderer.material;
            return null;
        }

        void ApplySettings()
        {
            Material mat = ResolveMaterial();
            if (mat == null) return;

            mat.SetFloat("_DepthScale", depthScale);
            mat.SetFloat("_MinRadius", minRadius);
            mat.SetFloat("_FlipY_Depth", flipYDepth ? 1f : 0f);
            mat.SetFloat("_FlipY_RGB", flipYRGB ? 1f : 0f);
        }

        void UpdateStatusText()
        {
            if (statusText == null) return;

            statusText.text = $"Theta Projection\n" +
                            $"DepthScale: {depthScale:F3}\n" +
                            $"MinRadius: {minRadius:F1}m\n" +
                            $"FlipY Depth: {flipYDepth}\n" +
                            $"FlipY RGB: {flipYRGB}";
        }

        // 外部から呼び出し可能なパラメータ設定メソッド
        public void SetDepthScale(float value)
        {
            depthScale = Mathf.Clamp(value, 0f, 5f);
            ApplySettings();
        }

        public void SetMinRadius(float value)
        {
            minRadius = Mathf.Clamp(value, 0.1f, 5f);
            ApplySettings();
        }

        public void ToggleFlipYDepth()
        {
            flipYDepth = !flipYDepth;
            ApplySettings();
        }

        public void ToggleFlipYRGB()
        {
            flipYRGB = !flipYRGB;
            ApplySettings();
        }

        // ボタン用のインクリメント/デクリメントメソッド
        public void IncreaseDepthScale()
        {
            SetDepthScale(depthScale + 0.01f);
        }

        public void DecreaseDepthScale()
        {
            SetDepthScale(depthScale - 0.01f);
        }

        public void IncreaseMinRadius()
        {
            SetMinRadius(minRadius + 0.1f);
        }

        public void DecreaseMinRadius()
        {
            SetMinRadius(minRadius - 0.1f);
        }
    }
}
