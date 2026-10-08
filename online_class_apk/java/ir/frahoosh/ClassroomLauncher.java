package ir.frahoosh;

import android.Manifest;
import android.app.Activity;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.webkit.PermissionRequest;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebSettings;
import android.view.Window;

public final class ClassroomLauncher {
  private static WebView web;

  public static void open(final Activity activity, final String url) {
    if (activity == null) return;

    activity.runOnUiThread(() -> {
      try {
        if (Build.VERSION.SDK_INT >= 23) {
          String[] permissions = new String[] {
              Manifest.permission.CAMERA,
              Manifest.permission.RECORD_AUDIO
          };
          boolean camera = activity.checkSelfPermission(Manifest.permission.CAMERA)
              == PackageManager.PERMISSION_GRANTED;
          boolean mic = activity.checkSelfPermission(Manifest.permission.RECORD_AUDIO)
              == PackageManager.PERMISSION_GRANTED;
          if (!camera || !mic) {
            activity.requestPermissions(permissions, 4207);
          }
        }

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
        s.setBuiltInZoomControls(false);
        s.setDisplayZoomControls(false);

        web.setBackgroundColor(Color.BLACK);
        web.setWebViewClient(new WebViewClient() {
          @Override
          public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
            return false;
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
                if (PermissionRequest.RESOURCE_VIDEO_CAPTURE.equals(resource) && camera) {
                  allowed.add(resource);
                } else if (PermissionRequest.RESOURCE_AUDIO_CAPTURE.equals(resource) && mic) {
                  allowed.add(resource);
                }
              }
              if (!allowed.isEmpty()) {
                request.grant(allowed.toArray(new String[0]));
              } else {
                request.deny();
              }
            });
          }
        });

        activity.setContentView(web);
        Window w = activity.getWindow();
        w.setStatusBarColor(Color.BLACK);
        w.setNavigationBarColor(Color.BLACK);
        web.loadUrl(url);
      } catch (Throwable error) {
        android.util.Log.e("FrahooshClassroom", "WebView launch failed", error);
      }
    });
  }
}
