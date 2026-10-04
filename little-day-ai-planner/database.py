import sqlite3
from datetime import date

DATABASE = "planner.db"


def connect():
    return sqlite3.connect(DATABASE)


def create_database():
    connection = connect()
    cursor = connection.cursor()

    # -------------------------
    # Tasks
    # -------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            date TEXT NOT NULL,
            start_time TEXT DEFAULT '',
            end_time TEXT DEFAULT '',
            priority TEXT DEFAULT 'Medium',
            completed INTEGER DEFAULT 0,
            duration_minutes INTEGER DEFAULT 60,
            goal_id INTEGER
        )
    """)

    # Add newer columns if this is an older database.
    task_columns = [
        row[1] for row in cursor.execute("PRAGMA table_info(tasks)")
    ]

    if "duration_minutes" not in task_columns:
        cursor.execute(
            "ALTER TABLE tasks ADD COLUMN duration_minutes INTEGER DEFAULT 60"
        )

    if "goal_id" not in task_columns:
        cursor.execute(
            "ALTER TABLE tasks ADD COLUMN goal_id INTEGER"
        )

    # -------------------------
    # Goals
    # -------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            priority TEXT DEFAULT 'Medium',
            deadline TEXT DEFAULT ''
        )
    """)

    # -------------------------
    # Habits
    # -------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            frequency TEXT DEFAULT 'Daily',
            last_completed TEXT DEFAULT ''
        )
    """)

    # -------------------------
    # Commitments
    # -------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS commitments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            start_time TEXT,
            end_time TEXT
        )
    """)

    # -------------------------
    # Old prototype migration
    # -------------------------
    task_columns = [
        row[1] for row in cursor.execute("PRAGMA table_info(tasks)")
    ]

    if "time" in task_columns and "date" not in task_columns:
        cursor.execute("ALTER TABLE tasks RENAME TO tasks_old")

        cursor.execute("""
            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                date TEXT NOT NULL,
                start_time TEXT DEFAULT '',
                end_time TEXT DEFAULT '',
                priority TEXT DEFAULT 'Medium',
                completed INTEGER DEFAULT 0,
                duration_minutes INTEGER DEFAULT 60,
                goal_id INTEGER
            )
        """)

        cursor.execute("""
            INSERT INTO tasks
            (id, title, description, date, start_time, end_time,
             priority, completed, duration_minutes, goal_id)
            SELECT
                id,
                title,
                COALESCE(description, ''),
                date('now'),
                CASE WHEN time = 'New' THEN '' ELSE COALESCE(time, '') END,
                '',
                'Medium',
                COALESCE(completed, 0),
                60,
                NULL
            FROM tasks_old
        """)

        cursor.execute("DROP TABLE tasks_old")

    connection.commit()
    connection.close()


# =========================================================
# TASKS
# =========================================================

