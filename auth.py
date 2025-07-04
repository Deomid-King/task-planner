import sqlite3
import bcrypt

DB_NAME = "users.db"

def create_user(username, password, role, supervisor_id=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    cursor.execute("INSERT INTO users (username, password, role, supervisor_id) VALUES (?, ?, ?, ?)",
                   (username, hashed, role, supervisor_id))
    conn.commit()
    conn.close()

def login_user(username, password, bypass_password=False):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user:
        if bypass_password or bcrypt.checkpw(password.encode(), user[2].encode()):
            return {'id': user[0], 'username': user[1], 'role': user[3], 'supervisor_id': user[4]}
    return None

def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    return users

def get_supervisors():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE role = 'supervisor'")
    users = cursor.fetchall()
    conn.close()
    return users
