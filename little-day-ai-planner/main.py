import sys
from datetime import date, datetime, timedelta

import qtawesome as qta

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QFrame,
    QLineEdit,
    QDialog,
    QComboBox,
    QDateEdit,
    QTimeEdit,
    QMessageBox,
    QScrollArea,
    QSpinBox,
)

from database import (
    create_database,
    add_task,
    get_tasks,
    complete_task,
    add_goal,
    get_goals,
    add_habit,
    get_habits,
    toggle_habit,
    add_commitment,
    get_commitments,
    delete_commitment,
    delete_goal,
)

from planner import (
    decompose_goal,
    suggest_schedule,
)


# ============================================================
# COLORS
# ============================================================

BG = "#EAF3EE"
SIDEBAR = "#D5EAE3"
SURFACE = "#FFFDF7"
SURFACE_ALT = "#F8F1E6"

TEXT = "#39352F"
TEXT_SOFT = "#625D55"
MUTED = "#888177"

BORDER = "#DDD5C8"

MINT = "#D8EADF"
MINT_DARK = "#77A48D"

LAVENDER = "#E9DDF2"
LAVENDER_DARK = "#9279AA"

PEACH = "#F4D9CA"
PEACH_DARK = "#C98D73"

BLUE = "#DCEAF3"
BLUE_DARK = "#7198AA"

YELLOW = "#F2E5BC"
YELLOW_DARK = "#B79650"

DANGER = "#F0D2D2"
DANGER_DARK = "#B87474"

WHITE = "#FFFFFF"


# ============================================================
# GLOBAL HELPERS
# ============================================================

NAV_BUTTONS = []


def icon(name, color=TEXT):
    return qta.icon(name, color=color)


def icon_label(icon_name, color=TEXT, size=20):
    label = QLabel()
    label.setPixmap(
        icon(icon_name, color).pixmap(size, size)
    )
    label.setFixedSize(size, size)
    return label


def styled_button(
    text,
    icon_name=None,
    object_name="secondary",
    height=40,
):
    button = QPushButton(text)
    button.setObjectName(object_name)
    button.setCursor(Qt.PointingHandCursor)
    button.setFixedHeight(height)

    if icon_name:
        button.setIcon(icon(icon_name))
        button.setIconSize(QSize(16, 16))

    return button


def clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)

        if item.widget():
            item.widget().deleteLater()

        elif item.layout():
            clear_layout(item.layout())


# ============================================================
# MAIN WINDOW
# ============================================================

