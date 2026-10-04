import json
import os
import sys
import time
from datetime import date, timedelta

from dotenv import load_dotenv


# Find the directory containing the application/project.
if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Look for .env next to the application.
ENV_PATH = os.path.join(APP_DIR, ".env")

load_dotenv(ENV_PATH)
from google import genai



MODEL = "gemini-3.8-flash"


# =========================================================
# GEMINI
# =========================================================

def get_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set.\n\n"
            "Make sure your .env file contains:\n\n"
            "GEMINI_API_KEY=your_key_here"
        )

    return genai.Client(api_key=api_key)


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
                text = text.replace("```json", "")
                text = text.replace("```", "")
                text = text.strip()

            data = json.loads(text)

            tasks = data.get("tasks", [])

            if not tasks:
                raise ValueError("Gemini returned no tasks.")

            cleaned_tasks = []

            for task in tasks:
                title = str(task.get("title", "")).strip()

                if not title:
                    continue

                priority = task.get("priority", "Medium")

                if priority not in ["High", "Medium", "Low"]:
                    priority = "Medium"

                duration = task.get("duration_minutes", 60)

                try:
                    duration = int(duration)
                except (TypeError, ValueError):
                    duration = 60

                duration = max(30, min(duration, 120))

                cleaned_tasks.append({
                    "title": title,
                    "priority": priority,
                    "duration_minutes": duration
                })

            if not cleaned_tasks:
                raise ValueError("No usable tasks returned.")

            return cleaned_tasks

        except Exception as error:
            if attempt == 2:
                raise RuntimeError(
                    "Gemini is temporarily unavailable.\n\n"
                    "Please wait a little and try again.\n\n"
                    f"Original error: {error}"
                )

            time.sleep(2 * (attempt + 1))


# =========================================================
# TIME HELPERS
# =========================================================

def time_to_minutes(value):
    if not value:
        return None

    try:
        hour, minute = value.split(":")
        return int(hour) * 60 + int(minute)
    except (ValueError, AttributeError):
        return None


def minutes_to_time(value):
    hour = value // 60
    minute = value % 60
    return f"{hour:02d}:{minute:02d}"


# =========================================================
# FREE TIME
# =========================================================

def find_free_slots(
    busy_blocks,
    start_hour=9,
    end_hour=18
):
    """
    busy_blocks:
        [
            ("10:00", "11:30"),
            ("14:00", "15:00")
        ]

    Returns:
        [
            (540, 600),
            (690, 840),
            ...
        ]
    """

    day_start = start_hour * 60
    day_end = end_hour * 60

    busy = []

    for block in busy_blocks:
        if isinstance(block, dict):
            start = block.get("start_time", "")
            end = block.get("end_time", "")
        else:
            start, end = block

        start_minutes = time_to_minutes(start)
        end_minutes = time_to_minutes(end)

        if start_minutes is None or end_minutes is None:
            continue

        if end_minutes <= day_start:
            continue

        if start_minutes >= day_end:
            continue

        start_minutes = max(start_minutes, day_start)
        end_minutes = min(end_minutes, day_end)

        if end_minutes > start_minutes:
            busy.append(
                (start_minutes, end_minutes)
            )

    busy.sort()

    # Merge overlapping busy blocks.
    merged = []

    for start, end in busy:
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(
                merged[-1][1],
                end
            )

    free_slots = []
    current = day_start

    for start, end in merged:
        if current < start:
            free_slots.append(
                (current, start)
            )

        current = max(current, end)

    if current < day_end:
        free_slots.append(
            (current, day_end)
        )

    return free_slots


# =========================================================
# SCHEDULER
# =========================================================

def suggest_schedule(
    tasks,
    start_date,
    deadline,
    busy_by_date=None
):
    """
    Deterministic scheduler.

    Gemini decides WHAT needs to be done.

    Python decides WHEN it should happen.

    busy_by_date should look like:

    {
        "2026-10-05": [
            ("09:00", "11:00"),
            ("14:00", "15:00")
        ]
    }
    """

    if deadline < start_date:
        deadline = start_date

    if busy_by_date is None:
        busy_by_date = {}

    # Highest priority first.
    priority_order = {
        "High": 0,
        "Medium": 1,
        "Low": 2
    }

    tasks = sorted(
        tasks,
        key=lambda task: (
            priority_order.get(
                task.get("priority", "Medium"),
                1
            ),
            task.get("title", "")
        )
    )

    scheduled = []

    current_date = start_date
    task_index = 0

    while current_date <= deadline and task_index < len(tasks):

        date_string = current_date.isoformat()

        busy_blocks = list(
            busy_by_date.get(date_string, [])
        )

        # Include tasks already scheduled on that day.
        free_slots = find_free_slots(
            busy_blocks,
            start_hour=9,
            end_hour=18
        )

        for slot_start, slot_end in free_slots:

            if task_index >= len(tasks):
                break

            task = tasks[task_index]

            duration = task.get(
                "duration_minutes",
                60
            )

            try:
                duration = int(duration)
            except (TypeError, ValueError):
                duration = 60

            duration = max(
                30,
                min(duration, 120)
            )

            available = slot_end - slot_start

            if available < duration:
                continue

            start_minutes = slot_start
            end_minutes = (
                start_minutes + duration
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

            # The newly scheduled task becomes busy time.
            busy_blocks.append((
                minutes_to_time(start_minutes),
                minutes_to_time(end_minutes)
            ))

            task_index += 1

            # Recalculate remaining free time.
            free_slots = find_free_slots(
                busy_blocks,
                start_hour=9,
                end_hour=18
            )

            break

        current_date += timedelta(days=1)

    return scheduled