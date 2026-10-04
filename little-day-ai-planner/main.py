import sys
from datetime import date, datetime, timedelta

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QPushButton,
    QFrame,
    QLineEdit,
    QDialog,
    QComboBox,
    QDateEdit,
    QTimeEdit,
    QMessageBox,
    QScrollArea
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
    update_task_schedule
)

from planner import (
    decompose_goal,
    suggest_schedule
)


# =========================================================
# DATABASE
# =========================================================

create_database()


# =========================================================
# APP
# =========================================================

app = QApplication(sys.argv)

app.setStyleSheet("""
QWidget {
    background-color: #E5F3E8;
    color: #38382F;
    font-family: "Trebuchet MS";
    font-size: 14px;
}

QFrame#sidebar {
    background-color: #C6E7E5;
    border: 2px solid #38382F;
    border-radius: 14px;
}

QFrame#paper {
    background-color: #FFF9EB;
    border: 2px solid #38382F;
    border-radius: 14px;
}

QLabel#title {
    font-size: 27px;
    font-weight: bold;
}

QLabel#muted {
    color: #777366;
}

QPushButton {
    background-color: #FFF9EB;
    border: 2px solid #38382F;
    border-radius: 8px;
    padding: 9px;
    text-align: left;
}

QPushButton:hover {
    background-color: #F7D9B8;
}

QPushButton#primary {
    background-color: #D8E8D8;
    font-weight: bold;
}

QPushButton#smart {
    background-color: #E8D8F8;
    font-weight: bold;
}

QPushButton#danger {
    background-color: #F5D6D6;
}

QFrame#card {
    background-color: #D8E8F8;
    border: 2px solid #38382F;
    border-radius: 10px;
}

QFrame#cardAlt {
    background-color: #F7D9B8;
    border: 2px solid #38382F;
    border-radius: 10px;
}

QLineEdit,
QComboBox,
QDateEdit,
QTimeEdit {
    background-color: #FFF9EB;
    border: 2px solid #38382F;
    border-radius: 8px;
    padding: 7px;
}

QScrollArea {
    border: none;
    background: transparent;
}

* {
    selection-background-color: #F7D9B8;
    selection-color: #38382F;
}
""")


window = QWidget()
window.setWindowTitle("Little Day — AI Planner")
window.resize(1100, 720)

main = QHBoxLayout(window)
main.setContentsMargins(16, 16, 16, 16)
main.setSpacing(14)


# =========================================================
# SIDEBAR
# =========================================================

sidebar = QFrame()
sidebar.setObjectName("sidebar")
sidebar.setFixedWidth(220)

nav = QVBoxLayout(sidebar)
nav.setContentsMargins(14, 20, 14, 14)
nav.setSpacing(10)

logo = QLabel("🌱 Little Day")
logo.setStyleSheet(
    "font-size: 23px; font-weight: bold;"
)

nav.addWidget(logo)
nav.addWidget(QLabel("YOUR LITTLE WORLD"))

today_button = QPushButton("☀️   Today")
goals_button = QPushButton("🌷   My Goals")
calendar_button = QPushButton("🗓️   Calendar")
habits_button = QPushButton("🌿   Habits")
smart_button = QPushButton("🧠   Plan my day")

nav.addWidget(today_button)
nav.addWidget(goals_button)
nav.addWidget(calendar_button)
nav.addWidget(habits_button)
nav.addWidget(smart_button)

nav.addStretch()

settings_button = QPushButton("⚙️   Settings")
nav.addWidget(settings_button)


# =========================================================
# MAIN PAPER
# =========================================================

paper = QFrame()
paper.setObjectName("paper")

content = QVBoxLayout(paper)
content.setContentsMargins(28, 25, 28, 25)
content.setSpacing(12)


def clear_content():
    while content.count():
        item = content.takeAt(0)

        widget = item.widget()

        if widget:
            widget.deleteLater()


def scroll_wrap(widget):
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setWidget(widget)
    return scroll


# =========================================================
# TASK CARD
# =========================================================

