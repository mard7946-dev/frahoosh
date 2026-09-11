from threading import Thread

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button

from mobile.config import (
    APP_NAME,
    SYSTEM_TITLE,
    SCHOOL_NAME,
    PRIMARY,
    SECONDARY,
    SUCCESS,
    WHITE,
    ERROR,
)

from mobile.ui import (
    font_name,
    rtl_text,
    PersianTextInput,
)


class LoginScreen(Screen):

    def __init__(
        self,
        app_state,
        **kwargs
    ):

        super().__init__(
            **kwargs
        )

        self.app_state = app_state
        self._busy = False

        self._build()

    def _build(self):

        root = BoxLayout(
            orientation="vertical",
            padding=dp(24),
            spacing=dp(12),
        )

        root.add_widget(
            Label(
                text=rtl_text(
                    APP_NAME
                ),
                font_name=font_name(),
                font_size="36sp",
                bold=True,
                color=PRIMARY,
                size_hint_y=None,
                height=dp(60),
            )
        )

        root.add_widget(
            Label(
                text=rtl_text(
                    SYSTEM_TITLE
                ),
                font_name=font_name(),
                font_size="17sp",
                color=SECONDARY,
                size_hint_y=None,
                height=dp(42),
            )
        )

        root.add_widget(
            Label(
                text=rtl_text(
                    SCHOOL_NAME
                ),
                font_name=font_name(),
                font_size="13sp",
                color=PRIMARY,
                size_hint_y=None,
                height=dp(38),
            )
        )

        root.add_widget(
            Label(
                text=rtl_text(
                    "ورود کاربران"
                ),
                font_name=font_name(),
                font_size="20sp",
                color=PRIMARY,
                bold=True,
                size_hint_y=None,
                height=dp(42),
            )
        )

        self.identifier = PersianTextInput(
            hint_text=rtl_text(
                "کد ملی"
            ),
            multiline=False,
            input_filter="int",
            size_hint_y=None,
            height=dp(54),
            halign="right",
            padding=[
                dp(14),
                dp(14),
            ],
        )

        self.password = PersianTextInput(
            hint_text=rtl_text(
                "رمز عبور"
            ),
            password=True,
            multiline=False,
            size_hint_y=None,
            height=dp(54),
            halign="right",
            padding=[
                dp(14),
                dp(14),
            ],
        )

        self.status = Label(
            text="",
            font_name=font_name(),
            font_size="13sp",
            color=SECONDARY,
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(55),
        )

        self.status.bind(
            size=lambda obj, value:
            setattr(
                obj,
                "text_size",
                value
            )
        )

        self.login_button = Button(
            text=rtl_text(
                "ورود به فراهوش"
            ),
            font_name=font_name(),
            font_size="17sp",
            background_normal="",
            background_color=SUCCESS,
            color=WHITE,
            size_hint_y=None,
            height=dp(56),
        )

        self.login_button.bind(
            on_release=self.login
        )

        root.add_widget(
            self.identifier
        )

        root.add_widget(
            self.password
        )

        root.add_widget(
            self.status
        )

        root.add_widget(
            self.login_button
        )

        root.add_widget(
            Label(
                text=rtl_text(
                    "نام کاربری: کد ملی\n"
                    "رمز عبور پیش‌فرض: حرف اول نام + کد ملی"
                ),
                font_name=font_name(),
                font_size="12sp",
                color=SECONDARY,
                halign="center",
                valign="middle",
            )
        )

        self.add_widget(
            root
        )

    def _set_status(
        self,
        text,
        color=SECONDARY
    ):

        self.status.text = rtl_text(
            text
        )

        self.status.color = color

    def login(self, *_):

        if self._busy:
            return

        identifier = (
            self.identifier.text
            .strip()
        )

        password = (
            self.password.text
        )

        if not identifier:

            self._set_status(
                "کد ملی را وارد کنید.",
                ERROR
            )

            return

        if len(identifier) != 10:

            self._set_status(
                "کد ملی باید ۱۰ رقم باشد.",
                ERROR
            )

            return

        if not password:

            self._set_status(
                "رمز عبور را وارد کنید.",
                ERROR
            )

            return

        if self.app_state is None:

            self._set_status(
                "وضعیت برنامه آماده نیست.",
                ERROR
            )

            return

        if self.app_state.api is None:

            self._set_status(
                "سرویس اتصال آماده نیست.",
                ERROR
            )

            return

        if not self.app_state.api.configured:

            self._set_status(
                "اتصال سرور تنظیم نشده است.",
                ERROR
            )

            return

        self._busy = True
        self.login_button.disabled = True

        self._set_status(
            "در حال بررسی اطلاعات...",
            SECONDARY
        )

        Thread(
            target=self._authenticate,
            args=(
                identifier,
                password,
            ),
            daemon=True
        ).start()

    def _authenticate(
        self,
        identifier,
        password
    ):

        try:

            session = (
                self.app_state.api.sign_in(
                    identifier,
                    password
                )
            )

            if not session:

                raise RuntimeError(
                    "نشست ایجاد نشد."
                )

            if not self.app_state.set_session(
                session
            ):

                raise RuntimeError(
                    "ذخیره نشست انجام نشد."
                )

            Clock.schedule_once(
                lambda dt:
                self._login_success(),
                0
            )

        except Exception as exc:

            print(
                "LOGIN ERROR:",
                repr(exc)
            )

            message = str(
                exc
            ).strip()

            if not message:
                message = (
                    "ورود انجام نشد."
                )

            Clock.schedule_once(
                lambda dt, msg=message:
                self._login_failed(
                    msg
                ),
                0
            )

    def _login_success(self):

        self._busy = False
        self.login_button.disabled = False

        self._set_status(
            "ورود موفق بود.",
            SUCCESS
        )

        try:

            if self.manager:

                dashboard = (
                    self.manager.get_screen(
                        "dashboard"
                    )
                )

                if hasattr(
                    dashboard,
                    "refresh"
                ):
                    dashboard.refresh()

                self.manager.current = (
                    "dashboard"
                )

        except Exception as exc:

            print(
                "DASHBOARD ERROR:",
                repr(exc)
            )

            self._set_status(
                "ورود موفق شد اما داشبورد باز نشد.",
                ERROR
            )

    def _login_failed(
        self,
        message
    ):

        self._busy = False
        self.login_button.disabled = False

        self._set_status(
            message,
            ERROR
        )

    def on_pre_enter(self, *args):

        self._busy = False

        try:
            self.login_button.disabled = False
        except Exception:
            pass

        return super().on_pre_enter(
            *args
        )
            
