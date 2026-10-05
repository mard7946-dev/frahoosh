package ir.frahoosh;

import android.Manifest;
import android.content.pm.PackageManager;
import android.app.Activity;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.webkit.PermissionRequest;
import android.webkit.WebChromeClient;
import android.webkit.ConsoleMessage;

public class FrahooshWebChromeClient extends WebChromeClient {
    private static final String TAG = "FrahooshWebChrome";
    private final Handler mainHandler = new Handler(Looper.getMainLooper());

    @Override
    public boolean onConsoleMessage(ConsoleMessage cm) {
        if (cm != null) {
            Log.e(TAG, "JS: " + cm.message() + " @ " + cm.sourceId() + ":" + cm.lineNumber());
        }
        return true;
    }

    @Override
    public void onPermissionRequest(final PermissionRequest request) {
        if (request == null) return;

        final String origin = request.getOrigin() == null ? "" : request.getOrigin().toString();
        if (request.getOrigin() == null
                || !"https".equalsIgnoreCase(request.getOrigin().getScheme())
                || !"frahoosh.ir".equalsIgnoreCase(request.getOrigin().getHost())) {
            Log.w(TAG, "Denied untrusted WebView origin: " + origin);
            request.deny();
            return;
        }

        boolean needsCamera = false;
        boolean needsMic = false;
        for (String resource : request.getResources()) {
            if (PermissionRequest.RESOURCE_VIDEO_CAPTURE.equals(resource)) needsCamera = true;
            if (PermissionRequest.RESOURCE_AUDIO_CAPTURE.equals(resource)) needsMic = true;
        }
        if (!needsCamera && !needsMic) {
            request.deny();
            return;
        }

        /*
         * Python requests Android runtime permissions immediately before the
         * WebView is loaded. WebView can raise onPermissionRequest while that
         * Android dialog is still settling. Never call grant() before the
         * corresponding Android runtime permission is actually granted.
         * Poll briefly, then grant the original WebView request.
         */
        final boolean cameraNeeded = needsCamera;
        final boolean micNeeded = needsMic;
        mainHandler.post(() -> {
            requestMissingAndroidPermissions(cameraNeeded, micNeeded);
            grantWhenAndroidPermissionReady(request, cameraNeeded, micNeeded, 0);
        });
    }

    private void requestMissingAndroidPermissions(boolean needsCamera, boolean needsMic) {
        if (activityContext == null) return;
        java.util.ArrayList<String> missing = new java.util.ArrayList<>();
        if (needsCamera && activityContext.checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            missing.add(Manifest.permission.CAMERA);
        }
        if (needsMic && activityContext.checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            missing.add(Manifest.permission.RECORD_AUDIO);
        }
        if (!missing.isEmpty()) {
            try {
                activityContext.requestPermissions(missing.toArray(new String[0]), MEDIA_PERMISSION_REQUEST_CODE);
                Log.d(TAG, "Requested Android media permissions from WebView handshake: " + missing);
            } catch (Exception e) {
                Log.e(TAG, "Android media permission request failed", e);
            }
        }
    }

    private void grantWhenAndroidPermissionReady(
            final PermissionRequest request,
            final boolean needsCamera,
            final boolean needsMic,
            final int attempt) {

        if (request == null) return;

        boolean cameraOk = !needsCamera
                || requestContextHasPermission(request, Manifest.permission.CAMERA);
        boolean micOk = !needsMic
                || requestContextHasPermission(request, Manifest.permission.RECORD_AUDIO);

        if (cameraOk && micOk) {
            try {
                java.util.ArrayList<String> allowed = new java.util.ArrayList<>();
                for (String resource : request.getResources()) {
                    if (PermissionRequest.RESOURCE_AUDIO_CAPTURE.equals(resource)
                            || PermissionRequest.RESOURCE_VIDEO_CAPTURE.equals(resource)) {
                        allowed.add(resource);
                    }
                }
                if (!allowed.isEmpty()) {
                    request.grant(allowed.toArray(new String[0]));
                    Log.d(TAG, "Granted WebView media permission: " + allowed);
                } else {
                    request.deny();
                }
            } catch (Exception e) {
                Log.e(TAG, "WebView permission grant failed", e);
                try { request.deny(); } catch (Exception ignored) {}
            }
            return;
        }

        if (attempt >= 40) {
            Log.e(TAG, "Android camera/microphone permission was not granted in time");
            try { request.deny(); } catch (Exception ignored) {}
            return;
        }

        mainHandler.postDelayed(
                () -> grantWhenAndroidPermissionReady(request, needsCamera, needsMic, attempt + 1),
                250
        );
    }

    private boolean requestContextHasPermission(
            PermissionRequest request, String permission) {
        /*
         * WebView's PermissionRequest does not expose its Context. The
         * WebView implementation is hosted by the Activity, so use the
         * application context carried by the WebView through a small static
         * holder installed by FrahooshWebChromeClient.setContext().
         */
        android.content.Context context = appContext;
        return context != null
                && context.checkSelfPermission(permission) == PackageManager.PERMISSION_GRANTED;
    }

    private static final int MEDIA_PERMISSION_REQUEST_CODE = 9401;
    private android.content.Context appContext;
    private Activity activityContext;

    public void setContext(android.content.Context context) {
        appContext = context == null ? null : context.getApplicationContext();
        activityContext = context instanceof Activity ? (Activity) context : null;
    }

    @Override
    public void onPermissionRequestCanceled(final PermissionRequest request) {
        Log.w(TAG, "WebView media permission request canceled");
        super.onPermissionRequestCanceled(request);
    }
}