def task_card(task, index=0):
    (
        task_id,
        title,
        description,
        task_date,
        start_time,
        end_time,
        priority,
        completed,
        duration_minutes,
        goal_id
    ) = task

    card = QFrame()

    card.setObjectName(
        "cardAlt" if index % 2 else "card"
    )

    row = QHBoxLayout(card)

    when = start_time or "Anytime"

    if end_time:
        when += f"–{end_time}"

    time_label = QLabel(when)
    time_label.setFixedWidth(105)

    row.addWidget(time_label)

    details = QVBoxLayout()

    title_label = QLabel(title)

    title_label.setStyleSheet(
        "font-weight: bold; font-size: 16px;"
    )

    details.addWidget(title_label)

    if description:
        description_label = QLabel(description)
        description_label.setWordWrap(True)
        details.addWidget(description_label)

    duration_text = (
        f"{duration_minutes or 60} min"
    )

    meta = QLabel(
        f"{task_date}  •  "
        f"{priority}  •  "
        f"{duration_text}"
    )

    meta.setObjectName("muted")

    details.addWidget(meta)

    row.addLayout(details, 1)

    done = QPushButton("✓")
    done.setFixedSize(38, 38)

    if completed:

        title_label.setStyleSheet(
            "font-weight: bold; "
            "font-size: 16px; "
            "text-decoration: line-through; "
            "color: #888;"
        )

        done.setEnabled(False)

    else:

        def finish():
            complete_task(task_id)
            show_today()

        done.clicked.connect(finish)

    row.addWidget(done)

    return card


# =========================================================
# ADD TASK
# =========================================================

def task_dialog(parent=window, initial_date=None):

    dialog = QDialog(parent)

    dialog.setWindowTitle("Add a task")
    dialog.resize(430, 360)

    layout = QVBoxLayout(dialog)

    title = QLineEdit()
    title.setPlaceholderText(
        "e.g. Read Transformer paper"
    )

    layout.addWidget(QLabel("Task"))
    layout.addWidget(title)

    description = QLineEdit()
    description.setPlaceholderText(
        "Optional notes"
    )

    layout.addWidget(QLabel("Notes"))
    layout.addWidget(description)

    task_date = QDateEdit()
    task_date.setCalendarPopup(True)

    task_date.setDate(
        initial_date or date.today()
    )

    layout.addWidget(QLabel("Date"))
    layout.addWidget(task_date)

    start = QTimeEdit()
    start.setDisplayFormat("HH:mm")

    layout.addWidget(QLabel("Start time"))
    layout.addWidget(start)

    end = QTimeEdit()
    end.setDisplayFormat("HH:mm")

    layout.addWidget(QLabel("End time"))
    layout.addWidget(end)

    priority = QComboBox()
    priority.addItems([
        "High",
        "Medium",
        "Low"
    ])

    layout.addWidget(QLabel("Priority"))
    layout.addWidget(priority)

    save = QPushButton("🌱 Add task")
    save.setObjectName("primary")

    layout.addWidget(save)

    save.clicked.connect(dialog.accept)

    if dialog.exec() and title.text().strip():

        start_time = start.time().toString("HH:mm")
        end_time = end.time().toString("HH:mm")

        # Calculate duration if possible.
        start_minutes = (
            start.time().hour() * 60
            + start.time().minute()
        )

        end_minutes = (
            end.time().hour() * 60
            + end.time().minute()
        )

        duration = end_minutes - start_minutes

        if duration <= 0:
            duration = 60

        return (
            title.text().strip(),
            description.text().strip(),
            task_date.date().toString(
                "yyyy-MM-dd"
            ),
            start_time,
            end_time,
            priority.currentText(),
            duration
        )

    return None


def add_task_popup():

    data = task_dialog()

    if data:

        add_task(*data)

        show_today()


# =========================================================
# TODAY
# =========================================================

def show_today():

    clear_content()

    heading = QLabel(
        "Your little day ✨"
    )

    heading.setObjectName("title")

    content.addWidget(heading)

    content.addWidget(
        QLabel(
            f"{date.today().strftime('%A, %d %B')}  "
            "• Small steps still count."
        )
    )

    add = QPushButton("＋ Add task")
    add.setObjectName("primary")

    add.clicked.connect(add_task_popup)

    content.addWidget(add)

    tasks = get_tasks(
        date.today().isoformat()
    )

    section = QLabel(
        "TODAY'S ADVENTURES"
    )

    section.setStyleSheet(
        "font-weight: bold;"
    )

    content.addWidget(section)

    if not tasks:

        empty = QLabel(
            "🌱 Nothing planned yet.\n"
            "Add a task or let the planner help."
        )

        empty.setStyleSheet(
            "font-size: 15px; padding: 18px;"
        )

        content.addWidget(empty)

    else:

        for i, task in enumerate(tasks):
            content.addWidget(
                task_card(task, i)
            )

    content.addStretch()

    footer = QLabel(
        "🌱 Your plans can change. That's okay."
    )

    footer.setObjectName("muted")

    content.addWidget(footer)


