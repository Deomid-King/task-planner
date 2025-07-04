import sqlite3

DB_NAME = "users.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supervisor_id INTEGER,
            employee_id INTEGER,
            title TEXT,
            description TEXT,
            image_path TEXT,
            priority INTEGER,
            deadline INTEGER,
            status TEXT DEFAULT 'не просмотрено',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            accepted BOOLEAN DEFAULT 0,
            completed BOOLEAN DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def create_task(supervisor_id, employee_id, title, description, image_path, priority, deadline):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tasks (supervisor_id, employee_id, title, description, image_path, priority, deadline)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (supervisor_id, employee_id, title, description, image_path, priority, deadline))
    conn.commit()
    conn.close()

def get_employees_by_supervisor(supervisor_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE supervisor_id = ?", (supervisor_id,))
    data = cursor.fetchall()
    conn.close()
    return data

def get_tasks_created_by_supervisor(supervisor_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE supervisor_id = ?", (supervisor_id,))
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def get_tasks_for_employee(employee_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE employee_id = ?", (employee_id,))
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def update_task_status(task_id, status, accepted=False, completed=False):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE tasks
        SET status = ?, accepted = ?, completed = ?
        WHERE id = ?
    ''', (status, int(accepted), int(completed), task_id))
    conn.commit()
    conn.close()

def get_tasks_pending_review(supervisor_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE supervisor_id = ? AND status = 'на проверке'", (supervisor_id,))
    tasks = cursor.fetchall()
    conn.close()
    return tasks
