package ir.frahoosh.classroom;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
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
import android.webkit.SslErrorHandler;
import android.net.http.SslError;

import android.widget.FrameLayout;

import java.util.ArrayList;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;

public final class MainActivity extends Activity {
    private static final int MEDIA_PERMISSION_REQUEST = 4207;
    private static final int FILE_CHOOSER_REQUEST = 4208;
    private static final String CLASSROOM_URL = "file:///android_asset/index.html";

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

    private void loadBundledRoom(WebView target) {
        try (InputStream in = getAssets().open("room.html");
             ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[8192];
            int count;
            while ((count = in.read(buffer)) != -1) out.write(buffer, 0, count);
            target.loadDataWithBaseURL("https://frahoosh.ir/online-class/",
                    out.toString("UTF-8"), "text/html", "UTF-8", null);
        } catch (Exception e) {
            Log.e("FrahooshClassroom", "Could not load bundled room bootstrap", e);
            showLoadError(target, "خطا در باز کردن تخته هوشمند",
                    "فایل محیط کلاس داخل برنامه خوانده نشد: " + e.getMessage());
        }
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
        // The entry screen is bundled in app/src/main/assets. WebView must be able to read\n        // that local asset; leaving file access disabled produces a blank black screen.\n        s.setAllowFileAccess(true);
        s.setAllowContentAccess(true);
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
            // Let the HTTPS classroom page load normally. There is no bundled room.html asset;
            // intercepting this navigation and trying to open a missing asset caused the APK
            // to show a local error instead of opening the real classroom.
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                // Do not shadow the live classroom with bundled HTML snapshots. The website is
                // the canonical implementation; serving stale local copies caused APK/web drift.
                return null;
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) {
                    String description = error == null ? "خطای نامشخص در بارگذاری صفحه" : String.valueOf(error.getDescription());
                    int code = error == null ? 0 : error.getErrorCode();
                    Log.e("FrahooshClassroom", "Main page load failed (" + code + "): " + description);
                    showLoadError(view, "خطا در باز کردن کلاس آنلاین", "کد خطا: " + code + "\\n" + description);
                }
            }

            @Override
            public void onReceivedSslError(WebView view, SslErrorHandler handler, SslError error) {
                // Keep TLS validation strict: never proceed through an invalid certificate.
                String reason = "خطای گواهی امنیتی";
                if (error != null) {
                    switch (error.getPrimaryError()) {
                        case SslError.SSL_EXPIRED:
                            reason = "گواهی امنیتی سایت منقضی شده است.";
                            break;
                        case SslError.SSL_IDMISMATCH:
                            reason = "نام دامنه با گواهی امنیتی مطابقت ندارد.";
                            break;
                        case SslError.SSL_NOTYETVALID:
                            reason = "گواهی امنیتی هنوز معتبر نشده است.";
                            break;
                        case SslError.SSL_UNTRUSTED:
                            reason = "گواهی امنیتی توسط مرجع معتبر تأیید نشده است.";
                            break;
                        default:
                            reason = "اعتبار گواهی امنیتی سایت تأیید نشد.";
                            break;
                    }
                }
                Log.e("FrahooshClassroom", "TLS certificate validation failed; url="
                        + (error == null ? "(unknown)" : error.getUrl())
                        + "; primaryError=" + (error == null ? -1 : error.getPrimaryError())
                        + "; details=" + error);
                if (handler != null) handler.cancel();
                showLoadError(view, "خطای گواهی امنیتی سایت",
                        reason + " ارتباط امن با frahoosh.ir برقرار نشد. تاریخ و ساعت گوشی و گواهی دامنه را بررسی کنید.");
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

        // Load the bundled classroom entry point first. This avoids making app startup depend\n        // on the website certificate; remote Supabase/WebRTC endpoints still use normal TLS.\n        // Keep the HTML bundled, but use the real HTTPS origin so root-relative
        // runtime configuration and Supabase requests resolve correctly.
        try (InputStream in = getAssets().open("index.html");
             ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[8192];
            int count;
            while ((count = in.read(buffer)) != -1) out.write(buffer, 0, count);
            webView.loadDataWithBaseURL("https://frahoosh.ir/online-class/",
                    out.toString("UTF-8"), "text/html", "UTF-8", null);
        } catch (Exception e) {
            Log.e("FrahooshClassroom", "Could not load bundled classroom HTML", e);
            showLoadError(webView, "خطا در باز کردن کلاس آنلاین",
                    "فایل اصلی کلاس داخل برنامه خوانده نشد: " + e.getMessage());
        }
    }

    private void showLoadError(WebView view, String title, String detail) {
        String safeTitle = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;");
        String safeDetail = detail.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\\n", "<br>");
        String html = "<html><meta name='viewport' content='width=device-width,initial-scale=1'><body style='margin:0;background:#101522;color:#fff;font-family:sans-serif;display:flex;min-height:100vh;align-items:center;justify-content:center;text-align:center'><main style='padding:28px'><h2>" + safeTitle + "</h2><p style='line-height:1.8;color:#d6d9e2'>" + safeDetail + "</p><a style='display:inline-block;margin-top:18px;padding:13px 22px;background:#b7202e;color:white;text-decoration:none;border-radius:10px' href='https://frahoosh.ir/online-class/'>باز کردن دوباره کلاس</a></main></body></html>";
        view.loadDataWithBaseURL("https://frahoosh.ir/", html, "text/html", "UTF-8", null);
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