class LittleDay(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Little Day")
        self.resize(1180, 760)
        self.setMinimumSize(950, 650)

        self.current_page = None
        self.active_button = None

        self.setup_style()
        self.setup_ui()
        self.show_today()

    # ========================================================
    # STYLE
    # ========================================================

    def setup_style(self):

        self.setStyleSheet(
            f"""
            QWidget {{
                background: {BG};
                color: {TEXT};
                font-family: "Avenir Next";
                font-size: 14px;
            }}

            /* -----------------------------------------------
               SIDEBAR
            ------------------------------------------------ */

            QFrame#sidebar {{
                background: {SIDEBAR};
                border: none;
                border-right: 1px solid {BORDER};
            }}

            QLabel#logo {{
                background: transparent;
                color: {TEXT};
                font-size: 23px;
                font-weight: 800;
            }}

            QLabel#tagline {{
                background: transparent;
                color: {MUTED};
                font-size: 11px;
            }}

            QLabel#eyebrow {{
                background: transparent;
                color: {MUTED};
                font-size: 10px;
                font-weight: 800;
            }}

            /* -----------------------------------------------
               NAVIGATION
            ------------------------------------------------ */

            QPushButton#navButton {{
                background: transparent;
                color: {TEXT};
                border: none;
                border-radius: 12px;
                text-align: left;
                padding: 0 14px;
                font-size: 14px;
                font-weight: 600;
            }}

            QPushButton#navButton:hover {{
                background: rgba(255,255,255,0.42);
            }}

            QPushButton#navButton[active="true"] {{
                background: {SURFACE};
                color: {TEXT};
                font-weight: 750;
            }}

            /* -----------------------------------------------
               MAIN SURFACE
            ------------------------------------------------ */

            QFrame#mainSurface {{
                background: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 24px;
            }}

            QLabel#pageTitle {{
                background: transparent;
                color: {TEXT};
                font-size: 28px;
                font-weight: 800;
            }}

            QLabel#subtitle {{
                background: transparent;
                color: {MUTED};
                font-size: 13px;
            }}

            QLabel#sectionTitle {{
                background: transparent;
                color: {TEXT};
                font-size: 17px;
                font-weight: 800;
            }}

            QLabel#muted {{
                background: transparent;
                color: {MUTED};
            }}

            /* -----------------------------------------------
               BUTTONS
            ------------------------------------------------ */

            QPushButton {{
                border: none;
                border-radius: 10px;
                padding: 7px 14px;
                font-weight: 650;
            }}

            QPushButton#primary {{
                background: {TEXT};
                color: {WHITE};
            }}

            QPushButton#primary:hover {{
                background: #504A42;
            }}

            QPushButton#secondary {{
                background: {SURFACE_ALT};
                color: {TEXT};
                border: 1px solid {BORDER};
            }}

            QPushButton#secondary:hover {{
                background: {PEACH};
            }}

            QPushButton#smart {{
                background: {LAVENDER};
                color: {TEXT};
            }}

            QPushButton#smart:hover {{
                background: #DDCEE8;
            }}

            QPushButton#complete {{
                background: {MINT};
                color: {TEXT};
            }}

            QPushButton#complete:hover {{
                background: #C5DED0;
            }}

            QPushButton#danger {{
                background: {DANGER};
                color: {TEXT};
            }}

            QPushButton#danger:hover {{
                background: #E7BEBE;
            }}

            /* -----------------------------------------------
               INPUTS
            ------------------------------------------------ */

            QLineEdit,
            QComboBox,
            QDateEdit,
            QTimeEdit,
            QSpinBox {{
                background: {WHITE};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 9px;
                padding: 8px 10px;
                min-height: 18px;
            }}

            QLineEdit:focus,
            QComboBox:focus,
            QDateEdit:focus,
            QTimeEdit:focus,
            QSpinBox:focus {{
                border: 1px solid {MINT_DARK};
            }}

            /* -----------------------------------------------
               SCROLL
            ------------------------------------------------ */

            QScrollArea {{
                border: none;
                background: transparent;
            }}

            QScrollBar:vertical {{
                background: transparent;
                width: 7px;
            }}

            QScrollBar::handle:vertical {{
                background: #C9C1B5;
                border-radius: 3px;
                min-height: 30px;
            }}

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            """
        )

    # ========================================================
    # UI SETUP
    # ========================================================

    def setup_ui(self):

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ====================================================
        # SIDEBAR
        # ====================================================

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(
            18, 24, 18, 18
        )
        sidebar_layout.setSpacing(6)

        # Logo
        logo_row = QHBoxLayout()
        logo_row.setSpacing(9)

        logo_icon = icon_label(
            "fa5s.sun",
            PEACH_DARK,
            25
        )

        logo = QLabel("Little Day")
        logo.setObjectName("logo")

        logo_row.addWidget(logo_icon)
        logo_row.addWidget(logo)
        logo_row.addStretch()

        sidebar_layout.addLayout(logo_row)

        tagline = QLabel("make room for your life")
        tagline.setObjectName("tagline")
        tagline.setContentsMargins(34, 0, 0, 0)

        sidebar_layout.addWidget(tagline)

        sidebar_layout.addSpacing(28)

        # Navigation
        self.today_btn = self.nav_button(
            "Today",
            "fa5s.sun"
        )

        self.goals_btn = self.nav_button(
            "My Goals",
            "fa5s.bullseye"
        )

        self.calendar_btn = self.nav_button(
            "Calendar",
            "fa5s.calendar-alt"
        )

        self.habits_btn = self.nav_button(
            "Habits",
            "fa5s.leaf"
        )

        sidebar_layout.addWidget(self.today_btn)
        sidebar_layout.addWidget(self.goals_btn)
        sidebar_layout.addWidget(self.calendar_btn)
        sidebar_layout.addWidget(self.habits_btn)

        sidebar_layout.addSpacing(20)

        smart_label = QLabel("SMART")
        smart_label.setObjectName("eyebrow")
        smart_label.setContentsMargins(14, 0, 0, 3)

        sidebar_layout.addWidget(smart_label)

        self.smart_btn = self.nav_button(
            "Plan my day",
            "fa5s.magic"
        )

        sidebar_layout.addWidget(self.smart_btn)

        sidebar_layout.addStretch()

        self.settings_btn = self.nav_button(
            "Settings",
            "fa5s.cog"
        )

        sidebar_layout.addWidget(self.settings_btn)

        footer = QLabel("little steps · big days")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet(
            f"""
            background: transparent;
            color: {MUTED};
            font-size: 10px;
            padding-top: 12px;
            """
        )

        sidebar_layout.addWidget(footer)

        root.addWidget(sidebar)

        # ====================================================
        # MAIN AREA
        # ====================================================

        main_area = QWidget()

        main_layout = QVBoxLayout(main_area)
        main_layout.setContentsMargins(
            22, 18, 22, 18
        )

        self.main_surface = QFrame()
        self.main_surface.setObjectName("mainSurface")

        self.paper_layout = QVBoxLayout(
            self.main_surface
        )

        self.paper_layout.setContentsMargins(
            30, 26, 30, 26
        )

        self.paper_layout.setSpacing(18)

        main_layout.addWidget(self.main_surface)

        root.addWidget(main_area, 1)

        # Connections
        self.today_btn.clicked.connect(
            self.show_today
        )

        self.goals_btn.clicked.connect(
            self.show_goals
        )

        self.calendar_btn.clicked.connect(
            self.show_calendar
        )

        self.habits_btn.clicked.connect(
            self.show_habits
        )

        self.smart_btn.clicked.connect(
            self.show_smart_plan
        )

        self.settings_btn.clicked.connect(
            self.show_settings
        )

    # ========================================================
    # NAV BUTTON
    # ========================================================

    def nav_button(self, text, icon_name):

        button = QPushButton(text)

        button.setObjectName("navButton")
        button.setProperty("active", False)

        button.setIcon(icon(icon_name))
        button.setIconSize(QSize(17, 17))

        button.setFixedHeight(42)
        button.setCursor(Qt.PointingHandCursor)

        NAV_BUTTONS.append(button)

        return button

    def set_active(self, button):

        for nav in NAV_BUTTONS:

            nav.setProperty(
                "active",
                nav is button
            )

            nav.style().unpolish(nav)
            nav.style().polish(nav)

        self.active_button = button

    # ========================================================
    # PAGE HEADER
    # ========================================================

    def page_header(
        self,
        eyebrow,
        title,
        subtitle,
        icon_name=None
    ):

        row = QHBoxLayout()
        row.setSpacing(13)

        if icon_name:

            icon_frame = QFrame()

            icon_frame.setFixedSize(
                46,
                46
            )

            icon_frame.setStyleSheet(
                f"""
                background: {MINT};
                border-radius: 14px;
                """
            )

            icon_layout = QVBoxLayout(
                icon_frame
            )

            icon_layout.setContentsMargins(
                0, 0, 0, 0
            )

            icon_layout.addWidget(
                icon_label(
                    icon_name,
                    MINT_DARK,
                    21
                ),
                alignment=Qt.AlignCenter
            )

            row.addWidget(icon_frame)

        text_column = QVBoxLayout()
        text_column.setSpacing(2)

        eyebrow_label = QLabel(
            eyebrow.upper()
        )

        eyebrow_label.setObjectName(
            "eyebrow"
        )

        title_label = QLabel(title)
        title_label.setObjectName(
            "pageTitle"
        )

        subtitle_label = QLabel(
            subtitle
        )

        subtitle_label.setObjectName(
            "subtitle"
        )

        text_column.addWidget(
            eyebrow_label
        )

        text_column.addWidget(
            title_label
        )

        text_column.addWidget(
            subtitle_label
        )

        row.addLayout(
            text_column
        )

        row.addStretch()

        self.paper_layout.addLayout(
            row
        )

    # ========================================================
    # TODAY
    # ========================================================

    def show_today(self):

        self.set_active(
            self.today_btn
        )

        self.current_page = "today"

        clear_layout(
            self.paper_layout
        )

        today = date.today()

        tasks = get_tasks(
            today.isoformat()
        )

        self.page_header(
            "YOUR DAY",
            today.strftime(
                "%A, %d %B"
            ),
            "A little structure for everything you want to get done.",
            "fa5s.sun"
        )

        # ----------------------------------------------------
        # ACTIONS
        # ----------------------------------------------------

        actions = QHBoxLayout()
        actions.setSpacing(8)

        add_btn = styled_button(
            "Add task",
            "fa5s.plus",
            "primary",
            38
        )

        plan_btn = styled_button(
            "Plan my day",
            "fa5s.magic",
            "smart",
            38
        )

        add_btn.clicked.connect(
            self.add_task_popup
        )

        plan_btn.clicked.connect(
            self.show_smart_plan
        )

        actions.addWidget(add_btn)
        actions.addWidget(plan_btn)
        actions.addStretch()

        self.paper_layout.addLayout(
            actions
        )

        # ----------------------------------------------------
        # STATS
        # ----------------------------------------------------

        total = len(tasks)

        completed = sum(
            1
            for task in tasks
            if task[7]
        )

        remaining = max(
            0,
            total - completed
        )

        stats = QHBoxLayout()
        stats.setSpacing(10)

        stats.addWidget(
            self.stat_card(
                "TASKS",
                str(total),
                "fa5s.list",
                BLUE
            )
        )

        stats.addWidget(
            self.stat_card(
                "DONE",
                str(completed),
                "fa5s.check-circle",
                MINT
            )
        )

        stats.addWidget(
            self.stat_card(
                "LEFT",
                str(remaining),
                "fa5s.clock",
                LAVENDER
            )
        )

        self.paper_layout.addLayout(
            stats
        )

        # ----------------------------------------------------
        # SECTION HEADER
        # ----------------------------------------------------

        section_row = QHBoxLayout()

        section = QLabel(
            "Today's tasks"
        )

        section.setObjectName(
            "sectionTitle"
        )

        section_row.addWidget(section)

        section_row.addStretch()

        if tasks:

            count_label = QLabel(
                f"{total} task"
                + (
                    "s"
                    if total != 1
                    else ""
                )
            )

            count_label.setStyleSheet(
                f"""
                background: {SURFACE_ALT};
                color: {MUTED};
                border-radius: 8px;
                padding: 5px 9px;
                font-size: 11px;
                """
            )

            section_row.addWidget(
                count_label
            )

        self.paper_layout.addLayout(
            section_row
        )

        # ----------------------------------------------------
        # TASKS
        # ----------------------------------------------------

        if not tasks:

            self.paper_layout.addWidget(
                self.empty_state(
                    "fa5s.sun",
                    "Nothing planned yet",
                    "Add a task or let Little Day plan something for you."
                )
            )

            self.paper_layout.addStretch()

            return

        scroll = self.scroll_container()

        container = QWidget()

        layout = QVBoxLayout(
            container
        )

        layout.setContentsMargins(
            1, 1, 1, 1
        )

        layout.setSpacing(9)

        for task in tasks:

            layout.addWidget(
                self.task_card(task)
            )

        layout.addStretch()

        scroll.setWidget(
            container
        )

        self.paper_layout.addWidget(
            scroll,
            1
        )

    # ========================================================
    # STAT CARD
    # ========================================================

    def stat_card(
        self,
        title,
        value,
        icon_name,
        background
    ):

        frame = QFrame()

        frame.setFixedHeight(
            76
        )

        frame.setStyleSheet(
            f"""
            QFrame {{
                background: {background};
                border: 1px solid {BORDER};
                border-radius: 14px;
            }}
            """
        )

        layout = QHBoxLayout(frame)

        layout.setContentsMargins(
            13, 10, 15, 10
        )

        layout.setSpacing(11)

        icon_box = QFrame()

        icon_box.setFixedSize(
            34,
            34
        )

        icon_box.setStyleSheet(
            f"""
            background: rgba(255,255,255,0.58);
            border-radius: 10px;
            """
        )

        icon_layout = QVBoxLayout(
            icon_box
        )

        icon_layout.setContentsMargins(
            0, 0, 0, 0
        )

        icon_layout.addWidget(
            icon_label(
                icon_name,
                MINT_DARK,
                16
            ),
            alignment=Qt.AlignCenter
        )

        layout.addWidget(
            icon_box
        )

        text = QVBoxLayout()
        text.setSpacing(0)

        title_label = QLabel(
            title
        )

        title_label.setStyleSheet(
            f"""
            background: transparent;
            color: {MUTED};
            font-size: 9px;
            font-weight: 800;
            """
        )

        value_label = QLabel(
            value
        )

        value_label.setStyleSheet(
            f"""
            background: transparent;
            color: {TEXT};
            font-size: 21px;
            font-weight: 800;
            """
        )

        text.addWidget(
            title_label
        )

        text.addWidget(
            value_label
        )

        layout.addLayout(
            text
        )

        layout.addStretch()

        return frame

    # ========================================================
    # TASK CARD
    # ========================================================

    def task_card(self, task):

        (
            task_id,
            title,
            description,
            task_date,
            start_time,
            end_time,
            priority,
            completed,
            duration,
            goal_id
        ) = task

        background = (
            "#F0F1EB"
            if completed
            else SURFACE_ALT
        )

        frame = QFrame()

        frame.setStyleSheet(
            f"""
            QFrame {{
                background: {background};
                border: 1px solid {BORDER};
                border-radius: 14px;
            }}
            """
        )

        layout = QHBoxLayout(
            frame
        )

        layout.setContentsMargins(
            14, 11, 14, 11
        )

        layout.setSpacing(12)

        # Priority indicator
        priority_colors = {
            "High": "#D98C8C",
            "Medium": YELLOW_DARK,
            "Low": MINT_DARK,
        }

        accent = QFrame()

        accent.setFixedWidth(
            4
        )

        accent.setStyleSheet(
            f"""
            background: {
                priority_colors.get(
                    priority,
                    MINT_DARK
                )
            };
            border-radius: 2px;
            """
        )

        layout.addWidget(
            accent
        )

        content = QVBoxLayout()
        content.setSpacing(2)

        # Time
        if start_time and end_time:

            time_text = (
                f"{start_time} — {end_time}"
            )

        elif start_time:

            time_text = start_time

        else:

            time_text = "Unscheduled"

        time_label = QLabel(
            time_text
        )

        time_label.setStyleSheet(
            f"""
            background: transparent;
            color: {MUTED};
            font-size: 10px;
            font-weight: 700;
            """
        )

        # Title
        title_label = QLabel(
            title
        )

        if completed:

            title_label.setStyleSheet(
                f"""
                background: transparent;
                color: {MUTED};
                font-size: 15px;
                font-weight: 750;
                text-decoration: line-through;
                """
            )

        else:

            title_label.setStyleSheet(
                f"""
                background: transparent;
                color: {TEXT};
                font-size: 15px;
                font-weight: 750;
                """
            )

        content.addWidget(
            time_label
        )

        content.addWidget(
            title_label
        )

        if description:

            desc = QLabel(
                description
            )

            desc.setWordWrap(
                True
            )

            desc.setStyleSheet(
                f"""
                background: transparent;
                color: {MUTED};
                font-size: 11px;
                """
            )

            content.addWidget(
                desc
            )

        meta = QLabel(
            f"{priority} priority  ·  "
            f"{duration} min"
        )

        meta.setStyleSheet(
            f"""
            background: transparent;
            color: {MUTED};
            font-size: 10px;
            """
        )

        content.addWidget(
            meta
        )

        layout.addLayout(
            content,
            1
        )

        if not completed:

            complete_btn = styled_button(
                "",
                "fa5s.check",
                "complete",
                36
            )

            complete_btn.setFixedWidth(
                38
            )

            complete_btn.setToolTip(
                "Mark complete"
            )

            complete_btn.clicked.connect(
                lambda checked=False,
                tid=task_id:
                self.finish_task(tid)
            )

            layout.addWidget(
                complete_btn
            )

        return frame

    def finish_task(self, task_id):

        complete_task(
            task_id
        )

        self.show_today()

    # ========================================================
    # TASK DIALOG
    # ========================================================

    def task_dialog(self):

        dialog = QDialog(
            self
        )

        dialog.setWindowTitle(
            "Add task"
        )

        dialog.setMinimumWidth(
            430
        )

        layout = QVBoxLayout(
            dialog
        )

        layout.setContentsMargins(
            24, 22, 24, 22
        )

        layout.setSpacing(
            10
        )

        heading = QLabel(
            "New task"
        )

        heading.setStyleSheet(
            f"""
            background: transparent;
            color: {TEXT};
            font-size: 22px;
            font-weight: 800;
            """
        )

        layout.addWidget(
            heading
        )

        subtitle = QLabel(
            "Add something you want to make room for."
        )

        subtitle.setStyleSheet(
            f"""
            background: transparent;
            color: {MUTED};
            font-size: 12px;
            """
        )

        layout.addWidget(
            subtitle
        )

        layout.addSpacing(
            6
        )

        title_input = QLineEdit()
        title_input.setPlaceholderText(
            "What do you want to do?"
        )

        description_input = QLineEdit()
        description_input.setPlaceholderText(
            "Optional description"
        )

        date_input = QDateEdit()
        date_input.setCalendarPopup(
            True
        )
        date_input.setDate(
            datetime.today()
        )

        start_input = QTimeEdit()
        start_input.setDisplayFormat(
            "HH:mm"
        )

        end_input = QTimeEdit()
        end_input.setDisplayFormat(
            "HH:mm"
        )

        priority_input = QComboBox()
        priority_input.addItems([
            "High",
            "Medium",
            "Low"
        ])

        priority_input.setCurrentText(
            "Medium"
        )

        duration_input = QSpinBox()
        duration_input.setRange(
            15,
            480
        )

        duration_input.setSingleStep(
            15
        )

        duration_input.setValue(
            60
        )

        duration_input.setSuffix(
            " min"
        )

        fields = [
            ("Task", title_input),
            ("Description", description_input),
            ("Date", date_input),
            ("Start", start_input),
            ("End", end_input),
            ("Priority", priority_input),
            ("Duration", duration_input),
        ]

        for label_text, widget in fields:

            label = QLabel(
                label_text
            )

            label.setStyleSheet(
                f"""
                background: transparent;
                color: {MUTED};
                font-size: 10px;
                font-weight: 750;
                """
            )

            layout.addWidget(
                label
            )

            layout.addWidget(
                widget
            )

        buttons = QHBoxLayout()

        buttons.addStretch()

        cancel = styled_button(
            "Cancel",
            "fa5s.times",
            "secondary"
        )

        save = styled_button(
            "Add task",
            "fa5s.plus",
            "primary"
        )

        cancel.clicked.connect(
            dialog.reject
        )

        save.clicked.connect(
            dialog.accept
        )

        buttons.addWidget(
            cancel
        )

        buttons.addWidget(
            save
        )

        layout.addSpacing(
            8
        )

        layout.addLayout(
            buttons
        )

        if dialog.exec() != QDialog.Accepted:
            return None

        return (
            title_input.text().strip(),
            description_input.text().strip(),
            date_input.date().toString(
                "yyyy-MM-dd"
            ),
            start_input.time().toString(
                "HH:mm"
            ),
            end_input.time().toString(
                "HH:mm"
            ),
            priority_input.currentText(),
            duration_input.value(),
        )

    def add_task_popup(self):

        result = self.task_dialog()

        if not result:
            return

        (
            title,
            description,
            task_date,
            start_time,
            end_time,
            priority,
            duration,
        ) = result

        if not title:

            QMessageBox.warning(
                self,
                "Missing title",
                "Please give your task a title."
            )

            return

        add_task(
            title=title,
            description=description,
            task_date=task_date,
            start_time=start_time,
            end_time=end_time,
            priority=priority,
            duration_minutes=duration,
        )

        self.show_today()

    # ========================================================
    # GOALS
    # ========================================================

    def show_goals(self):

        self.set_active(
            self.goals_btn
        )

        self.current_page = "goals"

        clear_layout(
            self.paper_layout
        )

        self.page_header(
            "DIRECTION",
            "My Goals",
            "Turn the things you care about into small, doable steps.",
            "fa5s.bullseye"
        )

        actions = QHBoxLayout()

        add_btn = styled_button(
            "Add goal",
            "fa5s.plus",
            "primary",
            38
        )

        add_btn.clicked.connect(
            self.add_goal_popup
        )

        actions.addWidget(
            add_btn
        )

        actions.addStretch()

        self.paper_layout.addLayout(
            actions
        )

        goals = get_goals()

        if not goals:

            self.paper_layout.addWidget(
                self.empty_state(
                    "fa5s.bullseye",
                    "No goals yet",
                    "Add something you're working toward."
                )
            )

            self.paper_layout.addStretch()

            return

        scroll = self.scroll_container()

        container = QWidget()

        layout = QVBoxLayout(
            container
        )

        layout.setContentsMargins(
            1, 1, 1, 1
        )

        layout.setSpacing(
            10
        )

        for goal in goals:

            layout.addWidget(
                self.goal_card(goal)
            )

        layout.addStretch()

        scroll.setWidget(
            container
        )

        self.paper_layout.addWidget(
            scroll,
            1
        )

    def goal_card(self, goal):

        (
            goal_id,
            title,
            description,
            priority,
            deadline,
        ) = goal

        frame = QFrame()

        frame.setStyleSheet(
            f"""
            QFrame {{
                background: {LAVENDER};
                border: 1px solid {BORDER};
                border-radius: 15px;
            }}
            """
        )

        layout = QHBoxLayout(
            frame
        )

        layout.setContentsMargins(
            15, 13, 15, 13
        )

        layout.setSpacing(
            12
        )

        icon_box = QFrame()

        icon_box.setFixedSize(
            38,
            38
        )

        icon_box.setStyleSheet(
            f"""
            background: rgba(255,255,255,0.48);
            border-radius: 11px;
            """
        )

        icon_layout = QVBoxLayout(
            icon_box
        )

        icon_layout.setContentsMargins(
            0, 0, 0, 0
        )

        icon_layout.addWidget(
            icon_label(
                "fa5s.bullseye",
                LAVENDER_DARK,
                19
            ),
            alignment=Qt.AlignCenter
        )

        layout.addWidget(
            icon_box
        )

        content = QVBoxLayout()

        content.setSpacing(
            3
        )

        title_label = QLabel(
            title
        )

        title_label.setStyleSheet(
            f"""
            background: transparent;
            color: {TEXT};
            font-size: 16px;
            font-weight: 800;
            """
        )

        content.addWidget(
            title_label
        )

        if description:

            desc = QLabel(
                description
            )

            desc.setWordWrap(
                True
            )

            desc.setStyleSheet(
                f"""
                background: transparent;
                color: {MUTED};
                font-size: 11px;
                """
            )

            content.addWidget(
                desc
            )

        deadline_text = (
            f"Deadline: {deadline}"
            if deadline
            else "No deadline"
        )

        meta = QLabel(
            f"{priority} priority  ·  "
            f"{deadline_text}"
        )

        meta.setStyleSheet(
            f"""
            background: transparent;
            color: {MUTED};
            font-size: 10px;
            """
        )

        content.addWidget(
            meta
        )

        layout.addLayout(
            content,
            1
        )

        generate = styled_button(
            "Break down",
            "fa5s.magic",
            "secondary",
            36
        )

        generate.clicked.connect(
            lambda checked=False,
            gid=goal_id:
            self.generate_goal_tasks(gid)
        )

        delete = styled_button(
            "",
            "fa5s.trash-alt",
            "danger",
            36
        )

        delete.setFixedWidth(
            38
        )

        delete.setToolTip(
            "Delete goal"
        )

        delete.clicked.connect(
            lambda checked=False,
            gid=goal_id:
            self.delete_goal_popup(gid)
        )

        layout.addWidget(
            generate
        )

        layout.addWidget(
            delete
        )

        return frame

    def add_goal_popup(self):

        dialog = QDialog(
            self
        )

        dialog.setWindowTitle(
            "Add goal"
        )

        dialog.setMinimumWidth(
            430
        )

        layout = QVBoxLayout(
            dialog
        )

        layout.setContentsMargins(
            24, 22, 24, 22
        )

        layout.setSpacing(
            10
        )

        heading = QLabel(
            "New goal"
        )

        heading.setStyleSheet(
            f"""
            background: transparent;
            color: {TEXT};
            font-size: 22px;
            font-weight: 800;
            """
        )

        layout.addWidget(
            heading
        )

        title = QLineEdit()
        title.setPlaceholderText(
            "e.g. Learn transformers"
        )

        description = QLineEdit()
        description.setPlaceholderText(
            "What does success look like?"
        )

        priority = QComboBox()

        priority.addItems([
            "High",
            "Medium",
            "Low"
        ])

        deadline = QDateEdit()

        deadline.setCalendarPopup(
            True
        )

        deadline.setDate(
            date.today()
            + timedelta(days=14)
        )

        fields = [
            ("Goal", title),
            ("Description", description),
            ("Priority", priority),
            ("Deadline", deadline),
        ]

        for label_text, widget in fields:

            label = QLabel(
                label_text
            )

            label.setStyleSheet(
                f"""
                background: transparent;
                color: {MUTED};
                font-size: 10px;
                font-weight: 750;
                """
            )

            layout.addWidget(
                label
            )

            layout.addWidget(
                widget
            )

        buttons = QHBoxLayout()

        buttons.addStretch()

        cancel = styled_button(
            "Cancel",
            "fa5s.times",
            "secondary"
        )

        save = styled_button(
            "Add goal",
            "fa5s.plus",
            "primary"
        )

        cancel.clicked.connect(
            dialog.reject
        )

        save.clicked.connect(
            dialog.accept
        )

        buttons.addWidget(
            cancel
        )

        buttons.addWidget(
            save
        )

        layout.addSpacing(
            8
        )

        layout.addLayout(
            buttons
        )

        if dialog.exec() != QDialog.Accepted:
            return

        if not title.text().strip():

            QMessageBox.warning(
                self,
                "Missing goal",
                "Please give your goal a title."
            )

            return

        add_goal(
            title.text().strip(),
            description.text().strip(),
            priority.currentText(),
            deadline.date().toString(
                "yyyy-MM-dd"
            )
        )

        self.show_goals()

    def generate_goal_tasks(self, goal_id):

        goals = get_goals()

        goal = next(
            (
                g
                for g in goals
                if g[0] == goal_id
            ),
            None
        )

        if not goal:
            return

        (
            _,
            title,
            description,
            priority,
            deadline,
        ) = goal

        try:

            QApplication.setOverrideCursor(
                Qt.WaitCursor
            )

            tasks = decompose_goal(
                f"{title}. {description}"
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "AI planner",
                str(error)
            )

            return

        finally:

            QApplication.restoreOverrideCursor()

        start_date = date.today()

        try:

            deadline_date = datetime.strptime(
                deadline,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            deadline_date = (
                start_date
                + timedelta(days=14)
            )

        commitments = get_commitments()

        busy_by_date = {}

        for commitment in commitments:

            (
                commitment_id,
                commitment_title,
                commitment_date,
                start_time,
                end_time,
            ) = commitment

            if (
                not start_time
                or not end_time
            ):
                continue

            busy_by_date.setdefault(
                commitment_date,
                []
            ).append({
                "start_time": start_time,
                "end_time": end_time,
            })

        scheduled = suggest_schedule(
            tasks,
            start_date,
            deadline_date,
            busy_by_date=busy_by_date,
        )

        for task in scheduled:

            add_task(
                title=task["title"],
                description=(
                    f"Generated from goal: {title}"
                ),
                task_date=task["date"],
                start_time=task["start"],
                end_time=task["end"],
                priority=task.get(
                    "priority",
                    "Medium"
                ),
                duration_minutes=task.get(
                    "duration_minutes",
                    60
                ),
                goal_id=goal_id,
            )

        QMessageBox.information(
            self,
            "Plan created",
            f"Little Day created "
            f"{len(scheduled)} tasks for this goal."
        )

        self.show_goals()

    def delete_goal_popup(self, goal_id):

        answer = QMessageBox.question(
            self,
            "Delete goal",
            "Delete this goal and its generated tasks?",
            QMessageBox.Yes
            | QMessageBox.No,
        )

        if answer == QMessageBox.Yes:

            delete_goal(
                goal_id
            )

            self.show_goals()

    # ========================================================
    # CALENDAR
    # ========================================================

    def show_calendar(self):

        self.set_active(
            self.calendar_btn
        )

        self.current_page = "calendar"

        clear_layout(
            self.paper_layout
        )

        self.page_header(
            "OVERVIEW",
            "Calendar",
            "A simple look at the week ahead.",
            "fa5s.calendar-alt"
        )

        start = date.today()

        scroll = self.scroll_container()

        container = QWidget()

        layout = QVBoxLayout(
            container
        )

        layout.setContentsMargins(
            1, 1, 1, 1
        )

        layout.setSpacing(
            9
        )

        for offset in range(7):

            current = (
                start
                + timedelta(days=offset)
            )

            tasks = get_tasks(
                current.isoformat()
            )

            day_card = QFrame()

            day_card.setStyleSheet(
                f"""
                QFrame {{
                    background: {SURFACE_ALT};
                    border: 1px solid {BORDER};
                    border-radius: 14px;
                }}
                """
            )

            day_layout = QVBoxLayout(
                day_card
            )

            day_layout.setContentsMargins(
                15, 11, 15, 11
            )

            day_layout.setSpacing(
                5
            )

            heading = QLabel(
                current.strftime(
                    "%A · %d %B"
                )
            )

            heading.setStyleSheet(
                f"""
                background: transparent;
                color: {TEXT};
                font-size: 14px;
                font-weight: 800;
                """
            )

            day_layout.addWidget(
                heading
            )

            if not tasks:

                empty = QLabel(
                    "Nothing scheduled"
                )

                empty.setStyleSheet(
                    f"""
                    background: transparent;
                    color: {MUTED};
                    font-size: 11px;
                    """
                )

                day_layout.addWidget(
                    empty
                )

            else:

                for task in tasks:

                    (
                        task_id,
                        title,
                        description,
                        task_date,
                        start_time,
                        end_time,
                        priority,
                        completed,
                        duration,
                        goal_id,
                    ) = task

                    time_text = (
                        start_time
                        if start_time
                        else "—"
                    )

                    task_label = QLabel(
                        f"{time_text}   {title}"
                    )

                    task_label.setStyleSheet(
                        f"""
                        background: transparent;
                        color: {
                            MUTED
                            if completed
                            else TEXT
                        };
                        font-size: 11px;
                        """
                    )

                    day_layout.addWidget(
                        task_label
                    )

            layout.addWidget(
                day_card
            )

        layout.addStretch()

        scroll.setWidget(
            container
        )

        self.paper_layout.addWidget(
            scroll,
            1
        )

    # ========================================================
    # HABITS
    # ========================================================

    def show_habits(self):

        self.set_active(
            self.habits_btn
        )

        self.current_page = "habits"

        clear_layout(
            self.paper_layout
        )

        self.page_header(
            "ROUTINES",
            "Habits",
            "Small things, repeated often.",
            "fa5s.leaf"
        )

        actions = QHBoxLayout()

        add_btn = styled_button(
            "Add habit",
            "fa5s.plus",
            "primary",
            38
        )

        add_btn.clicked.connect(
            self.add_habit_popup
        )

        actions.addWidget(
            add_btn
        )

        actions.addStretch()

        self.paper_layout.addLayout(
            actions
        )

        habits = get_habits()

        if not habits:

            self.paper_layout.addWidget(
                self.empty_state(
                    "fa5s.leaf",
                    "No habits yet",
                    "Start with one small thing you'd like to repeat."
                )
            )

            self.paper_layout.addStretch()

            return

        scroll = self.scroll_container()

        container = QWidget()

        layout = QVBoxLayout(
            container
        )

        layout.setContentsMargins(
            1, 1, 1, 1
        )

        layout.setSpacing(
            9
        )

        today = date.today().isoformat()

        for habit in habits:

            (
                habit_id,
                title,
                frequency,
                last_completed,
            ) = habit

            card = QFrame()

            card.setStyleSheet(
                f"""
                QFrame {{
                    background: {MINT};
                    border: 1px solid {BORDER};
                    border-radius: 14px;
                }}
                """
            )

            row = QHBoxLayout(
                card
            )

            row.setContentsMargins(
                14, 11, 14, 11
            )

            row.setSpacing(
                11
            )

            icon_box = QFrame()

            icon_box.setFixedSize(
                36,
                36
            )

            icon_box.setStyleSheet(
                """
                background: rgba(
                    255,255,255,0.45
                );
                border-radius: 10px;
                """
            )

            icon_layout = QVBoxLayout(
                icon_box
            )

            icon_layout.setContentsMargins(
                0, 0, 0, 0
            )

            icon_layout.addWidget(
                icon_label(
                    "fa5s.leaf",
                    MINT_DARK,
                    17
                ),
                alignment=Qt.AlignCenter
            )

            row.addWidget(
                icon_box
            )

            content = QVBoxLayout()

            content.setSpacing(
                2
            )

            title_label = QLabel(
                title
            )

            title_label.setStyleSheet(
                f"""
                background: transparent;
                color: {TEXT};
                font-size: 14px;
                font-weight: 800;
                """
            )

            frequency_label = QLabel(
                f"{frequency} · "
                + (
                    "completed today"
                    if last_completed == today
                    else "not completed today"
                )
            )

            frequency_label.setStyleSheet(
                f"""
                background: transparent;
                color: {MUTED};
                font-size: 10px;
                """
            )

            content.addWidget(
                title_label
            )

            content.addWidget(
                frequency_label
            )

            row.addLayout(
                content,
                1
            )

            done = (
                last_completed == today
            )

            button = styled_button(
                "Done"
                if done
                else "Complete",
                "fa5s.check",
                "secondary",
                35
            )

            button.clicked.connect(
                lambda checked=False,
                hid=habit_id:
                self.complete_habit(hid)
            )

            row.addWidget(
                button
            )

            layout.addWidget(
                card
            )

        layout.addStretch()

        scroll.setWidget(
            container
        )

        self.paper_layout.addWidget(
            scroll,
            1
        )

    def add_habit_popup(self):

        dialog = QDialog(
            self
        )

        dialog.setWindowTitle(
            "Add habit"
        )

        dialog.setMinimumWidth(
            400
        )

        layout = QVBoxLayout(
            dialog
        )

        layout.setContentsMargins(
            24, 22, 24, 22
        )

        layout.setSpacing(
            10
        )

        heading = QLabel(
            "New habit"
        )

        heading.setStyleSheet(
            f"""
            background: transparent;
            color: {TEXT};
            font-size: 22px;
            font-weight: 800;
            """
        )

        layout.addWidget(
            heading
        )

        title = QLineEdit()

        title.setPlaceholderText(
            "e.g. Read for 20 minutes"
        )

        frequency = QComboBox()

        frequency.addItems([
            "Daily",
            "Weekdays",
            "Weekly",
        ])

        for label_text, widget in [
            ("Habit", title),
            ("Frequency", frequency),
        ]:

            label = QLabel(
                label_text
            )

            label.setStyleSheet(
                f"""
                background: transparent;
                color: {MUTED};
                font-size: 10px;
                font-weight: 750;
                """
            )

            layout.addWidget(
                label
            )

            layout.addWidget(
                widget
            )

        buttons = QHBoxLayout()

        buttons.addStretch()

        cancel = styled_button(
            "Cancel",
            "fa5s.times",
            "secondary"
        )

        save = styled_button(
            "Add habit",
            "fa5s.plus",
            "primary"
        )

        cancel.clicked.connect(
            dialog.reject
        )

        save.clicked.connect(
            dialog.accept
        )

        buttons.addWidget(
            cancel
        )

        buttons.addWidget(
            save
        )

        layout.addSpacing(
            8
        )

        layout.addLayout(
            buttons
        )

        if dialog.exec() != QDialog.Accepted:
            return

        if not title.text().strip():
            return

        add_habit(
            title.text().strip(),
            frequency.currentText()
        )

        self.show_habits()

    def complete_habit(
        self,
        habit_id
    ):

        toggle_habit(
            habit_id
        )

        self.show_habits()

    # ========================================================
    # SMART PLANNER
    # ========================================================

    def show_smart_plan(self):

        self.set_active(
            self.smart_btn
        )

        self.current_page = "smart"

        clear_layout(
            self.paper_layout
        )

        self.page_header(
            "LITTLE DAY AI",
            "Plan my day",
            "Tell Little Day what matters and we'll turn it into real steps.",
            "fa5s.magic"
        )

        card = QFrame()

        card.setStyleSheet(
            f"""
            QFrame {{
                background: {LAVENDER};
                border: 1px solid {BORDER};
                border-radius: 17px;
            }}
            """
        )

        layout = QVBoxLayout(
            card
        )

        layout.setContentsMargins(
            20, 18, 20, 18
        )

        layout.setSpacing(
            10
        )

        label = QLabel(
            "What are you trying to accomplish?"
        )

        label.setStyleSheet(
            f"""
            background: transparent;
            color: {TEXT};
            font-size: 15px;
            font-weight: 800;
            """
        )

        layout.addWidget(
            label
        )

        self.smart_goal_input = QLineEdit()

        self.smart_goal_input.setPlaceholderText(
            "e.g. Learn the Transformer architecture"
        )

        layout.addWidget(
            self.smart_goal_input
        )

        deadline_label = QLabel(
            "Deadline"
        )

        deadline_label.setStyleSheet(
            f"""
            background: transparent;
            color: {MUTED};
            font-size: 10px;
            font-weight: 750;
            """
        )

        layout.addWidget(
            deadline_label
        )

        self.smart_deadline = QDateEdit()

        self.smart_deadline.setCalendarPopup(
            True
        )

        self.smart_deadline.setDate(
            date.today()
            + timedelta(days=7)
        )

        layout.addWidget(
            self.smart_deadline
        )

        generate = styled_button(
            "Create my plan",
            "fa5s.magic",
            "primary",
            40
        )

        generate.clicked.connect(
            self.generate_schedule_for_today
        )

        layout.addWidget(
            generate
        )

        self.paper_layout.addWidget(
            card
        )

        explanation = QLabel(
            "Little Day uses AI to break your goal into manageable steps, "
            "then places those steps into the time you actually have."
        )

        explanation.setWordWrap(
            True
        )

        explanation.setStyleSheet(
            f"""
            background: transparent;
            color: {MUTED};
            font-size: 12px;
            """
        )

        self.paper_layout.addWidget(
            explanation
        )

        self.paper_layout.addStretch()

    def generate_schedule_for_today(
        self
    ):

        goal = (
            self.smart_goal_input
            .text()
            .strip()
        )

        if not goal:

            QMessageBox.warning(
                self,
                "Missing goal",
                "Tell Little Day what you want to accomplish."
            )

            return

        try:

            QApplication.setOverrideCursor(
                Qt.WaitCursor
            )

            tasks = decompose_goal(
                goal
            )

            deadline = (
                self.smart_deadline
                .date()
                .toString(
                    "yyyy-MM-dd"
                )
            )

            deadline_date = datetime.strptime(
                deadline,
                "%Y-%m-%d"
            ).date()

            commitments = (
                get_commitments()
            )

            busy_by_date = {}

            for commitment in commitments:

                (
                    commitment_id,
                    title,
                    commitment_date,
                    start_time,
                    end_time,
                ) = commitment

                if (
                    not start_time
                    or not end_time
                ):
                    continue

                busy_by_date.setdefault(
                    commitment_date,
                    []
                ).append({
                    "start_time": start_time,
                    "end_time": end_time,
                })

            scheduled = suggest_schedule(
                tasks,
                date.today(),
                deadline_date,
                busy_by_date=busy_by_date,
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Planner error",
                str(error)
            )

            return

        finally:

            QApplication.restoreOverrideCursor()

        for task in scheduled:

            add_task(
                title=task["title"],
                description=(
                    f"Generated from goal: {goal}"
                ),
                task_date=task["date"],
                start_time=task["start"],
                end_time=task["end"],
                priority=task.get(
                    "priority",
                    "Medium"
                ),
                duration_minutes=task.get(
                    "duration_minutes",
                    60
                ),
            )

        if scheduled:

            QMessageBox.information(
                self,
                "Plan created",
                f"Little Day created "
                f"{len(scheduled)} tasks around your existing commitments."
            )

        else:

            QMessageBox.warning(
                self,
                "No available time",
                "Little Day couldn't find enough free time before your deadline."
            )

        self.show_today()

    # ========================================================
    # SETTINGS
    # ========================================================

    def show_settings(self):

        self.set_active(
            self.settings_btn
        )

        self.current_page = "settings"

        clear_layout(
            self.paper_layout
        )

        self.page_header(
            "YOUR LIFE",
            "Settings",
            "Tell Little Day about the things that already have a place.",
            "fa5s.cog"
        )

        section = QLabel(
            "Fixed commitments"
        )

        section.setObjectName(
            "sectionTitle"
        )

        self.paper_layout.addWidget(
            section
        )

        subtitle = QLabel(
            "Classes, appointments, family plans, or anything Little Day should never schedule over."
        )

        subtitle.setStyleSheet(
            f"""
            background: transparent;
            color: {MUTED};
            font-size: 11px;
            """
        )

        self.paper_layout.addWidget(
            subtitle
        )

        add_btn = styled_button(
            "Add commitment",
            "fa5s.plus",
            "primary",
            38
        )

        add_btn.clicked.connect(
            self.add_commitment_popup
        )

        self.paper_layout.addWidget(
            add_btn
        )

        commitments = get_commitments()

        if not commitments:

            self.paper_layout.addWidget(
                self.empty_state(
                    "fa5s.calendar-check",
                    "No commitments",
                    "Your schedule is wide open. Add anything fixed here."
                )
            )

            self.paper_layout.addStretch()

            return

        scroll = self.scroll_container()

        container = QWidget()

        layout = QVBoxLayout(
            container
        )

        layout.setContentsMargins(
            1, 1, 1, 1
        )

        layout.setSpacing(
            9
        )

        for commitment in commitments:

            (
                commitment_id,
                title,
                commitment_date,
                start_time,
                end_time,
            ) = commitment

            card = QFrame()

            card.setStyleSheet(
                f"""
                QFrame {{
                    background: {PEACH};
                    border: 1px solid {BORDER};
                    border-radius: 14px;
                }}
                """
            )

            row = QHBoxLayout(
                card
            )

            row.setContentsMargins(
                14, 11, 14, 11
            )

            row.setSpacing(
                11
            )

            icon_box = QFrame()

            icon_box.setFixedSize(
                36,
                36
            )

            icon_box.setStyleSheet(
                """
                background: rgba(
                    255,255,255,0.45
                );
                border-radius: 10px;
                """
            )

            icon_layout = QVBoxLayout(
                icon_box
            )

            icon_layout.setContentsMargins(
                0, 0, 0, 0
            )

            icon_layout.addWidget(
                icon_label(
                    "fa5s.thumbtack",
                    PEACH_DARK,
                    16
                ),
                alignment=Qt.AlignCenter
            )

            row.addWidget(
                icon_box
            )

            content = QVBoxLayout()

            content.setSpacing(
                2
            )

            title_label = QLabel(
                title
            )

            title_label.setStyleSheet(
                f"""
                background: transparent;
                color: {TEXT};
                font-size: 14px;
                font-weight: 800;
                """
            )

            meta = QLabel(
                f"{commitment_date} · "
                f"{start_time} — {end_time}"
            )

            meta.setStyleSheet(
                f"""
                background: transparent;
                color: {MUTED};
                font-size: 10px;
                """
            )

            content.addWidget(
                title_label
            )

            content.addWidget(
                meta
            )

            row.addLayout(
                content,
                1
            )

            delete = styled_button(
                "",
                "fa5s.trash-alt",
                "danger",
                36
            )

            delete.setFixedWidth(
                38
            )

            delete.clicked.connect(
                lambda checked=False,
                cid=commitment_id:
                self.delete_commitment_popup(cid)
            )

            row.addWidget(
                delete
            )

            layout.addWidget(
                card
            )

        layout.addStretch()

        scroll.setWidget(
            container
        )

        self.paper_layout.addWidget(
            scroll,
            1
        )

    def add_commitment_popup(self):

        dialog = QDialog(
            self
        )

        dialog.setWindowTitle(
            "Add commitment"
        )

        dialog.setMinimumWidth(
            420
        )

        layout = QVBoxLayout(
            dialog
        )

        layout.setContentsMargins(
            24, 22, 24, 22
        )

        layout.setSpacing(
            10
        )

        heading = QLabel(
            "New commitment"
        )

        heading.setStyleSheet(
            f"""
            background: transparent;
            color: {TEXT};
            font-size: 22px;
            font-weight: 800;
            """
        )

        layout.addWidget(
            heading
        )

        title = QLineEdit()

        title.setPlaceholderText(
            "e.g. Database Systems lecture"
        )

        commitment_date = QDateEdit()

        commitment_date.setCalendarPopup(
            True
        )

        commitment_date.setDate(
            date.today()
        )

        start = QTimeEdit()

        start.setDisplayFormat(
            "HH:mm"
        )

        end = QTimeEdit()

        end.setDisplayFormat(
            "HH:mm"
        )

        fields = [
            ("Title", title),
            ("Date", commitment_date),
            ("Starts", start),
            ("Ends", end),
        ]

        for label_text, widget in fields:

            label = QLabel(
                label_text
            )

            label.setStyleSheet(
                f"""
                background: transparent;
                color: {MUTED};
                font-size: 10px;
                font-weight: 750;
                """
            )

            layout.addWidget(
                label
            )

            layout.addWidget(
                widget
            )

        buttons = QHBoxLayout()

        buttons.addStretch()

        cancel = styled_button(
            "Cancel",
            "fa5s.times",
            "secondary"
        )

        save = styled_button(
            "Add commitment",
            "fa5s.plus",
            "primary"
        )

        cancel.clicked.connect(
            dialog.reject
        )

        save.clicked.connect(
            dialog.accept
        )

        buttons.addWidget(
            cancel
        )

        buttons.addWidget(
            save
        )

        layout.addSpacing(
            8
        )

        layout.addLayout(
            buttons
        )

        if dialog.exec() != QDialog.Accepted:
            return

        if not title.text().strip():
            return

        add_commitment(
            title.text().strip(),
            commitment_date.date().toString(
                "yyyy-MM-dd"
            ),
            start.time().toString(
                "HH:mm"
            ),
            end.time().toString(
                "HH:mm"
            )
        )

        self.show_settings()

    def delete_commitment_popup(
        self,
        commitment_id
    ):

        answer = QMessageBox.question(
            self,
            "Delete commitment",
            "Remove this commitment?",
            QMessageBox.Yes
            | QMessageBox.No,
        )

        if answer == QMessageBox.Yes:

            delete_commitment(
                commitment_id
            )

            self.show_settings()

    # ========================================================
    # SHARED UI
    # ========================================================

    def scroll_container(self):

        scroll = QScrollArea()

        scroll.setWidgetResizable(
            True
        )

        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        scroll.setFrameShape(
            QFrame.NoFrame
        )

        return scroll

    def empty_state(
        self,
        icon_name,
        title,
        subtitle
    ):

        frame = QFrame()

        frame.setMinimumHeight(
            170
        )

        frame.setStyleSheet(
            f"""
            QFrame {{
                background: {SURFACE_ALT};
                border: 1px dashed {BORDER};
                border-radius: 16px;
            }}
            """
        )

        layout = QVBoxLayout(
            frame
        )

        layout.setContentsMargins(
            25, 25, 25, 25
        )

        layout.setSpacing(
            7
        )

        icon_box = QFrame()

        icon_box.setFixedSize(
            44,
            44
        )

        icon_box.setStyleSheet(
            f"""
            background: {MINT};
            border-radius: 13px;
            """
        )

        icon_layout = QVBoxLayout(
            icon_box
        )

        icon_layout.setContentsMargins(
            0, 0, 0, 0
        )

        icon_layout.addWidget(
            icon_label(
                icon_name,
                MINT_DARK,
                21
            ),
            alignment=Qt.AlignCenter
        )

        layout.addWidget(
            icon_box,
            alignment=Qt.AlignCenter
        )

        title_label = QLabel(
            title
        )

        title_label.setAlignment(
            Qt.AlignCenter
        )

        title_label.setStyleSheet(
            f"""
            background: transparent;
            color: {TEXT};
            font-size: 16px;
            font-weight: 800;
            """
        )

        layout.addWidget(
            title_label
        )

        subtitle_label = QLabel(
            subtitle
        )

        subtitle_label.setAlignment(
            Qt.AlignCenter
        )

        subtitle_label.setWordWrap(
            True
        )

        subtitle_label.setStyleSheet(
            f"""
            background: transparent;
            color: {MUTED};
            font-size: 11px;
            """
        )

        layout.addWidget(
            subtitle_label
        )

        return frame


# ============================================================
# APP START
# ============================================================

if __name__ == "__main__":

    create_database()

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "Little Day"
    )

    window = LittleDay()

    window.show()

    sys.exit(
        app.exec()
    )