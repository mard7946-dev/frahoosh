package ir.frahoosh;

import android.Manifest;
import android.app.Activity;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.os.Handler;
import android.os.Looper;
import android.webkit.PermissionRequest;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebSettings;
import android.view.View;
import android.view.Window;

public final class ClassroomLauncher {
  private static WebView web;

  public static void open(final Activity activity, final String url) {
    if (activity == null) return;

    new Handler(Looper.getMainLooper()).post(() -> {
      try {
        web = new WebView(activity);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setJavaScriptCanOpenWindowsAutomatically(true);
        s.setAllowFileAccess(true);
        s.setAllowContentAccess(true);
        s.setSupportMultipleWindows(false);

        web.setBackgroundColor(Color.BLACK);
        web.setWebViewClient(new WebViewClient() {
          @Override
          public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
            view.loadUrl(request.getUrl().toString());
            return true;
          }
        });

        web.setWebChromeClient(new WebChromeClient() {
          @Override
          public void onPermissionRequest(final PermissionRequest request) {
            activity.runOnUiThread(() -> {
              boolean camera = activity.checkSelfPermission(Manifest.permission.CAMERA)
                  == PackageManager.PERMISSION_GRANTED;
              boolean mic = activity.checkSelfPermission(Manifest.permission.RECORD_AUDIO)
                  == PackageManager.PERMISSION_GRANTED;

              java.util.ArrayList<String> allowed = new java.util.ArrayList<>();
              for (String resource : request.getResources()) {
                if (PermissionRequest.RESOURCE_VIDEO_CAPTURE.equals(resource) && camera)
                  allowed.add(resource);
                else if (PermissionRequest.RESOURCE_AUDIO_CAPTURE.equals(resource) && mic)
                  allowed.add(resource);
              }
              if (!allowed.isEmpty())
                request.grant(allowed.toArray(new String[0]));
              else
                request.deny();
            });
          }
        });

        activity.setContentView(web);
        Window w = activity.getWindow();
        w.setStatusBarColor(Color.BLACK);
        w.setNavigationBarColor(Color.BLACK);
        web.loadUrl(url);
      } catch (Throwable ignored) {
        // Keep the host activity alive if WebView initialization fails.
      }
    });
  }
}
