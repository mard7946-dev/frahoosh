package ir.frahoosh;

import android.app.Activity;
import android.webkit.PermissionRequest;
import android.webkit.WebChromeClient;
import android.webkit.ConsoleMessage;
import android.util.Log;

public class FrahooshWebChromeClient extends WebChromeClient {
    private Activity context;

    public FrahooshWebChromeClient() {}

    public void setContext(Activity activity) { this.context = activity; }

    @Override
    public void onPermissionRequest(final PermissionRequest request) {
        if (request == null || context == null) {
            if (request != null) request.deny();
            return;
        }
        context.runOnUiThread(new Runnable() {
            @Override public void run() {
                try { request.grant(request.getResources()); }
                catch (Exception e) {
                    Log.e("FrahooshWebChrome", "permission request failed", e);
                    try { request.deny(); } catch (Exception ignored) {}
                }
            }
        });
    }

    @Override
    public boolean onConsoleMessage(ConsoleMessage message) {
        if (message != null)
            Log.d("FrahooshWebChrome", message.message() + " @" + message.sourceId() + ":" + message.lineNumber());
        return true;
    }
}
