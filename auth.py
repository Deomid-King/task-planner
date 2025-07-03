import hashlib
from database import create_connection

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_user(username, password):
    conn = create_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, username, password, role, supervisor_id FROM users WHERE username = ?", (username,))
    user = cur.fetchone()

    if user and user[2] == hash_password(password):
        return {
            "id": user[0],
            "username": user[1],
            "role": user[3],
            "supervisor_id": user[4]
        }

    return None

def get_all_users():
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, role FROM users")
    return cur.fetchall()
def create_user(username, password, role, supervisor_id=None):
    from database import hash_password
    conn = create_connection()
    cur = conn.cursor()
    try:
        cur.execute('''
            INSERT INTO users (username, password, role, supervisor_id)
            VALUES (?, ?, ?, ?)
        ''', (username, hash_password(password), role, supervisor_id))
        conn.commit()
        return True
    except Exception as e:
        print("Ошибка при создании пользователя:", e)
        return False

def get_supervisors():
    conn = create_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username FROM users WHERE role IN ('supervisor', 'owner')")
    return cur.fetchall()

