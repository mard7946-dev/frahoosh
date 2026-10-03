package ir.frahoosh;

import android.webkit.WebChromeClient;
import android.webkit.PermissionRequest;

public class FrahooshWebChromeClient extends WebChromeClient {
    @Override
    public void onPermissionRequest(final PermissionRequest request) {
        request.getOrigin();
        request.grant(request.getResources());
    }
}