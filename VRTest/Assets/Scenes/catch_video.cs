using System;
using System.Collections.Concurrent;
using System.IO;
using System.Net;
using System.Threading;
using UnityEngine;

public class MjpegToRenderTexture : MonoBehaviour
{
    [Header("MJPEG Stream URL")]
    public string streamUrl = "http://localhost:5000/raw";

    [Header("出力先 RenderTexture")]
    public RenderTexture targetRenderTexture;

    [Header("（任意）マテリアルに直接セットしたい場合")]
    public Renderer targetRenderer;
    public string texturePropertyName = "_MainTex";

    // スレッド→メインスレッド受け渡し用キュー
    private ConcurrentQueue<byte[]> _jpegQueue = new ConcurrentQueue<byte[]>();

    private Thread _workerThread;
    private volatile bool _running;

    void Start()
    {
        if (targetRenderTexture == null)
        {
            Debug.LogError("[MjpegToRenderTexture] targetRenderTexture をアサインしてください");
            enabled = false;
            return;
        }

        if (targetRenderer != null)
            targetRenderer.material.SetTexture(texturePropertyName, targetRenderTexture);

        _running = true;
        _workerThread = new Thread(StreamLoop) { IsBackground = true };
        _workerThread.Start();
    }

    private void StreamLoop()
    {
        while (_running)
        {
            HttpWebResponse resp = null;
            Stream stream = null;
            var ms = new MemoryStream();

            try
            {
                // リクエスト作成
                var req = (HttpWebRequest)WebRequest.Create(streamUrl);
                req.Timeout = System.Threading.Timeout.Infinite;        // GetResponse でタイムアウトさせない
                req.ReadWriteTimeout = System.Threading.Timeout.Infinite; // Read/Write でタイムアウトさせない
                req.KeepAlive = true;
                req.AllowWriteStreamBuffering = false;

                resp = (HttpWebResponse)req.GetResponse();
                stream = resp.GetResponseStream();

                var buf = new byte[4096];
                while (_running)
                {
                    int read = stream.Read(buf, 0, buf.Length);
                    if (read <= 0) break;

                    ms.Write(buf, 0, read);
                    var data = ms.ToArray();

                    int s = FindPattern(data, new byte[] { 0xFF, 0xD8 }, 0);
                    int e = (s >= 0) ? FindPattern(data, new byte[] { 0xFF, 0xD9 }, s + 2) : -1;
                    if (s >= 0 && e >= 0)
                    {
                        e += 2;
                        int len = e - s;
                        var jpg = new byte[len];
                        Array.Copy(data, s, jpg, 0, len);
                        _jpegQueue.Enqueue(jpg);

                        // 残りを再構築
                        ms = new MemoryStream();
                        ms.Write(data, e, data.Length - e);
                    }
                }
            }
            catch (Exception ex)
            {
                Debug.LogWarning($"[MjpegToRenderTexture] Stream error: {ex.Message} → 1秒後に再接続します");
            }
            finally
            {
                stream?.Close();
                resp?.Close();
            }

            // 切断 or エラー時は少し待ってから再接続
            if (_running)
                Thread.Sleep(1000);
        }
    }

    void Update()
    {
        // キュー内の古いフレームは破棄、最新だけデコード
        while (_jpegQueue.Count > 1)
            _jpegQueue.TryDequeue(out _);

        if (_jpegQueue.TryDequeue(out var jpgBytes))
        {
            var tex = new Texture2D(1024, 512, TextureFormat.RGB24, false);
            tex.LoadImage(jpgBytes);
            Graphics.Blit(tex, targetRenderTexture);
            Destroy(tex);
        }
    }

    void OnDestroy()
    {
        _running = false;
        if (_workerThread != null && _workerThread.IsAlive)
            _workerThread.Join();
    }

    private int FindPattern(byte[] hay, byte[] needle, int start)
    {
        for (int i = start; i <= hay.Length - needle.Length; i++)
        {
            bool ok = true;
            for (int j = 0; j < needle.Length; j++)
                if (hay[i + j] != needle[j]) { ok = false; break; }
            if (ok) return i;
        }
        return -1;
    }
}
