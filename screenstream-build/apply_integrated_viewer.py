#!/usr/bin/env python3
from pathlib import Path
import shutil
import sys


def die(msg: str):
    raise SystemExit(f"ERROR: {msg}")


def read(path: Path) -> str:
    if not path.exists():
        die(f"arquivo não encontrado: {path}")
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        die(f"âncora '{label}' esperada 1x, encontrada {count}x")
    return text.replace(old, new, 1)


VIEWER_ACTIVITY = r'''package info.dvkr.screenstream.webrtc.viewer

import android.annotation.SuppressLint
import android.os.Bundle
import android.webkit.CookieManager
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.ComponentActivity
import info.dvkr.screenstream.webrtc.R

/**
 * Integrated ScreenStream viewer. It keeps the official screenstream.io page inside the APK,
 * but replaces only the page's bundle.js with our patched bundle that understands the chat
 * RTCDataChannel. The media itself stays WebRTC end-to-end between host and viewer.
 */
public class ViewerActivity : ComponentActivity() {
    private lateinit var webView: WebView

    @SuppressLint("SetJavaScriptEnabled")
    public override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        title = getString(R.string.webrtc_viewer_title)

        webView = WebView(this).apply {
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            settings.databaseEnabled = true
            settings.mediaPlaybackRequiresUserGesture = false
            settings.mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
            settings.loadsImagesAutomatically = true
            settings.useWideViewPort = true
            settings.loadWithOverviewMode = true

            CookieManager.getInstance().setAcceptCookie(true)
            CookieManager.getInstance().setAcceptThirdPartyCookies(this, true)

            webChromeClient = WebChromeClient()
            webViewClient = object : WebViewClient() {
                override fun shouldInterceptRequest(view: WebView?, request: WebResourceRequest?): WebResourceResponse? {
                    val url = request?.url ?: return super.shouldInterceptRequest(view, request)
                    if (url.host.equals("screenstream.io", ignoreCase = true) && url.encodedPath == "/bundle.js") {
                        return runCatching {
                            WebResourceResponse(
                                "application/javascript",
                                "UTF-8",
                                assets.open("viewer/bundle.js")
                            ).apply {
                                responseHeaders = mapOf(
                                    "Cache-Control" to "no-store",
                                    "Access-Control-Allow-Origin" to "https://screenstream.io"
                                )
                            }
                        }.getOrNull() ?: super.shouldInterceptRequest(view, request)
                    }
                    return super.shouldInterceptRequest(view, request)
                }
            }
        }

        setContentView(webView)
        if (savedInstanceState == null) webView.loadUrl("https://screenstream.io/")
        else webView.restoreState(savedInstanceState)
    }

    public override fun onSaveInstanceState(outState: Bundle) {
        webView.saveState(outState)
        super.onSaveInstanceState(outState)
    }

    @Suppress("DEPRECATION")
    public override fun onBackPressed() {
        if (::webView.isInitialized && webView.canGoBack()) webView.goBack()
        else super.onBackPressed()
    }

    public override fun onDestroy() {
        if (::webView.isInitialized) {
            webView.stopLoading()
            webView.loadUrl("about:blank")
            webView.clearHistory()
            webView.removeAllViews()
            webView.destroy()
        }
        super.onDestroy()
    }
}
'''


VIEWER_CARD = r'''package info.dvkr.screenstream.webrtc.ui.main.cards

import android.content.Intent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import info.dvkr.screenstream.webrtc.R
import info.dvkr.screenstream.webrtc.viewer.ViewerActivity

@Composable
internal fun ViewerCard(modifier: Modifier = Modifier) {
    val context = LocalContext.current

    Card(modifier = modifier, elevation = CardDefaults.cardElevation(defaultElevation = 1.dp)) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Text(
                text = stringResource(R.string.webrtc_viewer_title),
                style = MaterialTheme.typography.titleMedium
            )
            Text(
                text = stringResource(R.string.webrtc_viewer_description),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Button(
                modifier = Modifier.fillMaxWidth(),
                onClick = { context.startActivity(Intent(context, ViewerActivity::class.java)) }
            ) {
                Text(stringResource(R.string.webrtc_viewer_open))
            }
        }
    }
}
'''