# =========================================================
# GOALS
# =========================================================

def goal_dialog():

    dialog = QDialog(window)

    dialog.setWindowTitle("Add a goal")
    dialog.resize(420, 300)

    layout = QVBoxLayout(dialog)

    title = QLineEdit()
    title.setPlaceholderText(
        "e.g. Learn Transformers"
    )

    layout.addWidget(QLabel("Goal"))
    layout.addWidget(title)

    description = QLineEdit()
    description.setPlaceholderText(
        "What does success look like?"
    )

    layout.addWidget(QLabel("Description"))
    layout.addWidget(description)

    priority = QComboBox()
    priority.addItems([
        "High",
        "Medium",
        "Low"
    ])

    layout.addWidget(QLabel("Priority"))
    layout.addWidget(priority)

    deadline = QDateEdit()
    deadline.setCalendarPopup(True)

    deadline.setDate(
        date.today() + timedelta(days=30)
    )

    layout.addWidget(QLabel("Deadline"))
    layout.addWidget(deadline)

    save = QPushButton("🌷 Add goal")
    save.setObjectName("primary")

    layout.addWidget(save)

    save.clicked.connect(dialog.accept)

    if dialog.exec() and title.text().strip():

        return (
            title.text().strip(),
            description.text().strip(),
            priority.currentText(),
            deadline.date().toString(
                "yyyy-MM-dd"
            )
        )

    return None


def add_goal_popup():

    data = goal_dialog()

    if data:

        add_goal(*data)

        show_goals()


# =========================================================
# GOAL → AI TASKS → SCHEDULE
# =========================================================