def add_task(
    title,
    description="",
    task_date="",
    start_time="",
    end_time="",
    priority="Medium",
    duration_minutes=60,
    goal_id=None
):
    connection = connect()

    connection.execute("""
        INSERT INTO tasks
        (
            title,
            description,
            date,
            start_time,
            end_time,
            priority,
            duration_minutes,
            goal_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        title,
        description,
        task_date,
        start_time,
        end_time,
        priority,
        duration_minutes,
        goal_id
    ))

    connection.commit()
    connection.close()


def get_tasks(task_date=None):
    connection = connect()

    if task_date:
        rows = connection.execute("""
            SELECT
                id,
                title,
                description,
                date,
                start_time,
                end_time,
                priority,
                completed,
                duration_minutes,
                goal_id
            FROM tasks
            WHERE date = ?
            ORDER BY
                CASE WHEN start_time = '' THEN 1 ELSE 0 END,
                start_time,
                id
        """, (task_date,)).fetchall()
    else:
        rows = connection.execute("""
            SELECT
                id,
                title,
                description,
                date,
                start_time,
                end_time,
                priority,
                completed,
                duration_minutes,
                goal_id
            FROM tasks
            ORDER BY date, start_time, id
        """).fetchall()

    connection.close()
    return rows


def complete_task(task_id):
    connection = connect()

    connection.execute(
        "UPDATE tasks SET completed = 1 WHERE id = ?",
        (task_id,)
    )

    connection.commit()
    connection.close()


def delete_task(task_id):
    connection = connect()

    connection.execute(
        "DELETE FROM tasks WHERE id = ?",
        (task_id,)
    )

    connection.commit()
    connection.close()


def update_task_schedule(task_id, task_date, start_time, end_time):
    connection = connect()

    connection.execute("""
        UPDATE tasks
        SET date = ?, start_time = ?, end_time = ?
        WHERE id = ?
    """, (
        task_date,
        start_time,
        end_time,
        task_id
    ))

    connection.commit()
    connection.close()


# =========================================================
# GOALS
# =========================================================

def add_goal(title, description="", priority="Medium", deadline=""):
    connection = connect()

    connection.execute("""
        INSERT INTO goals
        (title, description, priority, deadline)
        VALUES (?, ?, ?, ?)
    """, (
        title,
        description,
        priority,
        deadline
    ))

    connection.commit()
    connection.close()


def get_goals():
    connection = connect()

    goals = connection.execute("""
        SELECT
            id,
            title,
            description,
            priority,
            deadline
        FROM goals
        ORDER BY
            CASE priority
                WHEN 'High' THEN 1
                WHEN 'Medium' THEN 2
                ELSE 3
            END,
            deadline,
            id
    """).fetchall()

    connection.close()
    return goals


def delete_goal(goal_id):
    connection = connect()

    # Delete all tasks explicitly associated with this goal.
    connection.execute(
        "DELETE FROM tasks WHERE goal_id = ?",
        (goal_id,)
    )

    # Also clean up tasks generated by the older version
    # of Little Day that didn't have goal_id.
    goal = connection.execute(
        "SELECT title FROM goals WHERE id = ?",
        (goal_id,)
    ).fetchone()

    if goal:
        connection.execute(
            """
            DELETE FROM tasks
            WHERE description = ?
            AND goal_id IS NULL
            """,
            (f"Generated from goal: {goal[0]}",)
        )

    connection.execute(
        "DELETE FROM goals WHERE id = ?",
        (goal_id,)
    )

    connection.commit()
    connection.close()


# =========================================================
# HABITS
# =========================================================

def add_habit(title, frequency="Daily"):
    connection = connect()

    connection.execute("""
        INSERT INTO habits
        (title, frequency)
        VALUES (?, ?)
    """, (
        title,
        frequency
    ))

    connection.commit()
    connection.close()


def get_habits():
    connection = connect()

    habits = connection.execute("""
        SELECT
            id,
            title,
            frequency,
            last_completed
        FROM habits
        ORDER BY id
    """).fetchall()

    connection.close()
    return habits


def toggle_habit(habit_id):
    connection = connect()

    connection.execute("""
        UPDATE habits
        SET last_completed = ?
        WHERE id = ?
    """, (
        date.today().isoformat(),
        habit_id
    ))

    connection.commit()
    connection.close()


# =========================================================
# COMMITMENTS
# =========================================================

def add_commitment(
    title,
    commitment_date,
    start_time,
    end_time
):
    connection = connect()

    connection.execute("""
        INSERT INTO commitments
        (title, date, start_time, end_time)
        VALUES (?, ?, ?, ?)
    """, (
        title,
        commitment_date,
        start_time,
        end_time
    ))

    connection.commit()
    connection.close()


def get_commitments(commitment_date=None):
    connection = connect()

    if commitment_date:
        rows = connection.execute("""
            SELECT
                id,
                title,
                date,
                start_time,
                end_time
            FROM commitments
            WHERE date = ?
            ORDER BY start_time
        """, (commitment_date,)).fetchall()
    else:
        rows = connection.execute("""
            SELECT
                id,
                title,
                date,
                start_time,
                end_time
            FROM commitments
            ORDER BY date, start_time
        """).fetchall()

    connection.close()
    return rows


def delete_commitment(commitment_id):
    connection = connect()

    connection.execute(
        "DELETE FROM commitments WHERE id = ?",
        (commitment_id,)
    )

    connection.commit()
    connection.close()