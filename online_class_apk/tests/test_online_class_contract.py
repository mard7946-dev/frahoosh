from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
ENTRY = ROOT / "web" / "online-class" / "index.html"
ROOM = ROOT / "web" / "online-class" / "room.html"
CLASSROOM = ROOT / "mobile" / "assets" / "online_class.html"
PATCH = ROOT / "online_class_apk" / "app" / "src" / "main" / "assets" / "room_assets" / "classroom_patch.js"


class OnlineClassContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entry = ENTRY.read_text(encoding="utf-8")
        cls.room = ROOM.read_text(encoding="utf-8")
        cls.classroom = CLASSROOM.read_text(encoding="utf-8")
        cls.patch = PATCH.read_text(encoding="utf-8")

    def test_entry_offers_three_distinct_roles(self):
        for role in ("manager", "teacher", "student"):
            self.assertIn(f"chooseRole('{role}')", self.entry)
        self.assertNotIn("chooseRole('staff')", self.entry)

    def test_teacher_and_student_rosters_are_local_not_posted_to_supabase(self):
        self.assertIn('writeLocalRows("frahoosh_local_students"', self.entry)
        self.assertIn('writeLocalRows("frahoosh_local_teachers"', self.entry)
        import_block = self.entry[self.entry.index("async function importPeople"):self.entry.index("let classWizardStep=0;")]
        self.assertNotIn('api("/rest/v1/teachers"', import_block)
        self.assertIn("اطلاعات به Supabase ارسال نشد", import_block)

    def test_manual_roster_forms_match_excel_templates_and_mark_required_fields(self):
        for field in ("newStudentFirst", "newStudentLast", "newStudentClass",
                      "newTeacherFirst", "newTeacherLast", "newTeacherCode",
                      "newTeacherEmail", "newTeacherPhone", "newTeacherSubject"):
            self.assertIn(f'id="{field}"', self.entry)
        self.assertIn('id="downloadStudentsTemplate"', self.entry)
        self.assertIn('id="downloadTeachersTemplate"', self.entry)
        self.assertIn('id="saveStudentLocal"', self.entry)
        self.assertIn('class="required-mark"', self.entry)
        self.assertIn('class="optional-mark">(اختیاری)', self.entry)
        self.assertIn('["نام *","نام خانوادگی *","کلاس *"]', self.entry)
        self.assertIn('"ایمیل (اختیاری)"', self.entry)

    def test_local_teacher_and_student_rosters_support_edit_and_confirmed_delete(self):
        for token in (
            'data-edit-local-student=',
            'data-remove-local-student=',
            'data-edit-local-teacher=',
            'data-remove-local-teacher=',
            'editingLocalStudentIndex!==null',
            'editingLocalTeacherIndex!==null',
            'cancelStudentEdit',
            'cancelTeacherEdit',
            'if(!confirm("این دانش‌آموز از فهرست محلی همین دستگاه حذف شود؟"))',
            'if(!confirm("این دبیر از فهرست محلی همین دستگاه حذف شود؟"))',
        ):
            self.assertIn(token, self.entry)
        self.assertIn('writeLocalRows("frahoosh_local_students"', self.entry)
        self.assertIn('writeLocalRows("frahoosh_local_teachers"', self.entry)

    def test_excel_templates_work_in_android_webview_and_report_results(self):
        self.assertIn('src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"', self.entry)
        self.assertIn('window.FrahooshNative.saveExcelTemplate(fileName,XLSX.write(wb,{bookType:"xlsx",type:"base64"}))', self.entry)
        self.assertIn('window.frahooshTemplateSaved=function(success)', self.entry)
        self.assertIn('XLSX.writeFile(wb,fileName)', self.entry)
        activity = (ROOT / "online_class_apk" / "app" / "src" / "main" / "java" /
                    "ir" / "frahoosh" / "classroom" / "MainActivity.java").read_text(encoding="utf-8")
        self.assertIn('addJavascriptInterface(new TemplateDownloadBridge(), "FrahooshNative")', activity)
        self.assertIn('MediaStore.Downloads.EXTERNAL_CONTENT_URI', activity)
        self.assertIn('onJsAlert(', activity)
        self.assertIn('onJsConfirm(', activity)
        self.assertIn('@JavascriptInterface', activity)

    def test_weekly_schedule_uses_existing_supabase_contract(self):
        self.assertIn("weekly_schedule_entries", self.entry)
        self.assertIn("get_student_class_schedule", self.entry)
        self.assertIn('id="scheduleDay"', self.entry)
        self.assertIn('id="studentSchedule"', self.entry)
        self.assertIn('register_online_class_student_guest', self.entry)
        self.assertIn('location.href="room.html"', self.entry)

    def test_weekly_bell_times_are_editable_and_shared_with_apk(self):
        for field in ('scheduleStartTime', 'scheduleEndTime'):
            self.assertIn(f'id="{field}"', self.entry)
        self.assertIn('data-edit-schedule=', self.entry)
        self.assertIn('start_time,end_time', self.entry)
        self.assertIn('if(start_time>=end_time)', self.entry)
        self.assertIn('weekly_schedule_entries', self.entry)
        self.assertIn('ساعت پایان باید بعد از ساعت شروع باشد.', self.entry)
        migration = (ROOT / "supabase" / "migrations" /
                     "20261014070000_weekly_schedule_bell_time_automation.sql").read_text(encoding="utf-8")
        self.assertIn("trg_validate_weekly_schedule_bell_times", migration)
        self.assertIn("refresh_online_class_statuses", migration)
        self.assertIn("Asia/Tehran", migration)
        self.assertIn("ورود دبیر به این کلاس فقط در بازه زمانی", migration)

    def test_manager_can_open_class_without_implicitly_starting_teacher_session(self):
        open_room = self.entry.split("async function openRoom(id)", 1)[1].split("$(\"importStudents\")", 1)[0]
        self.assertIn("if(isManager){/* Manager may inspect any class without implicitly starting the teacher session. */", open_room)
        manager_branch = open_room.split("if(isManager){", 1)[1].split("}else{", 1)[0]
        self.assertNotIn("start_online_class_session", manager_branch)
        self.assertIn("هنوز دبیر کلاس را شروع نکرده است", open_room)

    def test_room_bootstrap_has_cross_origin_source_fallbacks_for_raw_githack(self):
        self.assertIn("https://raw.githubusercontent.com/mard7946-dev/frahoosh/fix/classroom-audio-timer-menu/mobile/assets/online_class.html", (ROOT / "web" / "online-class" / "room.html").read_text(encoding="utf-8"))
        self.assertIn("https://raw.githubusercontent.com/mard7946-dev/frahoosh/fix/classroom-audio-timer-menu/online_class_apk/classroom_patch.js", (ROOT / "web" / "online-class" / "room.html").read_text(encoding="utf-8"))

    def test_room_requires_a_complete_authenticated_session(self):
        self.assertIn('!config.token', self.room)
        self.assertIn('!config.userId', self.room)
        self.assertIn('frahoosh_online_class_config', self.room)

    def test_student_tools_remain_teacher_permission_gated(self):
        self.assertIn('const student=', self.patch)
        self.assertIn('const controller=', self.patch)
        self.assertIn('tools_permission', self.patch)
        self.assertIn('pollPermissions', self.patch)


    def test_apk_bundles_exact_same_entry_and_classroom_sources(self):
        apk_entry = ROOT / "online_class_apk" / "app" / "src" / "main" / "assets" / "index.html"
        apk_room = ROOT / "online_class_apk" / "app" / "src" / "main" / "assets" / "room.html"
        apk_classroom = ROOT / "online_class_apk" / "app" / "src" / "main" / "assets" / "room_assets" / "online_class.html"
        apk_patch = ROOT / "online_class_apk" / "app" / "src" / "main" / "assets" / "room_assets" / "classroom_patch.js"
        web_classroom = ROOT / "mobile" / "assets" / "online_class.html"
        source_patch = ROOT / "online_class_apk" / "classroom_patch.js"
        self.assertEqual(self.entry, apk_entry.read_text(encoding="utf-8"))
        self.assertEqual(self.room, apk_room.read_text(encoding="utf-8"))
        self.assertEqual(web_classroom.read_text(encoding="utf-8"), apk_classroom.read_text(encoding="utf-8"))
        self.assertEqual(source_patch.read_text(encoding="utf-8"), apk_patch.read_text(encoding="utf-8"))


    def test_class_creation_persists_valid_jalali_date_and_24_hour_time(self):
        self.assertIn('classWizardStep===4?$("cdateDisplay")', self.entry)
        self.assertIn('if(!/^\\d{4}-\\d{2}-\\d{2}$/.test(selectedDate))', self.entry)
        self.assertIn('if(!/^(?:[01]\\d|2[0-3]):[0-5]\\d$/.test(selectedTime))', self.entry)
        for field in ("start_time_shamsi", "end_time_shamsi", "start_at", "end_at"):
            self.assertIn(field, self.entry)
        self.assertIn('unicode-bidi:isolate-override!important', self.entry)
        self.assertIn('timeZone:"Asia/Tehran"', self.entry)
        self.assertIn('function todayJalali(){const p=Object.fromEntries', self.entry)


    def test_student_schedule_auto_refreshes_and_uses_server_bell_times(self):
        self.assertIn("function getTehranBellState(row)", self.entry)
        self.assertIn("showStudentSchedule(true)", self.entry)
        self.assertIn("startTeacherSchedulePolling()", self.entry)
        self.assertIn("sessionId:s[0]?.id||null", self.entry)
        migration = (ROOT / "supabase" / "migrations" /
                     "20261014072000_weekly_schedule_runtime_times_and_session_close.sql").read_text(encoding="utf-8")
        self.assertIn("start_time time without time zone", migration)
        self.assertIn("end_time time without time zone", migration)
        self.assertIn("drop function if exists public.get_student_class_schedule(text)", migration)

    def test_transient_session_polling_never_ejects_active_classroom(self):
        self.assertIn("CLASS_SESSION_ID_MISMATCH; preserving active classroom media", self.classroom)
        self.assertIn("temporarily missing/RLS-filtered session row must never tear down working audio/video", self.classroom)
        refresh = self.classroom.split("async function refreshSessionTimer()", 1)[1].split("async function loadAttendance()", 1)[0]
        self.assertNotIn("closeClassAfterServerEnd()", refresh)
        self.assertIn("updateClassTimer()", refresh)

    def test_classroom_grants_webview_audio_without_requiring_camera_permission(self):
        activity = (ROOT / "online_class_apk" / "app" / "src" / "main" / "java" /
                    "ir" / "frahoosh" / "classroom" / "MainActivity.java").read_text(encoding="utf-8")
        self.assertIn("buildWebView();\n        requestMediaPermissions();", activity)
        self.assertIn("private boolean hasRequestedMediaPermissions(PermissionRequest request)", activity)
        self.assertIn("RESOURCE_AUDIO_CAPTURE.equals(resource)", activity)
        self.assertIn("Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED", activity)
        self.assertIn("s.setMediaPlaybackRequiresUserGesture(false);", activity)
        permission_result = activity.split("public void onRequestPermissionsResult", 1)[1].split("@Override", 1)[0]
        self.assertIn("grantWebMediaPermission(request);", permission_result)
        self.assertNotIn("if (hasMediaPermissions())", permission_result)
        self.assertIn("Denying camera must not mute audio", permission_result)

    def test_shared_room_loader_keeps_classroom_in_the_top_level_webview(self):
        self.assertIn('https://raw.githubusercontent.com/mard7946-dev/frahoosh/fix/classroom-audio-timer-menu/mobile/assets/online_class.html', self.room)
        self.assertIn('https://raw.githubusercontent.com/mard7946-dev/frahoosh/fix/classroom-audio-timer-menu/online_class_apk/classroom_patch.js', self.room)
        self.assertIn('../../online_class_apk/classroom_patch.js', self.room)
        self.assertIn('new URL("index.html",location.href).href', self.room)
        self.assertIn("document.open();document.write(page);document.close()", self.room)
        self.assertNotIn("frame.srcdoc", self.room)
        self.assertNotIn("<iframe", self.room)

    def test_remote_audio_uses_an_explicit_audio_playback_path(self):
        self.assertIn('<audio autoplay playsinline></audio>', self.classroom)
        self.assertIn('audio.srcObject=stream', self.classroom)
        self.assertIn('REMOTE_AUDIO_PLAY_BLOCKED', self.classroom)
        self.assertIn('e.streams&&e.streams[0]?e.streams[0]:new MediaStream([e.track])', self.classroom)

    def test_attendance_refresh_only_uses_an_active_session_for_the_timer(self):
        self.assertIn('online_class_sessions?class_id=eq."+C.classId+"&ended_at=is.null&order=id.desc&limit=1', self.classroom)

    def test_hidden_student_tool_menu_cannot_toggle_class_layout(self):
        self.assertIn('const mt=$("menuToggle");if(mt){if(!teacher){mt.style.display="none"}else mt.onclick=e=>{e.preventDefault();e.stopPropagation();drawer.open=!drawer.open;layout.classList.toggle("drawer-open",drawer.open)}};', self.classroom)

    def test_whiteboard_fills_remaining_viewport_when_header_wraps(self):
        self.assertIn(".layout{flex:1 1 0;height:auto;min-height:0", self.classroom)
        self.assertIn(".boardwrap{flex:1 1 0;height:auto;min-height:0", self.classroom)

    def test_raw_githack_paths_and_manager_session_start_are_supported(self):
        apk_entry = ROOT / "online_class_apk" / "app" / "src" / "main" / "assets" / "index.html"
        apk_room = ROOT / "online_class_apk" / "app" / "src" / "main" / "assets" / "room.html"
        self.assertEqual(self.entry, apk_entry.read_text(encoding="utf-8"))
        self.assertEqual(self.room, apk_room.read_text(encoding="utf-8"))
        for entry in (self.entry, apk_entry.read_text(encoding="utf-8")):
            self.assertIn('resolveEmailsByUsername(identifier)', entry)
            self.assertIn('account_settings?select=email&username=eq.', entry)
            self.assertIn('if(isManager){/* Manager may inspect any class without implicitly starting the teacher session. */', entry)
            self.assertNotIn('if(!s[0]){const started=await api("/rest/v1/rpc/start_online_class_session"', entry)
            self.assertIn('sessionStartedAt:s[0]?.started_at||null', entry)
        for room in (self.room, apk_room.read_text(encoding="utf-8")):
            self.assertIn("../../mobile/assets/online_class.html", room)
            self.assertIn("../../online_class_apk/classroom_patch.js", room)
        self.assertIn('location.replace(C.guestInviteBase||new URL("index.html",location.href).href)', self.classroom)
        self.assertIn('resumeRemoteAudio()', self.classroom)


if __name__ == "__main__":
    unittest.main()