def generate_goal_tasks(
    goal_id,
    title,
    deadline
):

    try:

        # ---------------------------------------------
        # 1. Ask Gemini what needs to be done.
        # ---------------------------------------------

        tasks = decompose_goal(title)

        # ---------------------------------------------
        # 2. Parse deadline.
        # ---------------------------------------------

        try:

            deadline_date = datetime.strptime(
                deadline,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            deadline_date = (
                date.today()
                + timedelta(days=14)
            )

        # ---------------------------------------------
        # 3. Build busy schedule.
        # ---------------------------------------------

        busy_by_date = {}

        current_date = date.today()

        while current_date <= deadline_date:

            day_string = current_date.isoformat()

            busy_by_date[day_string] = []

            # Existing commitments.
            commitments = get_commitments(
                day_string
            )

            for commitment in commitments:

                (
                    _cid,
                    _title,
                    _date,
                    start,
                    end
                ) = commitment

                if start and end:

                    busy_by_date[
                        day_string
                    ].append(
                        (start, end)
                    )

            # Existing scheduled tasks.
            existing_tasks = get_tasks(
                day_string
            )

            for existing in existing_tasks:

                (
                    _tid,
                    _title,
                    _description,
                    _task_date,
                    start,
                    end,
                    _priority,
                    _completed,
                    _duration,
                    _goal_id
                ) = existing

                if start and end:

                    busy_by_date[
                        day_string
                    ].append(
                        (start, end)
                    )

            current_date += timedelta(days=1)

        # ---------------------------------------------
        # 4. Let deterministic Python scheduler
        #    decide when everything goes.
        # ---------------------------------------------

        scheduled = suggest_schedule(
            tasks,
            date.today(),
            deadline_date,
            busy_by_date
        )

        # ---------------------------------------------
        # 5. Save scheduled tasks.
        # ---------------------------------------------

        for item in scheduled:

            add_task(
                item["title"],
                f"Generated from goal: {title}",
                item["date"],
                item["start"],
                item["end"],
                item["priority"],
                item["duration_minutes"],
                goal_id
            )

        if len(scheduled) < len(tasks):

            QMessageBox.warning(
                window,
                "Not enough free time",
                (
                    f"I created {len(scheduled)} "
                    f"of {len(tasks)} tasks.\n\n"
                    "There wasn't enough available "
                    "time before the deadline for "
                    "everything."
                )
            )

        else:

            QMessageBox.information(
                window,
                "Goal broken down ✨",
                (
                    f"I created {len(scheduled)} "
                    f"tasks for:\n{title}"
                )
            )

        show_today()

    except Exception as error:

        QMessageBox.critical(
            window,
            "Planner error",
            str(error)
        )


def goal_card(goal, index=0):

    (
        goal_id,
        title,
        description,
        priority,
        deadline
    ) = goal

    card = QFrame()

    card.setObjectName(
        "cardAlt" if index % 2 else "card"
    )

    layout = QVBoxLayout(card)

    title_label = QLabel(
        "🎯  " + title
    )

    title_label.setStyleSheet(
        "font-weight: bold; font-size: 17px;"
    )

    layout.addWidget(title_label)

    if description:
        layout.addWidget(
            QLabel(description)
        )

    meta = QLabel(
        f"Priority: {priority}   •   "
        f"Deadline: {deadline or 'None'}"
    )

    meta.setObjectName("muted")

    layout.addWidget(meta)

    actions = QHBoxLayout()

    break_button = QPushButton(
        "✨ Break into tasks"
    )

    break_button.setObjectName(
        "smart"
    )

    break_button.clicked.connect(
        lambda checked=False,
               gid=goal_id,
               t=title,
               d=deadline:
        generate_goal_tasks(
            gid,
            t,
            d
        )
    )

    actions.addWidget(
        break_button
    )

    delete_button = QPushButton(
        "Delete"
    )

    delete_button.setObjectName(
        "danger"
    )

    def remove_goal():

        answer = QMessageBox.question(
            window,
            "Delete goal?",
            (
                f"Delete '{title}'?\n\n"
                "Any tasks generated from "
                "this goal will also be deleted."
            ),
            QMessageBox.Yes |
            QMessageBox.No
        )

        if answer == QMessageBox.Yes:

            delete_goal(goal_id)

            show_goals()

    delete_button.clicked.connect(
        remove_goal
    )

    actions.addWidget(
        delete_button
    )

    layout.addLayout(actions)

    return card


def show_goals():

    clear_content()

    heading = QLabel(
        "Things I'm working toward 🌷"
    )

    heading.setObjectName("title")

    content.addWidget(heading)

    content.addWidget(
        QLabel(
            "Turn big goals into small actions. "
            "The planner can help with that."
        )
    )

    add = QPushButton(
        "＋ Add goal"
    )

    add.setObjectName("primary")

    add.clicked.connect(
        add_goal_popup
    )

    content.addWidget(add)

    goals = get_goals()

    if not goals:

        content.addWidget(
            QLabel(
                "🌱 No goals yet.\n"
                "Start with something you "
                "genuinely want to achieve."
            )
        )

    else:

        for i, goal in enumerate(goals):

            content.addWidget(
                goal_card(
                    goal,
                    i
                )
            )

    content.addStretch()


# =========================================================
# CALENDAR
# =========================================================

def show_calendar():

    clear_content()

    heading = QLabel(
        "Your calendar 🗓️"
    )

    heading.setObjectName("title")

    content.addWidget(heading)

    add = QPushButton(
        "＋ Add scheduled task"
    )

    add.setObjectName("primary")

    add.clicked.connect(
        add_task_popup
    )

    content.addWidget(add)

    today = date.today()

    for offset in range(7):

        day = today + timedelta(
            days=offset
        )

        tasks = get_tasks(
            day.isoformat()
        )

        day_label = QLabel(
            f"{day.strftime('%A')}  •  "
            f"{day.strftime('%d %b')}"
        )

        day_label.setStyleSheet(
            "font-weight: bold; font-size: 16px;"
        )

        content.addWidget(
            day_label
        )

        if tasks:

            for i, task in enumerate(tasks):

                content.addWidget(
                    task_card(
                        task,
                        i
                    )
                )

        else:

            empty = QLabel(
                "  Nothing planned"
            )

            empty.setObjectName(
                "muted"
            )

            content.addWidget(
                empty
            )

    content.addStretch()


# =========================================================
# HABITS
# =========================================================

def habit_dialog():

    dialog = QDialog(window)

    dialog.setWindowTitle(
        "Add a habit"
    )

    dialog.resize(380, 220)

    layout = QVBoxLayout(dialog)

    title = QLineEdit()

    title.setPlaceholderText(
        "e.g. Read for 30 minutes"
    )

    layout.addWidget(
        QLabel("Habit")
    )

    layout.addWidget(title)

    frequency = QComboBox()

    frequency.addItems([
        "Daily",
        "Weekdays",
        "3x per week"
    ])

    layout.addWidget(
        QLabel("Frequency")
    )

    layout.addWidget(
        frequency
    )

    save = QPushButton(
        "🌿 Add habit"
    )

    save.setObjectName(
        "primary"
    )

    layout.addWidget(save)

    save.clicked.connect(
        dialog.accept
    )

    if dialog.exec() and title.text().strip():

        return (
            title.text().strip(),
            frequency.currentText()
        )

    return None


def show_habits():

    clear_content()

    heading = QLabel(
        "Little habits 🌿"
    )

    heading.setObjectName(
        "title"
    )

    content.addWidget(
        heading
    )

    add = QPushButton(
        "＋ Add habit"
    )

    add.setObjectName(
        "primary"
    )

    add.clicked.connect(
        add_habit_popup
    )

    content.addWidget(add)

    habits = get_habits()

    if not habits:

        content.addWidget(
            QLabel(
                "🌱 No habits yet."
            )
        )

    else:

        for habit_id, title, frequency, last_completed in habits:

            card = QFrame()
            card.setObjectName(
                "card"
            )

            row = QHBoxLayout(card)

            label = QLabel(
                f"🌿 {title}\n"
                f"{frequency}"
            )

            row.addWidget(
                label,
                1
            )

            check = QPushButton(
                "✓ Done today"
            )

            check.clicked.connect(
                lambda checked=False,
                       hid=habit_id:
                (
                    toggle_habit(hid),
                    show_habits()
                )
            )

            row.addWidget(check)

            content.addWidget(
                card
            )

    content.addStretch()


def add_habit_popup():

    data = habit_dialog()

    if data:

        add_habit(*data)

        show_habits()


# =========================================================
# COMMITMENTS
# =========================================================

def commitment_dialog():

    dialog = QDialog(window)

    dialog.setWindowTitle(
        "Add a commitment"
    )

    dialog.resize(420, 300)

    layout = QVBoxLayout(dialog)

    title = QLineEdit()

    title.setPlaceholderText(
        "e.g. College lecture"
    )

    layout.addWidget(
        QLabel("What are you busy with?")
    )

    layout.addWidget(title)

    commitment_date = QDateEdit()

    commitment_date.setCalendarPopup(
        True
    )

    commitment_date.setDate(
        date.today()
    )

    layout.addWidget(
        QLabel("Date")
    )

    layout.addWidget(
        commitment_date
    )

    start = QTimeEdit()

    start.setDisplayFormat(
        "HH:mm"
    )

    layout.addWidget(
        QLabel("Starts")
    )

    layout.addWidget(start)

    end = QTimeEdit()

    end.setDisplayFormat(
        "HH:mm"
    )

    layout.addWidget(
        QLabel("Ends")
    )

    layout.addWidget(end)

    save = QPushButton(
        "📌 Add commitment"
    )

    save.setObjectName(
        "primary"
    )

    layout.addWidget(save)

    save.clicked.connect(
        dialog.accept
    )

    if dialog.exec() and title.text().strip():

        start_time = (
            start.time().toString(
                "HH:mm"
            )
        )

        end_time = (
            end.time().toString(
                "HH:mm"
            )
        )

        return (
            title.text().strip(),
            commitment_date.date().toString(
                "yyyy-MM-dd"
            ),
            start_time,
            end_time
        )

    return None


def add_commitment_popup():

    data = commitment_dialog()

    if data:

        add_commitment(*data)

        show_settings()


def show_settings():

    clear_content()

    heading = QLabel(
        "Little Day settings ⚙️"
    )

    heading.setObjectName(
        "title"
    )

    content.addWidget(
        heading
    )

    content.addWidget(
        QLabel(
            "Tell Little Day about the things "
            "that already occupy your time."
        )
    )

    commitment_button = QPushButton(
        "＋ Add commitment"
    )

    commitment_button.setObjectName(
        "primary"
    )

    commitment_button.clicked.connect(
        add_commitment_popup
    )

    content.addWidget(
        commitment_button
    )

    section = QLabel(
        "YOUR COMMITMENTS"
    )

    section.setStyleSheet(
        "font-weight: bold;"
    )

    content.addWidget(
        section
    )

    commitments = get_commitments()

    if not commitments:

        content.addWidget(
            QLabel(
                "🌱 No commitments yet.\n"
                "Add classes, meetings, gym sessions, "
                "appointments, etc."
            )
        )

    else:

        for (
            commitment_id,
            title,
            commitment_date,
            start,
            end
        ) in commitments:

            card = QFrame()

            card.setObjectName(
                "card"
            )

            row = QHBoxLayout(card)

            label = QLabel(
                f"📌 {title}\n"
                f"{commitment_date}  •  "
                f"{start}–{end}"
            )

            row.addWidget(
                label,
                1
            )

            delete = QPushButton(
                "Delete"
            )

            delete.setObjectName(
                "danger"
            )

            def remove_commitment(
                checked=False,
                cid=commitment_id
            ):

                delete_commitment(cid)

                show_settings()

            delete.clicked.connect(
                remove_commitment
            )

            row.addWidget(delete)

            content.addWidget(card)

    content.addStretch()


# =========================================================
# SMART DAILY PLAN
# =========================================================

def show_smart_plan():

    clear_content()

    heading = QLabel(
        "Plan my day 🧠"
    )

    heading.setObjectName(
        "title"
    )

    content.addWidget(
        heading
    )

    content.addWidget(
        QLabel(
            "Little Day will fit your unfinished "
            "tasks around your existing commitments."
        )
    )

    tasks = get_tasks(
        date.today().isoformat()
    )

    unfinished = [
        task
        for task in tasks
        if not task[7]
    ]

    if not unfinished:

        content.addWidget(
            QLabel(
                "✨ You're clear for today!\n"
                "Add a task or work on a goal."
            )
        )

    else:

        content.addWidget(
            QLabel(
                f"I found {len(unfinished)} "
                "unfinished task(s):"
            )
        )

        for i, task in enumerate(
            unfinished
        ):

            content.addWidget(
                task_card(
                    task,
                    i
                )
            )

        plan_button = QPushButton(
            "🧠 Generate a realistic schedule"
        )

        plan_button.setObjectName(
            "smart"
        )

        plan_button.clicked.connect(
            lambda:
            generate_schedule_for_today(
                unfinished
            )
        )

        content.addWidget(
            plan_button
        )

    content.addStretch()


def generate_schedule_for_today(tasks):

    today_string = date.today().isoformat()

    busy = []

    # Existing commitments.
    commitments = get_commitments(
        today_string
    )

    for (
        _cid,
        _title,
        _date,
        start,
        end
    ) in commitments:

        if start and end:
            busy.append(
                (start, end)
            )

    # Existing scheduled tasks are also busy.
    for task in tasks:

        start = task[4]
        end = task[5]

        if start and end:
            busy.append(
                (start, end)
            )

    # Temporarily remove each task's own
    # current schedule, otherwise it would
    # block itself.
    busy_without_tasks = []

    for (
        _cid,
        _title,
        _date,
        start,
        end
    ) in commitments:

        if start and end:
            busy_without_tasks.append(
                (start, end)
            )

    # Build tasks for the scheduler.
    scheduler_tasks = []

    for task in tasks:

        duration = task[8] or 60

        scheduler_tasks.append({
            "id": task[0],
            "title": task[1],
            "priority": task[6],
            "duration_minutes": duration
        })

    scheduled = suggest_schedule(
        scheduler_tasks,
        date.today(),
        date.today(),
        {
            today_string:
            busy_without_tasks
        }
    )

    if not scheduled:

        QMessageBox.warning(
            window,
            "No free time",
            (
                "I couldn't find enough free time "
                "between 09:00 and 18:00 today."
            )
        )

        return

    # Show preview first.
    lines = []

    for item in scheduled:

        lines.append(
            f"{item['start']}–{item['end']}  "
            f"{item['title']}"
        )

    answer = QMessageBox.question(
        window,
        "Suggested schedule 🧠",
        (
            "Here's what Little Day suggests:\n\n"
            + "\n".join(lines)
            + "\n\nApply this schedule?"
        ),
        QMessageBox.Yes |
        QMessageBox.No
    )

    if answer != QMessageBox.Yes:
        return

    # Apply schedule to the actual tasks.
    task_lookup = {
        task["title"]: task
        for task in scheduler_tasks
    }

    for item in scheduled:

        task = task_lookup.get(
            item["title"]
        )

        if task:

            update_task_schedule(
                task["id"],
                item["date"],
                item["start"],
                item["end"]
            )

    QMessageBox.information(
        window,
        "Schedule updated ✨",
        "Your tasks have been scheduled around your commitments."
    )

    show_today()


# =========================================================
# NAVIGATION
# =========================================================

today_button.clicked.connect(
    show_today
)

goals_button.clicked.connect(
    show_goals
)

calendar_button.clicked.connect(
    show_calendar
)

habits_button.clicked.connect(
    show_habits
)

smart_button.clicked.connect(
    show_smart_plan
)

settings_button.clicked.connect(
    show_settings
)


# =========================================================
# START
# =========================================================

show_today()

main.addWidget(
    sidebar
)

main.addWidget(
    paper,
    1
)

window.show()

sys.exit(
    app.exec()
)