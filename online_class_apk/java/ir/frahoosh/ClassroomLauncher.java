package ir.frahoosh;
import android.app.Activity;
import android.app.Dialog;
import android.graphics.Color;
import android.os.Handler;
import android.os.Looper;
import android.view.ViewGroup;
import android.webkit.PermissionRequest;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
public final class ClassroomLauncher {
  private static final Handler H=new Handler(Looper.getMainLooper());
  private static Dialog dialog; private static WebView web;
  public static void open(Activity a,String url){
    H.post(()->{
      web=new WebView(a);
      WebSettings s=web.getSettings();
      s.setJavaScriptEnabled(true); s.setDomStorageEnabled(true);
      s.setMediaPlaybackRequiresUserGesture(false);
      s.setJavaScriptCanOpenWindowsAutomatically(true);
      web.setWebChromeClient(new WebChromeClient(){
        @Override public void onPermissionRequest(final PermissionRequest r){
          a.runOnUiThread(()->r.grant(r.getResources()));
        }
      });
      web.setWebViewClient(new WebViewClient());
      dialog=new Dialog(a);
      dialog.setContentView(web);
      dialog.setCancelable(true);
      dialog.show();
      if(dialog.getWindow()!=null) dialog.getWindow().setLayout(-1,-1);
      web.loadUrl(url);
    });
  }
}
