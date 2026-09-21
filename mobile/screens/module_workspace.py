    "share_enabled":"اشتراک فعال","snapshot_data":"اطلاعات نسخه","sort_order":"ترتیب",
    "sport_type":"رشته ورزشی","start_at":"شروع","start_date":"تاریخ شروع","start_time_shamsi":"شروع (شمسی)",
    "status":"وضعیت","student_code":"شماره دانش‌آموزی","student_id":"دانش‌آموز",
    "student_name":"نام دانش‌آموز","subject":"درس","submitted_at":"زمان ارسال تکلیف",
    "submitted_at_shamsi":"زمان ارسال شمسی","target_id":"شناسه هدف","target_name":"نام مخاطب",
    "target_role":"نقش مخاطب","target_type":"نوع مخاطب","teacher":"دبیر","teacher_id":"دبیر",
    "teacher_name":"نام دبیر","team_members":"اعضای گروه","term":"نوبت","text":"متن پیام",
    "title":"عنوان","tool_type":"نوع ابزار","transaction_date":"تاریخ تراکنش",
    "transaction_type":"نوع تراکنش","transport_type":"نوع سرویس","updated_at":"آخرین ویرایش",
    "username":"نام کاربری","vehicle_type":"نوع وسیله","week_index":"شماره هفته",
    "weekday":"روز هفته","weekdays":"روزهای هفته","weight":"ضریب","work_experience":"سابقه کار",
};
for _key, _value in _CATALOG_FIELD_LABELS.items():
    if not COLUMNS.get(_key):
        COLUMNS[_key] = _value


# Explicit write policy. Reads remain available through the existing API for all visible tables.
EDITABLE = {
    "manager": {table for items in SUBMENUS.values() for _, table in items},
    "educational": {
        "attendance","student_referrals","meeting_requests","ai_smart_reports","online_classes",
        "messages","message_targets","exam_schedule","quiz_questions","teacher_classes","students",
        "educational_followups","academic_followups","khwarizmi_registrations"
    },
    "executive": {
        "students","executive_classes","staff","archive_items","executive_operations","executive_reports",
        "report_cards","online_classes","messages","weekly_schedule","discipline_records",
        "certificate_requests","school_class_config","parent_children","assets","student_cards","class_cards",
        "certificates","executive_requests","surveys"
    },
    "cultural": {
        "morning_ceremony","cultural_competitions","activity_programs","competitions",
        "educational_activities","cultural_reports","cultural_activity_registrations",
        "messages","message_targets","activity_offers","activity_registrations",
        "student_council","basij_registration","school_ally","school_mayor","qari_registration",
        "art_competitions","sport_competitions","morning_leaders"
    },
    "advisor": {
        "counselor_board","counseling_records","counseling_followups","student_referrals",
        "parent_meetings","counseling_classes","parent_activities","counseling_guidance",
        "ai_smart_reports","discipline_records","messages","message_targets","educational_followups",
        "academic_followups","parent_meeting_requests"
    },
    "teacher": {
        "teacher_classes","attendance","grades","assignments","teacher_exams","online_classes",
        "lesson_plans","teacher_meetings","teacher_activities","grade_items","discipline_records",
        "messages","message_targets","student_referrals"
    },
    "finance": {
        "finance_accounts","finance_transactions","finance_donations","payment_offers","payment_attempts","payment_records"
    },
}
# Normalize write permissions to the canonical backend table ids used by the
# mother contract.  Without this step an alias such as "virtual" would render
# correctly but lose the three CRUD actions after resolving to online_classes.
for _role_key in tuple(EDITABLE):
    _expanded = set(EDITABLE.get(_role_key) or set())
    for _panel_items in _MOTHER_MODULES.values():
        for _label, _module_id in _panel_items:
            _table_id = _MOTHER_TABLE_ALIASES.get(_module_id, _module_id)
            if _role_key == "manager" or _module_id in _expanded or _table_id in _expanded:
                _expanded.add(_table_id)
    EDITABLE[_role_key] = _expanded
EDITABLE.setdefault("manager", set()).update(_MOTHER_TABLE_ALIASES.values())
EDITABLE.setdefault("manager", set()).update({"meeting_requests","certificate_requests"})
EDITABLE.setdefault("executive", set()).update({"meeting_requests","certificate_requests"})
EDITABLE.setdefault("educational", set()).update({"meeting_requests"})
EDITABLE.setdefault("cultural", set()).update({"meeting_requests"})
EDITABLE.setdefault("advisor", set()).update({"meeting_requests"})
EDITABLE.setdefault("teacher", set()).update({"meeting_requests"})

FORMS = {
    "students":["first_name","last_name","father_name","mother_name","national_code","birth_certificate_place","birth_place","religion","sect","nationality","student_phone","father_phone","mother_phone","grade","class_name"],
    "teachers":["first_name","last_name","father_name","national_code","personnel_code","birth_certificate_place","birth_place","nationality","religion","sect","service_years","phone","subject"],
    "staff":["first_name","last_name","father_name","national_code","personnel_code","birth_certificate_place","birth_place","nationality","religion","sect","service_years","phone","role"],
    "school_events":["title","description","event_date","status"],