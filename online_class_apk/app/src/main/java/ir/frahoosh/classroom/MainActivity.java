package ir.frahoosh.classroom;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.res.AssetManager;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.util.Log;
import android.webkit.CookieManager;
import android.webkit.PermissionRequest;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceError;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebResourceResponse;

import java.io.InputStream;
import android.widget.FrameLayout;

import java.util.ArrayList;

public final class MainActivity extends Activity {
    private static final int MEDIA_PERMISSION_REQUEST = 4207;
    private static final int FILE_CHOOSER_REQUEST = 4208;
    private static final String CLASSROOM_URL = "https://frahoosh.ir/online-class/";

    private WebView webView;
    private final ArrayList<PermissionRequest> pendingWebPermissions = new ArrayList<>();
    private boolean mediaPermissionRequestInFlight = false;
    private ValueCallback<Uri[]> fileCallback;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(Color.BLACK);
        getWindow().setNavigationBarColor(Color.BLACK);
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_FULLSCREEN |
                View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY |
                View.SYSTEM_UI_FLAG_LAYOUT_STABLE |
                View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION |
                View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
        );

        buildWebView();
    }

    private void buildWebView() {
        webView = new WebView(this);
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.BLACK);
        root.addView(webView, new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT
        ));
        setContentView(root);

        WebSettings s = webView.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setJavaScriptCanOpenWindowsAutomatically(false);
        s.setSupportMultipleWindows(false);
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(false);
        s.setBuiltInZoomControls(false);
        s.setDisplayZoomControls(false);
        s.setLoadsImagesAutomatically(true);
        s.setUseWideViewPort(true);
        s.setLoadWithOverviewMode(false);
        if (Build.VERSION.SDK_INT >= 26) {
            s.setSafeBrowsingEnabled(true);
        }

        CookieManager.getInstance().setAcceptCookie(true);
        CookieManager.getInstance().setAcceptThirdPartyCookies(webView, true);

        webView.setBackgroundColor(Color.BLACK);
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return false;
            }

            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                return localAssetResponse(request.getUrl().getPath());
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) {
                    view.postDelayed(() -> {
                        if (webView != null) {
                            webView.loadUrl(CLASSROOM_URL + "index.html");
                        }
                    }, 800);
                }
            }
        });

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onPermissionRequest(final PermissionRequest request) {
                // Keep WebRTC requests while Android runtime permissions are requested.
                // Camera and microphone may arrive as separate WebView requests.
                runOnUiThread(() -> {
                    if (request == null) return;
                    Uri origin = request.getOrigin();
                    if (!isTrustedClassroomOrigin(origin)) {
                        Log.w("FrahooshClassroom", "Denied WebView media request from untrusted origin: " + origin);
                        request.deny();
                        return;
                    }
                    // Handle camera and microphone independently. A granted camera must not
                    // wait for microphone permission (or vice versa), otherwise WebRTC can
                    // appear to ignore the classroom buttons on devices with partial grants.
                    if (hasRequestedMediaPermissions(request)) {
                        grantWebMediaPermission(request);
                    } else {
                        if (!pendingWebPermissions.contains(request)) pendingWebPermissions.add(request);
                        requestMediaPermissions(request);
                    }
                });
            }

            @Override
            public void onPermissionRequestCanceled(PermissionRequest request) {
                pendingWebPermissions.remove(request);
            }

            @Override
            public boolean onShowFileChooser(
                    WebView view,
                    ValueCallback<Uri[]> callback,
                    FileChooserParams params) {
                if (fileCallback != null) fileCallback.onReceiveValue(null);
                fileCallback = callback;
                try {
                    Intent intent = params.createIntent();
                    startActivityForResult(intent, FILE_CHOOSER_REQUEST);
                    return true;
                } catch (Exception e) {
                    fileCallback = null;
                    callback.onReceiveValue(null);
                    return false;
                }
            }
        });

        webView.loadUrl(CLASSROOM_URL + "index.html");
    }

    private WebResourceResponse localAssetResponse(String path) {
        if (path == null) return null;
        String asset = null;
        if (path.endsWith("/online-class/") || path.endsWith("/online-class/index.html")) {
            asset = "index.html";
        } else if (path.endsWith("/online-class/room.html")) {
            asset = "room.html";
        } else if (path.endsWith("/online-class/online_class.html") || path.endsWith("/mobile/assets/online_class.html")) {
            asset = "room_assets/online_class.html";
        } else if (path.endsWith("/online-class/classroom_patch.js") || path.endsWith("/online_class_apk/classroom_patch.js")) {
            asset = "room_assets/classroom_patch.js";
        }
        if (asset == null) return null;
        try {
            AssetManager am = getAssets();
            InputStream in = am.open(asset, AssetManager.ACCESS_STREAMING);
            String mime = asset.endsWith(".js") ? "application/javascript" : "text/html";
            return new WebResourceResponse(mime, "UTF-8", in);
        } catch (Exception ignored) {
            return null;
        }
    }

    private boolean isTrustedClassroomOrigin(Uri origin) {
        if (origin == null || !"https".equalsIgnoreCase(origin.getScheme())) return false;
        String host = origin.getHost();
        return "frahoosh.ir".equalsIgnoreCase(host) || "www.frahoosh.ir".equalsIgnoreCase(host);
    }

    private boolean hasRequestedMediaPermissions(PermissionRequest request) {
        if (Build.VERSION.SDK_INT < 23) return true;
        boolean requestedMedia = false;
        for (String resource : request.getResources()) {
            if (PermissionRequest.RESOURCE_VIDEO_CAPTURE.equals(resource)) {
                requestedMedia = true;
                if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) return false;
            } else if (PermissionRequest.RESOURCE_AUDIO_CAPTURE.equals(resource)) {
                requestedMedia = true;
                if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) return false;
            }
        }
        return requestedMedia;
    }

    private void requestMediaPermissions() {
        requestMediaPermissions(null);
    }

    private void requestMediaPermissions(PermissionRequest request) {
        if (Build.VERSION.SDK_INT < 23) {
            grantPendingWebPermissions();
            return;
        }
        if (mediaPermissionRequestInFlight) return;
        ArrayList<String> missing = new ArrayList<>();
        if (request == null) {
            if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
                missing.add(Manifest.permission.CAMERA);
            }
            if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
                missing.add(Manifest.permission.RECORD_AUDIO);
            }
        } else {
            for (String resource : request.getResources()) {
                if (PermissionRequest.RESOURCE_VIDEO_CAPTURE.equals(resource)
                        && checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED
                        && !missing.contains(Manifest.permission.CAMERA)) {
                    missing.add(Manifest.permission.CAMERA);
                } else if (PermissionRequest.RESOURCE_AUDIO_CAPTURE.equals(resource)
                        && checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED
                        && !missing.contains(Manifest.permission.RECORD_AUDIO)) {
                    missing.add(Manifest.permission.RECORD_AUDIO);
                }
            }
        }
        if (!missing.isEmpty()) {
            mediaPermissionRequestInFlight = true;
            requestPermissions(missing.toArray(new String[0]), MEDIA_PERMISSION_REQUEST);
        } else {
            grantPendingWebPermissions();
        }
    }

    private void grantWebMediaPermission(PermissionRequest request) {
        if (request == null) return;

        ArrayList<String> allowed = new ArrayList<>();
        for (String resource : request.getResources()) {
            if (PermissionRequest.RESOURCE_VIDEO_CAPTURE.equals(resource)
                    && checkSelfPermission(Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
                allowed.add(resource);
            } else if (PermissionRequest.RESOURCE_AUDIO_CAPTURE.equals(resource)
                    && checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
                allowed.add(resource);
            }
        }

        if (!allowed.isEmpty()) {
            request.grant(allowed.toArray(new String[0]));
        } else {
            request.deny();
        }
    }

    private void grantPendingWebPermissions() {
        if (pendingWebPermissions.isEmpty()) return;
        ArrayList<PermissionRequest> requests = new ArrayList<>(pendingWebPermissions);
        pendingWebPermissions.clear();
        for (PermissionRequest request : requests) grantWebMediaPermission(request);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(requestCode, permissions, results);
        if (requestCode == MEDIA_PERMISSION_REQUEST) {
            mediaPermissionRequestInFlight = false;
            // Grant each requested capability independently after Android's permission dialog.
            grantPendingWebPermissions();
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == FILE_CHOOSER_REQUEST && fileCallback != null) {
            Uri[] result = null;
            if (resultCode == RESULT_OK && data != null) {
                if (data.getClipData() != null) {
                    int n = data.getClipData().getItemCount();
                    result = new Uri[n];
                    for (int i = 0; i < n; i++) {
                        result[i] = data.getClipData().getItemAt(i).getUri();
                    }
                } else if (data.getData() != null) {
                    result = new Uri[] { data.getData() };
                }
            }
            fileCallback.onReceiveValue(result);
            fileCallback = null;
        }
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onDestroy() {
        for (PermissionRequest request : new ArrayList<>(pendingWebPermissions)) request.deny();
        pendingWebPermissions.clear();
        if (fileCallback != null) {
            fileCallback.onReceiveValue(null);
            fileCallback = null;
        }
        if (webView != null) {
            webView.stopLoading();
            webView.loadUrl("about:blank");
            webView.clearHistory();
            webView.removeAllViews();
            webView.destroy();
            webView = null;
        }
        super.onDestroy();
    }
}
