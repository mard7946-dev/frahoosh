"""Real Excel/PDF import/export for Frahoosh."""
from pathlib import Path
from datetime import datetime
def app_dir():
    try:
        from kivy.app import App
        p=Path(App.get_running_app().user_data_dir)
    except Exception:p=Path.cwd()
    p.mkdir(parents=True,exist_ok=True);return p
def export_excel(rows,fields,title="frahoosh"):
    from openpyxl import Workbook
    from openpyxl.styles import Font
    path=app_dir()/f"{title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"; wb=Workbook(); ws=wb.active
    for j,k in enumerate(fields,1):ws.cell(1,j,k).font=Font(bold=True)
    for i,r in enumerate(rows or [],2):
        for j,k in enumerate(fields,1):ws.cell(i,j,str((r or {}).get(k,"")))
    wb.save(path);return str(path)
def import_excel(path):
    from openpyxl import load_workbook
    vals=list(load_workbook(path,read_only=True,data_only=True).active.iter_rows(values_only=True))
    if not vals:return []
    h=[str(x).strip() for x in vals[0] if x not in (None,"")]
    return [{h[i]:r[i] for i in range(min(len(h),len(r))) if h[i] and r[i] is not None} for r in vals[1:]]
def export_pdf(rows,fields,title="گزارش فراهوش"):
    from reportlab.lib.pagesizes import A4,landscape
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    try:
        from mobile.ui import font_name
        pdfmetrics.registerFont(TTFont("Frahoosh",font_name()));font="Frahoosh"
    except Exception:font="Helvetica"
    path=app_dir()/f"{title.replace(' ','_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"; c=canvas.Canvas(str(path),pagesize=landscape(A4));w,h=landscape(A4);c.setFont(font,10);c.drawCentredString(w/2,h-25,title)
    cw=(w-30)/max(1,len(fields));y=h-45;c.setFont(font,7)
    for j,k in enumerate(fields):c.rect(15+j*cw,y-12,cw,12);c.drawCentredString(15+j*cw+cw/2,y-9,str(k)[:20])
    y-=12
    for r in rows or []:
        if y<25:c.showPage();y=h-25
        for j,k in enumerate(fields):c.rect(15+j*cw,y-12,cw,12);c.drawCentredString(15+j*cw+cw/2,y-9,str((r or {}).get(k,""))[:24])
        y-=12
    c.save();return str(path)
