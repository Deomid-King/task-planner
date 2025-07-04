import streamlit as st
import time
from streamlit_autorefresh import st_autorefresh
from auth import login_user, create_user, get_all_users, get_supervisors
from database import (
    init_db,
    create_task,
    get_employees_by_supervisor,
    get_tasks_created_by_supervisor,
    get_tasks_for_employee,
    update_task_status,
    get_tasks_pending_review
)
import os
from datetime import datetime, timedelta

# Настройки
st.set_page_config("Плановик задач", layout="centered")
init_db()
st_autorefresh(interval=1000, key="global_refresh")  # Обновление каждые 1 сек

# Очистка старых файлов
def clean_old_uploads(days=30):
    folder = "uploads"
    if not os.path.exists(folder):
        return
    for file in os.listdir(folder):
        path = os.path.join(folder, file)
        if os.path.isfile(path):
            file_time = datetime.fromtimestamp(os.path.getctime(path))
            if datetime.now() - file_time > timedelta(days=days):
                os.remove(path)

clean_old_uploads()

# Стили
st.markdown("""
    <style>
        .task-card {
            background-color: white;
            border-radius: 15px;
            box-shadow: 0px 4px 8px rgba(0,0,0,0.1);
            padding: 16px;
            margin-bottom: 12px;
            border-left: 6px solid #f0f0f0;
        }
        .task-card.overdue {
            border-left: 6px solid red;
        }
    </style>
""", unsafe_allow_html=True)

# Таймер
def calculate_remaining_time(created_at_str, deadline_minutes):
    try:
        created_at = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S")
        deadline = created_at + timedelta(minutes=deadline_minutes)
        now = datetime.now()
        remaining = deadline - now
        if remaining.total_seconds() <= 0:
            return "⏰ Время вышло!", True
        else:
            return f"⏳ Осталось: {str(remaining).split('.')[0]}", False
    except:
        return "", False

# Обработка действий
if "action" in st.session_state:
    action = st.session_state.pop("action")
    update_task_status(
        action["task_id"],
        {"accept": "в работе", "done": "на проверке", "check": "выполнено"}[action["type"]],
        accepted=(action["type"] == "accept"),
        completed=(action["type"] == "done")
    )
    st.experimental_rerun()

# Авторизация
if "user" not in st.session_state:
    st.title("🔐 Вход в систему")
    login = st.text_input("Логин")
    password = st.text_input("Пароль", type="password")
    if st.button("Войти"):
        user_record = login_user(login, password)
        if user_record:
            st.session_state.user = user_record
            st.experimental_rerun()
        else:
            st.error("Неверный логин или пароль")
    st.stop()

user = st.session_state.user

# Сайдбар
st.sidebar.success(f"Вы вошли как {user['username']} ({user['role']})")
if st.sidebar.button("Выйти"):
    del st.session_state.user
    st.experimental_rerun()

# Управление пользователями
if user['role'] == 'owner':
    st.subheader("👤 Управление пользователями")
    with st.form("add_user"):
        new_username = st.text_input("Логин")
        new_password = st.text_input("Пароль", type="password")
        new_role = st.selectbox("Роль", ["supervisor", "employee"])
        supervisor = None
        if new_role == "employee":
            supervisors = get_supervisors()
            supervisor = st.selectbox("Назначить руководителя", supervisors, format_func=lambda x: x[1]) if supervisors else None
        if st.form_submit_button("Создать пользователя"):
            create_user(new_username, new_password, new_role, supervisor[0] if supervisor else None)
            st.success(f"Пользователь {new_username} создан")

# Назначение задачи
if user['role'] in ['owner', 'supervisor']:
    st.subheader("📝 Назначить задачу")
    employees = get_employees_by_supervisor(user['id'])
    if employees:
        with st.form("task_form"):
            emp = st.selectbox("Сотрудник", employees, format_func=lambda x: x[1])
            title = st.text_input("Заголовок задачи")
            desc = st.text_area("Описание")
            img = st.file_uploader("Фото", type=["jpg", "png"])
            prio = st.slider("Приоритет (1-10)", 1, 10, 5)
            mins = st.number_input("Срок (минут)", 1, 1440, 60)
            if st.form_submit_button("Отправить") and emp and title:
                image_path = None
                if img:
                    os.makedirs("uploads", exist_ok=True)
                    image_path = os.path.join("uploads", img.name)
                    with open(image_path, "wb") as f:
                        f.write(img.read())
                create_task(user['id'], emp[0], title, desc, image_path, prio, int(mins))
                st.success("Задача назначена")
    else:
        st.info("Нет подчинённых сотрудников")

# Фильтр по статусу
st.subheader("📋 Мои задачи")
selected_status = st.selectbox("Фильтр по статусу", ["Все", "не просмотрено", "в работе", "на проверке", "выполнено"])

# Получение задач
if user['role'] == 'employee':
    tasks = get_tasks_for_employee(user['id'])
else:
    tasks = get_tasks_created_by_supervisor(user['id'])

# Отображение задач
for task in tasks:
    if selected_status != "Все" and task[8] != selected_status:
        continue

    remaining_text, is_overdue = ("", False)
    if task[8] == "в работе":
        remaining_text, is_overdue = calculate_remaining_time(task[9], task[7])

    border_class = "task-card overdue" if is_overdue else "task-card"
    st.markdown(f'<div class="{border_class}">', unsafe_allow_html=True)
    st.markdown(f"**Задача:** {task[3]}")
    st.markdown(f"Описание: {task[4]}")
    st.markdown(f"Статус: `{task[8]}`")

    if task[5] and os.path.exists(task[5]):
        st.image(task[5], width=250)

    if remaining_text:
        st.markdown(f"<span style='color:gray'>{remaining_text}</span>", unsafe_allow_html=True)

    if user['role'] == 'employee' and task[8] == "не просмотрено":
        if st.button("Принять", key=f"accept_{task[0]}"):
            st.session_state.action = {"type": "accept", "task_id": task[0]}
    elif user['role'] == 'employee' and task[8] == "в работе":
        if st.button("Выполнено", key=f"done_{task[0]}"):
            st.session_state.action = {"type": "done", "task_id": task[0]}
    elif user['role'] in ["supervisor", "owner"] and task[8] == "на проверке":
        if st.button("Проверено", key=f"check_{task[0]}"):
            st.session_state.action = {"type": "check", "task_id": task[0]}

    st.markdown("</div>", unsafe_allow_html=True)
