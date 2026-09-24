"""Real Excel/PDF import/export for Frahoosh."""
from pathlib import Path
from datetime import datetime

def app_dir():
    try:
        from kivy.app import App
        p=Path(App.get_running_app().user_data_dir)
    except Exception:
        p=Path.cwd()
    p.mkdir(parents=True,exist_ok=True)
    return p

def btitr_path():
    from mobile.config import FONT_REGULAR
    candidates=[Path(FONT_REGULAR),Path(__file__).resolve().parents[1]/"assets"/"BTitrBd.ttf"]
    for p in candidates:
        if p.is_file():
            return str(p)
    raise FileNotFoundError("فونت BTitrBd.ttf پیدا نشد.")

def _rtl(value):
    text=str(value or "")
    try:
        from arabic_reshaper import reshape
        from bidi.algorithm import get_display
        return get_display(reshape(text))
    except Exception:
        return text

def export_excel(rows,fields,title="frahoosh"):
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment
    path=app_dir()/f"{title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    wb=Workbook(); ws=wb.active; ws.title="داده‌ها"
    for j,k in enumerate(fields,1):
        cell=ws.cell(1,j,_rtl(k))
        cell.font=Font(name="BTitr",bold=True)
        cell.alignment=Alignment(horizontal="right")
    for i,r in enumerate(rows or [],2):
        for j,k in enumerate(fields,1):
            cell=ws.cell(i,j,str((r or {}).get(k,"")))
            cell.font=Font(name="BTitr")
            cell.alignment=Alignment(horizontal="right")
    wb.save(path)
    return str(path)

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
    font_path=btitr_path()
    pdfmetrics.registerFont(TTFont("FrahooshBTitr",font_path))
    path=app_dir()/f"{title.replace(' ','_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    c=canvas.Canvas(str(path),pagesize=landscape(A4))
    w,h=landscape(A4)
    c.setFont("FrahooshBTitr",10)
    c.drawCentredString(w/2,h-25,_rtl(title))
    cw=(w-30)/max(1,len(fields)); y=h-45; c.setFont("FrahooshBTitr",7)
    for j,k in enumerate(fields):
        c.rect(15+j*cw,y-12,cw,12); c.drawCentredString(15+j*cw+cw/2,y-9,_rtl(str(k))[:30])
    y-=12
    for r in rows or []:
        if y<25:
            c.showPage(); y=h-25; c.setFont("FrahooshBTitr",7)
        for j,k in enumerate(fields):
            value=_rtl(str((r or {}).get(k,"")))[:28]
            c.rect(15+j*cw,y-12,cw,12); c.drawCentredString(15+j*cw+cw/2,y-9,value)
        y-=12
    c.save()
    return str(path)
