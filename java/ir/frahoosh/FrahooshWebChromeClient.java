package ir.frahoosh;

import android.net.Uri;
import android.webkit.PermissionRequest;
import android.webkit.WebChromeClient;

public class FrahooshWebChromeClient extends WebChromeClient {
    @Override
    public void onPermissionRequest(final PermissionRequest request) {
        final Uri origin = request.getOrigin();
        if (origin == null || (!"https".equalsIgnoreCase(origin.getScheme())
                || !"frahoosh.ir".equalsIgnoreCase(origin.getHost()))) {
            request.deny();
            return;
        }

        String[] requested = request.getResources();
        java.util.ArrayList<String> allowed = new java.util.ArrayList<>();
        for (String resource : requested) {
            if (PermissionRequest.RESOURCE_AUDIO_CAPTURE.equals(resource)
                    || PermissionRequest.RESOURCE_VIDEO_CAPTURE.equals(resource)) {
                allowed.add(resource);
            }
        }

        if (allowed.isEmpty()) {
            request.deny();
        } else {
            request.grant(allowed.toArray(new String[0]));
        }
    }
}
