import json
import os
import sys
import time
from pathlib import Path
from datetime import date, timedelta

from dotenv import load_dotenv
from google import genai


# ============================================================
# LITTLE DAY CONFIGURATION
# ============================================================

def get_config_directory():

    # Normal development mode
    if not getattr(
        sys,
        "frozen",
        False
    ):

        return Path(__file__).resolve().parent

    # Packaged macOS application
    #
    # Example:
    #
    # /Applications/Little Day.app/
    #     Contents/
    #         MacOS/
    #             Little Day
    #
    # We store user configuration outside
    # the application bundle.

    config_dir = (
        Path.home()
        / "Library"
        / "Application Support"
        / "Little Day"
    )

    config_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    return config_dir


CONFIG_DIR = get_config_directory()

ENV_FILE = CONFIG_DIR / ".env"


# Load packaged-app configuration first
load_dotenv(
    dotenv_path=ENV_FILE
)

# Also allow normal development .env
load_dotenv()


MODEL = "gemini-3.8-flash"


# ============================================================
# DEFAULT PLANNING PREFERENCES
# ============================================================

DEFAULT_START = "09:00"
DEFAULT_END = "18:00"

DEFAULT_FOCUS_PERIOD = "Morning"

DEFAULT_BREAK_MINUTES = 10


# ============================================================
# GEMINI
# ============================================================

def get_client():

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    if not api_key:

        raise RuntimeError(
            "GEMINI_API_KEY is not set.\n\n"
            "Make sure your .env file contains:\n\n"
            "GEMINI_API_KEY=your_key_here"
        )

    return genai.Client(
        api_key=api_key
    )


