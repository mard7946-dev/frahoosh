package ir.frahoosh;

import android.app.Activity;
import android.app.Dialog;
import android.graphics.Color;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.FrameLayout;
import android.util.Log;

public final class FrahooshClassroomLauncher {
    private static final String TAG = "FrahooshClassroom";
    private static final Handler MAIN = new Handler(Looper.getMainLooper());
    private static Dialog activeDialog;
    private static WebView activeWebView;

    private FrahooshClassroomLauncher() {}

    public static void open(final Activity activity, final String html) {
        if (activity == null) {
            Log.e(TAG, "open() called without Activity");
            return;
        }

        MAIN.post(new Runnable() {
            @Override
            public void run() {
                try {
                    closeInternal();

                    final WebView web = new WebView(activity);
                    activeWebView = web;

                    WebSettings settings = web.getSettings();
                    settings.setJavaScriptEnabled(true);
                    settings.setDomStorageEnabled(true);
                    settings.setDatabaseEnabled(true);
                    settings.setMediaPlaybackRequiresUserGesture(false);
                    settings.setAllowFileAccess(false);
                    settings.setAllowContentAccess(false);
                    settings.setJavaScriptCanOpenWindowsAutomatically(true);
                    settings.setSupportMultipleWindows(true);
                    settings.setBuiltInZoomControls(false);
                    settings.setDisplayZoomControls(false);
                    settings.setLoadWithOverviewMode(true);
                    settings.setUseWideViewPort(true);
                    settings.setCacheMode(WebSettings.LOAD_DEFAULT);

                    /*
                     * Keep WebView hardware-accelerated. Forcing a WebView to
                     * LAYER_TYPE_SOFTWARE can break WebRTC video rendering on
                     * Android devices and produce black remote/local video
                     * surfaces even when getUserMedia succeeds.
                     */
                    web.setLayerType(View.LAYER_TYPE_HARDWARE, null);
                    web.setBackgroundColor(Color.WHITE);

                    web.setWebViewClient(new WebViewClient() {
                        @Override
                        public boolean shouldOverrideUrlLoading(WebView view, String url) {
                            if ("about:blank".equalsIgnoreCase(url)) {
                                close();
                                return true;
                            }
                            return false;
                        }

                        @Override
                        public void onPageFinished(WebView view, String url) {
                            Log.i(TAG, "Classroom page loaded: " + url);
                        }

                        @Override
                        public void onReceivedError(
                                WebView view,
                                android.webkit.WebResourceRequest request,
                                android.webkit.WebResourceError error) {
                            if (request != null && request.isForMainFrame()) {
                                Log.e(TAG, "Classroom WebView error: " + error);
                            }
                        }

                        @Override
                        public void onReceivedHttpError(
                                WebView view,
                                android.webkit.WebResourceRequest request,
                                android.webkit.WebResourceResponse response) {
                            if (request != null && request.isForMainFrame()) {
                                Log.e(TAG, "Classroom HTTP error: " + response.getStatusCode());
                            }
                        }

                        @Override
                        public void onReceivedSslError(
                                WebView view,
                                android.webkit.SslErrorHandler handler,
                                android.net.http.SslError error) {
                            // Never bypass certificate validation. Fail closed and log
                            // enough detail to distinguish expiry, hostname, and chain issues.
                            String failingUrl = error == null ? "(unknown URL)" : error.getUrl();
                            String primaryError = error == null
                                    ? "unknown"
                                    : android.net.http.SslError.SSL_UNTRUSTED == error.getPrimaryError()
                                            ? "untrusted certificate"
                                            : android.net.http.SslError.SSL_EXPIRED == error.getPrimaryError()
                                                    ? "expired certificate"
                                                    : android.net.http.SslError.SSL_IDMISMATCH == error.getPrimaryError()
                                                            ? "hostname mismatch"
                                                            : android.net.http.SslError.SSL_NOTYETVALID == error.getPrimaryError()
                                                                    ? "certificate not yet valid"
                                                                    : "SSL error " + error.getPrimaryError();
                            Log.e(TAG, "HTTPS certificate validation failed: " + primaryError
                                    + "; url=" + failingUrl
                                    + "; certificate=" + (error == null ? "(unavailable)" : error.getCertificate()));
                            if (handler != null) handler.cancel();
                            MAIN.post(() -> android.widget.Toast.makeText(
                                    activity,
                                    "اتصال امن برقرار نشد؛ گواهی امنیتی frahoosh.ir را بررسی کنید.",
                                    android.widget.Toast.LENGTH_LONG
                            ).show());
                        }
                    });

                    try {
                        FrahooshWebChromeClient chrome = new FrahooshWebChromeClient();
                        chrome.setContext(activity);
                        web.setWebChromeClient(chrome);
                    } catch (Throwable chromeError) {
                        Log.e(TAG, "Could not install Frahoosh WebChromeClient", chromeError);
                        web.setWebChromeClient(new android.webkit.WebChromeClient());
                    }

                    FrameLayout container = new FrameLayout(activity);
                    container.setBackgroundColor(Color.WHITE);
                    container.addView(web, new FrameLayout.LayoutParams(
                            FrameLayout.LayoutParams.MATCH_PARENT,
                            FrameLayout.LayoutParams.MATCH_PARENT
                    ));

                    Button back = new Button(activity);
                    back.setText("بازگشت به فراهوش");
                    back.setTextColor(Color.WHITE);
                    back.setBackgroundColor(Color.rgb(36, 77, 130));
                    FrameLayout.LayoutParams backParams = new FrameLayout.LayoutParams(
                            FrameLayout.LayoutParams.WRAP_CONTENT,
                            FrameLayout.LayoutParams.WRAP_CONTENT
                    );
                    backParams.leftMargin = 18;
                    backParams.topMargin = 18;
                    container.addView(back, backParams);

                    final Dialog dialog = new Dialog(activity);
                    activeDialog = dialog;
                    dialog.setContentView(container);
                    dialog.setCanceledOnTouchOutside(false);
                    dialog.setCancelable(false);

                    back.setOnClickListener(new View.OnClickListener() {
                        @Override
                        public void onClick(View v) {
                            close();
                        }
                    });

                    Window window = dialog.getWindow();
                    if (window != null) {
                        window.setBackgroundDrawableResource(android.R.color.white);
                        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
                        window.addFlags(WindowManager.LayoutParams.FLAG_HARDWARE_ACCELERATED);
                        window.setDimAmount(0.0f);
                    }

                    dialog.show();

                    window = dialog.getWindow();
                    if (window != null) {
                        window.setLayout(
                                WindowManager.LayoutParams.MATCH_PARENT,
                                WindowManager.LayoutParams.MATCH_PARENT
                        );
                        window.addFlags(WindowManager.LayoutParams.FLAG_HARDWARE_ACCELERATED);
                    }

                    container.setVisibility(View.VISIBLE);
                    web.setVisibility(View.VISIBLE);
                    container.bringToFront();
                    web.bringToFront();

                    // Use a real HTTPS origin so WebRTC getUserMedia is eligible.
                    // The HTML is self-contained; only its REST/WebRTC calls need network access.
                    web.loadDataWithBaseURL(
                            "https://frahoosh.ir/online-class/",
                            html == null ? "" : html,
                            "text/html",
                            "UTF-8",
                            "https://frahoosh.ir/online-class/"
                    );

                    Log.i(TAG, "Classroom dialog shown with hardware acceleration");
                } catch (Throwable error) {
                    Log.e(TAG, "Classroom launcher failed", error);
                    closeInternal();
                }
            }
        });
    }

    public static void close() {
        MAIN.post(new Runnable() {
            @Override
            public void run() {
                closeInternal();
            }
        });
    }

    private static void closeInternal() {
        if (activeWebView != null) {
            try {
                activeWebView.stopLoading();
                activeWebView.loadUrl("about:blank");
                activeWebView.destroy();
            } catch (Throwable ignored) {}
            activeWebView = null;
        }

        if (activeDialog != null) {
            try {
                activeDialog.dismiss();
            } catch (Throwable ignored) {}
            activeDialog = null;
        }
    }
}
