# app.py
import streamlit as st
import yaml
import streamlit_authenticator as stauth
from yaml.loader import SafeLoader
import datetime
import time
import os
from database import init_db
from auth import login_user, create_user, get_all_users, get_supervisors
from database import (
    create_task, get_employees_by_supervisor, get_tasks_created_by_supervisor,
    get_tasks_for_employee, update_task_status, get_tasks_pending_review
)

# Инициализация базы
init_db()

# Настройки страницы
st.set_page_config(page_title="Плановик задач", layout="wide")

# Загрузка конфигурации
with open("config.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

name, authentication_status, username = authenticator.login("Вход в систему", "main")

if authentication_status is False:
    st.error("Неверный логин или пароль")
elif authentication_status is None:
    st.warning("Пожалуйста, введите логин и пароль")

if authentication_status:
    st.sidebar.title(f"👤 {name}")
    authenticator.logout("🚪 Выйти", "sidebar")

    # Роль пользователя
    user_record = login_user(username, None, bypass_password=True)
    role = user_record['role']
    user_id = user_record['id']

    st.title("📋 Плановик задач")

    # Владелец
    if role == 'owner':
        st.subheader("👤 Управление пользователями")
        with st.expander("➕ Создать нового пользователя"):
            new_username = st.text_input("Логин")
            new_password = st.text_input("Пароль", type="password")
            new_role = st.selectbox("Роль", ["supervisor", "employee"])

            supervisors = get_supervisors()
            supervisor_id = None
            if new_role == "employee" and supervisors:
                sel = st.selectbox("Назначить руководителя", [f"{i[0]} — {i[1]}" for i in supervisors])
                supervisor_id = int(sel.split(" — ")[0])

            if st.button("Создать пользователя"):
                create_user(new_username, new_password, new_role, supervisor_id)
                st.success("Пользователь создан")
                st.rerun()

        st.subheader("📋 Список пользователей")
        for u in get_all_users():
            st.write(f"{u[1]} ({u[2]})")

    # Руководитель
    elif role == 'supervisor':
        st.subheader("📌 Создать задачу")
        employees = get_employees_by_supervisor(user_id)
        emp_dict = {f"{e[1]} (ID {e[0]})": e[0] for e in employees}
        selected_emp = st.selectbox("Сотрудник", list(emp_dict.keys()))
        title = st.text_input("Название задачи")
        description = st.text_area("Описание")
        priority = st.slider("Приоритет", 1, 10, 5)
        deadline = st.number_input("Срок (мин)", 1)

        image_path = None
        file = st.file_uploader("Файл", type=["jpg", "jpeg", "png"])
        if file:
            os.makedirs("tasks", exist_ok=True)
            image_path = os.path.join("tasks", file.name)
            with open(image_path, "wb") as f:
                f.write(file.read())

        if st.button("Отправить задачу"):
            create_task(user_id, emp_dict[selected_emp], title, description, image_path, priority, deadline)
            st.success("Задача отправлена")
            st.rerun()

        st.subheader("📋 Мои задачи")
        tasks = get_tasks_created_by_supervisor(user_id)
        for t in tasks:
            st.markdown(f"**{t[2]}** — {t[3]} | Приоритет: {t[4]}")

    # Сотрудник
    elif role == 'employee':
        st.subheader("📥 Мои задачи")
        tasks = get_tasks_for_employee(user_id)

        for task in tasks:
            task_id, title, desc, image, priority, deadline, status, created, accepted = task
            st.markdown(f"### 📌 {title}\n{desc}")

            if image and os.path.exists(image):
                st.image(image, width=300)

            st.text(f"Статус: {status} | Приоритет: {priority} | Срок: {deadline} мин")

            col1, col2 = st.columns(2)
            if status == 'не просмотрено':
                if col1.button("✅ Принято", key=f"acc_{task_id}"):
                    update_task_status(task_id, 'в работе', accepted=True)
                    st.rerun()
            elif status == 'в работе':
                if col2.button("📤 Выполнено", key=f"done_{task_id}"):
                    update_task_status(task_id, 'на проверке', completed=True)
                    st.rerun()

            st.markdown("---")
