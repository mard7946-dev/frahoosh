from pathlib import Path
from datetime import datetime

def _rtl(text):
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(str(text or "")))
    except Exception:
        return str(text or "")

def _font_path():
    p = Path(__file__).resolve().parents[1] / "assets" / "BTitrBd.ttf"
    return p if p.is_file() else None

def export_table_pdf(table, rows, fields, labels, output_path, title="گزارش فراهوش"):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    font = "Helvetica"
    fp = _font_path()
    if fp:
        try:
            pdfmetrics.registerFont(TTFont("FrahooshPDF", str(fp)))
            font = "FrahooshPDF"
        except Exception:
            pass
    page = landscape(A4)
    c = canvas.Canvas(str(output_path), pagesize=page)
    w, h = page
    c.setFont(font, 14)
    c.drawCentredString(w/2, h-32, _rtl(title))
    c.setFont(font, 8)
    y = h-58
    visible = [f for f in fields if f]
    if not visible:
        visible = list(rows[0].keys()) if rows else []
    colw = max(55, (w-36)/max(1, len(visible)))
    def header():
        nonlocal y
        c.setFont(font, 8)
        for i,f in enumerate(visible):
            x=18+i*colw
            c.rect(x,y-14,colw,16)
            c.drawCentredString(x+colw/2,y-10,_rtl(labels.get(f,f))[:22])
        y -= 18
    header()
    for row in rows:
        if y < 28:
            c.showPage(); y=h-32; header()
        for i,f in enumerate(visible):
            x=18+i*colw
            c.rect(x,y-14,colw,16)
            value=str(row.get(f,"") or "")
            c.drawCentredString(x+colw/2,y-10,_rtl(value)[:28])
        y -= 16
    c.save()
    return output_path

def generate_enrollment_certificate(row, output_path, school_name="دبیرستان سردار شهید حاجی زاده ۲", school_code="", academic_year="1404-1405", manager_name="حسن مردانه جهان تیغ"):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    font="Helvetica"
    fp=_font_path()
    if fp:
        try:
            pdfmetrics.registerFont(TTFont("FrahooshPDF",str(fp))); font="FrahooshPDF"
        except Exception: pass
    c=canvas.Canvas(str(output_path), pagesize=A4)
    w,h=A4
    c.setLineWidth(1)
    c.rect(28,28,w-56,h-56)
    c.setFont(font,12)
    c.drawRightString(w-55,h-58,_rtl("جمهوری اسلامی ایران"))
    c.drawRightString(w-55,h-78,_rtl("وزارت آموزش وپرورش"))
    c.setFont(font,18); c.drawCentredString(w/2,h-118,_rtl("گواهی اشتغال به تحصیل"))
    c.setFont(font,11)
    name=row.get("student_name") or row.get("name") or ""
    national=row.get("national_code") or ""
    father=row.get("father_name") or ""
    birth=row.get("birth_date") or row.get("date_of_birth") or ""
    school=row.get("school_name") or school_name
    code=row.get("school_code") or school_code
    grade=row.get("grade") or row.get("grade_level") or ""
    destination=row.get("destination") or ""
    lines=[
        f"بدین وسیله گواهی میشود: {name} کد ملی {national} فرزند: {father}",
        f"شماره شناسنامه: {national}    تاریخ تولد: {birth}    سال تحصیلی: {academic_year}",
        f"در مدرسه: {school} ({code})    در پایه: {grade}",
        "مشغول به تحصیل میباشد",
        f"این گواهی طبق تقاضای مورخ : {row.get('request_date') or ''}",
        f"فقط به منظور ارائه به: {destination}",
        "صادر گردید و فاقد هرگونه ارزش دیگری می باشد.",
    ]
    y=h-165
    for line in lines:
        c.drawRightString(w-58,y,_rtl(line)); y-=28
    c.drawRightString(w-58,125,_rtl("تاریخ"))
    c.drawRightString(w-58,98,_rtl("مهر و امضا مدیر مدرسه"))
    c.drawRightString(w-58,75,_rtl(manager_name))
    c.save()
    return output_path