def decompose_goal(goal):

    client = get_client()

    prompt = f"""
You are the planning assistant inside a personal productivity app.

The user's goal is:

"{goal}"

Break this goal into 4-6 realistic, actionable tasks.

Rules:

- Tasks must be concrete actions.
- Start from fundamentals and progress toward the goal.
- Do not make tasks ridiculously large.
- Each task should take between 30 and 120 minutes.
- Assign a realistic duration_minutes to every task.
- Use "High", "Medium", or "Low" for priority.
- Tasks should form a sensible progression toward the goal.
- Return ONLY valid JSON.
- Do not include markdown.
- Do not include explanations.

Use exactly this format:

{{
    "tasks": [
        {{
            "title": "task title",
            "priority": "High",
            "duration_minutes": 60
        }}
    ]
}}
"""

    for attempt in range(3):

        try:

            response = client.models.generate_content(
                model=MODEL,
                contents=prompt
            )

            text = response.text.strip()

            if text.startswith("```"):

                text = text.replace(
                    "```json",
                    ""
                )

                text = text.replace(
                    "```",
                    ""
                )

                text = text.strip()

            data = json.loads(text)

            tasks = data.get(
                "tasks",
                []
            )

            if not tasks:

                raise ValueError(
                    "Gemini returned no tasks."
                )

            cleaned_tasks = []

            for task in tasks:

                title = str(
                    task.get(
                        "title",
                        ""
                    )
                ).strip()

                if not title:
                    continue

                priority = task.get(
                    "priority",
                    "Medium"
                )

                if priority not in [
                    "High",
                    "Medium",
                    "Low"
                ]:

                    priority = "Medium"

                duration = task.get(
                    "duration_minutes",
                    60
                )

                try:

                    duration = int(
                        duration
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    duration = 60

                duration = max(
                    30,
                    min(
                        duration,
                        120
                    )
                )

                cleaned_tasks.append({
                    "title": title,
                    "priority": priority,
                    "duration_minutes": duration
                })

            if not cleaned_tasks:

                raise ValueError(
                    "No usable tasks returned."
                )

            return cleaned_tasks

        except Exception as error:

            if attempt == 2:

                raise RuntimeError(
                    "Gemini is temporarily unavailable.\n\n"
                    "Please wait a little and try again.\n\n"
                    f"Original error: {error}"
                )

            time.sleep(
                2 * (attempt + 1)
            )


# ============================================================
# TIME HELPERS
# ============================================================

def time_to_minutes(value):

    if not value:
        return None

    try:

        hour, minute = value.split(":")

        return (
            int(hour) * 60
            + int(minute)
        )

    except (
        ValueError,
        AttributeError
    ):

        return None


def minutes_to_time(value):

    hour = value // 60
    minute = value % 60

    return f"{hour:02d}:{minute:02d}"


# ============================================================
# PREFERENCE HELPERS
# ============================================================

def normalise_preferences(
    preferences=None
):

    if preferences is None:

        preferences = {}

    planning_start = preferences.get(
        "planning_start",
        DEFAULT_START
    )

    planning_end = preferences.get(
        "planning_end",
        DEFAULT_END
    )

    focus_period = preferences.get(
        "focus_period",
        DEFAULT_FOCUS_PERIOD
    )

    break_minutes = preferences.get(
        "break_minutes",
        DEFAULT_BREAK_MINUTES
    )

    if (
        time_to_minutes(planning_start)
        is None
    ):

        planning_start = DEFAULT_START

    if (
        time_to_minutes(planning_end)
        is None
    ):

        planning_end = DEFAULT_END

    try:

        break_minutes = int(
            break_minutes
        )

    except (
        TypeError,
        ValueError
    ):

        break_minutes = DEFAULT_BREAK_MINUTES

    break_minutes = max(
        0,
        min(
            break_minutes,
            60
        )
    )

    if focus_period not in [
        "Morning",
        "Afternoon",
        "Evening"
    ]:

        focus_period = DEFAULT_FOCUS_PERIOD

    return {
        "planning_start": planning_start,
        "planning_end": planning_end,
        "focus_period": focus_period,
        "break_minutes": break_minutes
    }


def period_for_time(
    minutes
):

    hour = minutes // 60

    if hour < 12:

        return "Morning"

    if hour < 17:

        return "Afternoon"

    return "Evening"


def energy_score(
    start_minutes,
    priority,
    focus_period
):

    period = period_for_time(
        start_minutes
    )

    # --------------------------------------------------------
    # High priority work strongly prefers the user's
    # chosen focus period.
    # --------------------------------------------------------

    if priority == "High":

        if period == focus_period:
            return 100

        return 60

    # --------------------------------------------------------
    # Medium priority work has a smaller preference.
    # --------------------------------------------------------

    if priority == "Medium":

        if period == focus_period:
            return 80

        return 70

    # --------------------------------------------------------
    # Low priority work is intentionally easier to move around.
    # --------------------------------------------------------

    if period == focus_period:

        return 65

    return 80


# ============================================================
# FREE TIME CALCULATOR
# ============================================================

def find_free_slots(
    busy_blocks,
    start_time=DEFAULT_START,
    end_time=DEFAULT_END
):

    day_start = time_to_minutes(
        start_time
    )

    day_end = time_to_minutes(
        end_time
    )

    if (
        day_start is None
        or day_end is None
        or day_end <= day_start
    ):

        day_start = time_to_minutes(
            DEFAULT_START
        )

        day_end = time_to_minutes(
            DEFAULT_END
        )

    busy = []

    for block in busy_blocks:

        if isinstance(block, dict):

            start = block.get(
                "start_time",
                ""
            )

            end = block.get(
                "end_time",
                ""
            )

        else:

            start, end = block

        start_minutes = time_to_minutes(
            start
        )

        end_minutes = time_to_minutes(
            end
        )

        if (
            start_minutes is None
            or end_minutes is None
        ):
            continue

        if end_minutes <= day_start:
            continue

        if start_minutes >= day_end:
            continue

        start_minutes = max(
            start_minutes,
            day_start
        )

        end_minutes = min(
            end_minutes,
            day_end
        )

        if end_minutes > start_minutes:

            busy.append(
                (
                    start_minutes,
                    end_minutes
                )
            )

    busy.sort()

    # --------------------------------------------------------
    # Merge overlapping busy blocks.
    # --------------------------------------------------------

    merged = []

    for start, end in busy:

        if (
            not merged
            or start > merged[-1][1]
        ):

            merged.append(
                [start, end]
            )

        else:

            merged[-1][1] = max(
                merged[-1][1],
                end
            )

    # --------------------------------------------------------
    # Find free regions.
    # --------------------------------------------------------

    free_slots = []

    current = day_start

    for start, end in merged:

        if current < start:

            free_slots.append(
                (
                    current,
                    start
                )
            )

        current = max(
            current,
            end
        )

    if current < day_end:

        free_slots.append(
            (
                current,
                day_end
            )
        )

    return free_slots


# ============================================================
# SLOT CANDIDATES
# ============================================================

def generate_candidate_slots(
    free_slots,
    duration
):

    candidates = []

    for slot_start, slot_end in free_slots:

        current = slot_start

        while (
            current + duration
            <= slot_end
        ):

            candidates.append(
                current
            )

            current += 30

    return candidates


# ============================================================
# BEST SLOT
# ============================================================

def find_best_slot(
    task,
    free_slots,
    focus_period
):

    duration = task.get(
        "duration_minutes",
        60
    )

    try:

        duration = int(
            duration
        )

    except (
        TypeError,
        ValueError
    ):

        duration = 60

    duration = max(
        30,
        min(
            duration,
            120
        )
    )

    priority = task.get(
        "priority",
        "Medium"
    )

    candidates = generate_candidate_slots(
        free_slots,
        duration
    )

    if not candidates:

        return None

    scored = []

    for start in candidates:

        score = energy_score(
            start,
            priority,
            focus_period
        )

        # Slight preference for earlier times when
        # the energy score is otherwise similar.
        early_bonus = max(
            0,
            180 - start
        ) / 1000

        scored.append(
            (
                score + early_bonus,
                start
            )
        )

    scored.sort(
        key=lambda item: (
            item[0],
            -item[1]
        ),
        reverse=True
    )

    best_start = scored[0][1]

    return (
        best_start,
        duration
    )


# ============================================================
# CONSUME SLOT
# ============================================================

def consume_slot(
    free_slots,
    used_start,
    used_end
):

    new_slots = []

    for slot_start, slot_end in free_slots:

        # No overlap.
        if (
            used_end <= slot_start
            or used_start >= slot_end
        ):

            new_slots.append(
                (
                    slot_start,
                    slot_end
                )
            )

            continue

        # Space before used time.
        if slot_start < used_start:

            new_slots.append(
                (
                    slot_start,
                    used_start
                )
            )

        # Space after used time.
        if used_end < slot_end:

            new_slots.append(
                (
                    used_end,
                    slot_end
                )
            )

    new_slots.sort()

    return new_slots


# ============================================================
# SMART SCHEDULER
# ============================================================

def suggest_schedule(
    tasks,
    start_date,
    deadline,
    busy_by_date=None,
    preferences=None
):

    if deadline < start_date:

        deadline = start_date

    if busy_by_date is None:

        busy_by_date = {}

    preferences = normalise_preferences(
        preferences
    )

    planning_start = preferences[
        "planning_start"
    ]

    planning_end = preferences[
        "planning_end"
    ]

    focus_period = preferences[
        "focus_period"
    ]

    break_minutes = preferences[
        "break_minutes"
    ]

    # --------------------------------------------------------
    # Preserve Gemini's progression.
    # --------------------------------------------------------

    task_queue = list(tasks)

    scheduled = []

    current_date = start_date

    while (
        current_date <= deadline
        and task_queue
    ):

        date_string = current_date.isoformat()

        busy_blocks = list(
            busy_by_date.get(
                date_string,
                []
            )
        )

        free_slots = find_free_slots(
            busy_blocks,
            start_time=planning_start,
            end_time=planning_end
        )

        # ----------------------------------------------------
        # Fill the current day.
        # ----------------------------------------------------

        while task_queue:

            task = task_queue[0]

            result = find_best_slot(
                task,
                free_slots,
                focus_period
            )

            if result is None:

                break

            start_minutes, duration = result

            end_minutes = (
                start_minutes
                + duration
            )

            scheduled.append({
                "title": task["title"],
                "priority": task.get(
                    "priority",
                    "Medium"
                ),
                "duration_minutes": duration,
                "date": date_string,
                "start": minutes_to_time(
                    start_minutes
                ),
                "end": minutes_to_time(
                    end_minutes
                )
            })

            # ------------------------------------------------
            # Consume task time.
            # ------------------------------------------------

            free_slots = consume_slot(
                free_slots,
                start_minutes,
                end_minutes
            )

            # ------------------------------------------------
            # Consume user's chosen break.
            # ------------------------------------------------

            if break_minutes > 0:

                free_slots = consume_slot(
                    free_slots,
                    end_minutes,
                    end_minutes + break_minutes
                )

            # ------------------------------------------------
            # Remove completed task from queue.
            # ------------------------------------------------

            task_queue.pop(0)

        current_date += timedelta(
            days=1
        )

    return scheduled