def patch_strings(repo: Path):
    res_root = repo / "webrtc/src/main/res"
    files = sorted(res_root.glob("values*/strings.xml"))
    if not files:
        die("nenhum strings.xml do módulo webrtc encontrado")

    english = [
        ("webrtc_viewer_title", "Watch stream"),
        ("webrtc_viewer_description", "Watch a Global stream with video, audio and party chat inside the app."),
        ("webrtc_viewer_open", "Watch inside app"),
    ]
    portuguese = {
        "webrtc_viewer_title": "Assistir transmissão",
        "webrtc_viewer_description": "Assista a uma transmissão Global com vídeo, áudio e chat da sala dentro do app.",
        "webrtc_viewer_open": "Assistir dentro do app",
    }

    for path in files:
        text = read(path)
        if "webrtc_viewer_title" in text:
            continue
        values = english
        if path.parent.name == "values-pt":
            values = [(key, portuguese[key]) for key, _ in english]
        block = "\n" + "\n".join(f'    <string name="{key}">{value}</string>' for key, value in values) + "\n"
        if "</resources>" not in text:
            die(f"fechamento </resources> ausente em {path}")
        write(path, text.replace("</resources>", block + "</resources>", 1))


def patch_manifest(repo: Path):
    path = repo / "webrtc/src/main/AndroidManifest.xml"
    s = read(path)
    if ".viewer.ViewerActivity" in s:
        return
    s = replace_once(
        s,
        "    </application>\n",
        '''        <activity
            android:name=".viewer.ViewerActivity"
            android:exported="false"
            android:hardwareAccelerated="true" />
    </application>\n''',
        "viewer activity manifest",
    )
    write(path, s)


def patch_main_ui(repo: Path):
    path = repo / "webrtc/src/main/java/info/dvkr/screenstream/webrtc/ui/WebRtcMainScreenUI.kt"
    s = read(path)
    if "ViewerCard" not in s:
        s = replace_once(
            s,
            "import info.dvkr.screenstream.webrtc.ui.main.cards.StreamCard\n",
            "import info.dvkr.screenstream.webrtc.ui.main.cards.StreamCard\nimport info.dvkr.screenstream.webrtc.ui.main.cards.ViewerCard\n",
            "viewer card import",
        )
        s = replace_once(
            s,
            '''            item(key = "CLIENTS") {
''',
            '''            item(key = "VIEWER") {
                ViewerCard(modifier = Modifier.padding(8.dp))
            }

            item(key = "CLIENTS") {
''',
            "viewer card item",
        )
    write(path, s)


def main():
    if len(sys.argv) != 3:
        die("uso: apply_integrated_viewer.py /caminho/ScreenStream /caminho/bundle.js")
    repo = Path(sys.argv[1]).resolve()
    bundle = Path(sys.argv[2]).resolve()
    if not (repo / "webrtc").exists():
        die(f"checkout ScreenStream inválido: {repo}")
    if not bundle.exists():
        die(f"bundle.js não encontrado: {bundle}")

    write(repo / "webrtc/src/main/java/info/dvkr/screenstream/webrtc/viewer/ViewerActivity.kt", VIEWER_ACTIVITY)
    write(repo / "webrtc/src/main/java/info/dvkr/screenstream/webrtc/ui/main/cards/ViewerCard.kt", VIEWER_CARD)
    assets = repo / "webrtc/src/main/assets/viewer"
    assets.mkdir(parents=True, exist_ok=True)
    shutil.copy2(bundle, assets / "bundle.js")

    patch_strings(repo)
    patch_manifest(repo)
    patch_main_ui(repo)

    required = [
        repo / "webrtc/src/main/java/info/dvkr/screenstream/webrtc/viewer/ViewerActivity.kt",
        repo / "webrtc/src/main/java/info/dvkr/screenstream/webrtc/ui/main/cards/ViewerCard.kt",
        repo / "webrtc/src/main/assets/viewer/bundle.js",
    ]
    for p in required:
        if not p.exists() or p.stat().st_size == 0:
            die(f"arquivo integrado ausente: {p}")
    print("Viewer integrado aplicado com sucesso.")


if __name__ == "__main__":
    main()
