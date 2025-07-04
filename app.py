import streamlit as st
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

init_db()

st.set_page_config("Плановик задач", layout="centered")

st.markdown("""
    <style>
        .task-card {
            background-color: white;
            border-radius: 15px;
            box-shadow: 0px 4px 8px rgba(0,0,0,0.1);
            padding: 16px;
            margin-bottom: 12px;
        }
        .title {
            font-weight: 600;
            font-family: Montserrat, sans-serif;
        }
    </style>
""", unsafe_allow_html=True)

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
st.sidebar.success(f"Вы вошли как {user['username']} ({user['role']})")
if st.sidebar.button("Выйти"):
    del st.session_state.user
    st.experimental_rerun()

# Владельцу — управление пользователями
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
        submitted = st.form_submit_button("Создать пользователя")
        if submitted:
            create_user(new_username, new_password, new_role, supervisor[0] if supervisor else None)
            st.success(f"Пользователь {new_username} создан")

# Создание задачи
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
            submit = st.form_submit_button("Отправить")
            if submit and emp and title:
                image_path = None
                if img:
                    uploads_dir = "uploads"
                    os.makedirs(uploads_dir, exist_ok=True)
                    image_path = os.path.join(uploads_dir, img.name)
                    with open(image_path, "wb") as f:
                        f.write(img.read())
                create_task(user['id'], emp[0], title, desc, image_path, prio, int(mins))
                st.success("Задача назначена")
    else:
        st.info("Нет подчиненных сотрудников")

# Просмотр задач
st.subheader("📋 Мои задачи")
if user['role'] == 'employee':
    tasks = get_tasks_for_employee(user['id'])
else:
    tasks = get_tasks_created_by_supervisor(user['id'])

for task in tasks:
    st.markdown('<div class="task-card">', unsafe_allow_html=True)
    st.markdown(f"**Задача:** {task[3]}")
    st.markdown(f"Описание: {task[4]}")
    st.markdown(f"Статус: `{task[8]}`")
    if task[5]:
        st.image(task[5], width=250)
    if user['role'] == 'employee' and task[8] == "не просмотрено":
        if st.button("Принять", key=f"accept_{task[0]}"):
            update_task_status(task[0], "в работе", accepted=True)
            st.experimental_rerun()
    elif user['role'] == 'employee' and task[8] == "в работе":
        if st.button("Выполнено", key=f"done_{task[0]}"):
            update_task_status(task[0], "на проверке", completed=True)
            st.experimental_rerun()
    elif user['role'] in ["supervisor", "owner"] and task[8] == "на проверке":
        if st.button("Проверено", key=f"check_{task[0]}"):
            update_task_status(task[0], "выполнено")
            st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)
