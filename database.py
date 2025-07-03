import sqlite3
import hashlib
import datetime

def create_connection():
    return sqlite3.connect("task_planner.db", check_same_thread=False)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = create_connection()
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT,
            supervisor_id INTEGER,
            FOREIGN KEY(supervisor_id) REFERENCES users(id)
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator_id INTEGER,
            assignee_id INTEGER,
            title TEXT,
            description TEXT,
            image_path TEXT,
            priority INTEGER,
            deadline_minutes INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            accepted_at TIMESTAMP,
            completed_at TIMESTAMP,
            status TEXT DEFAULT 'не просмотрено',
            FOREIGN KEY(creator_id) REFERENCES users(id),
            FOREIGN KEY(assignee_id) REFERENCES users(id)
        )
    ''')

    cur.execute("SELECT * FROM users WHERE username = ?", ('adminplan',))
    if not cur.fetchone():
        cur.execute('''
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
        ''', ('adminplan', hash_password('Planovik2025***'), 'owner'))

    conn.commit()
    conn.close()

def get_user_by_username(username):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    return cur.fetchone()

def create_task(creator_id, assignee_id, title, description, image_path, priority, deadline_minutes):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO tasks (creator_id, assignee_id, title, description, image_path, priority, deadline_minutes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (creator_id, assignee_id, title, description, image_path, priority, deadline_minutes))
    conn.commit()
    conn.close()

def get_employees_by_supervisor(supervisor_id):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT id, username FROM users
        WHERE supervisor_id = ?
    ''', (supervisor_id,))
    return cur.fetchall()

def get_tasks_created_by_supervisor(supervisor_id):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT t.id, u.username, t.title, t.status, t.priority, t.created_at
        FROM tasks t
        JOIN users u ON t.assignee_id = u.id
        WHERE t.creator_id = ?
        ORDER BY t.created_at DESC
    ''', (supervisor_id,))
    return cur.fetchall()

def get_tasks_for_employee(employee_id):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT id, title, description, image_path, priority, deadline_minutes, status, created_at, accepted_at
        FROM tasks
        WHERE assignee_id = ?
        ORDER BY created_at DESC
    ''', (employee_id,))
    return cur.fetchall()

def update_task_status(task_id, status, accepted=False, completed=False):
    conn = create_connection()
    cur = conn.cursor()
    if accepted:
        cur.execute("UPDATE tasks SET status = ?, accepted_at = ? WHERE id = ?", (status, datetime.datetime.now(), task_id))
    elif completed:
        cur.execute("UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?", (status, datetime.datetime.now(), task_id))
    else:
        cur.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
    conn.commit()
    conn.close()

def get_tasks_pending_review(supervisor_id):
    conn = create_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT t.id, u.username, t.title, t.status, t.priority, t.created_at
        FROM tasks t
        JOIN users u ON t.assignee_id = u.id
        WHERE t.creator_id = ? AND t.status IN ('на проверке', 'не просмотрено')
        ORDER BY t.created_at DESC
    ''', (supervisor_id,))
    return cur.fetchall()
