# Little Day — AI Planner

A local-first personal planner built with Python, PySide6 and SQLite.

## Current features

- Tasks with dates, times and priorities
- Persistent SQLite database
- Goals with priorities and deadlines
- Automatic goal → task decomposition
- Simple schedule generation
- 7-day calendar view
- Habits
- Git-friendly project structure
- Local-first architecture

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Architecture

- `main.py` — desktop UI
- `database.py` — SQLite persistence
- `planner.py` — planning/decomposition logic

The `decompose_goal()` function is deliberately isolated so a local LLM can replace it later.
