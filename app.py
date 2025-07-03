import streamlit as st
import time
from database import init_db
from auth import login_user, create_user, get_all_users, get_supervisors
from database import (
    create_task, get_employees_by_supervisor, get_tasks_created_by_supervisor,
    get_tasks_for_employee, update_task_status, get_tasks_pending_review
)
import os
import uuid
import datetime

# Запускаем базу
init_db()

# Настройки страницы
st.set_page_config(page_title="Плановик задач", layout="wide")

# --- Авторизация и сохранение сессии ---
if 'user' not in st.session_state:
    st.title("🔐 Вход в систему")
    username = st.text_input("Логин")
    password = st.text_input("Пароль", type="password")
    if st.button("Войти", use_container_width=True):
        user = login_user(username, password)
        if user:
            st.session_state.user = user
            st.rerun()
        else:
            st.error("Неверный логин или пароль")
else:
    user = st.session_state.user
    st.sidebar.title(f"👤 {user['username']} ({user['role']})")

    if st.sidebar.button("🚪 Выйти"):
        del st.session_state.user
        st.rerun()

    # Уведомления для сотрудника
    if user['role'] == 'employee':
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔔 Уведомления")

        tasks = get_tasks_for_employee(user['id'])
        now = datetime.datetime.now()

        for task in tasks:
            task_id, title, _, _, _, deadline, status, _, accepted_at = task

            if status == 'в работе' and accepted_at:
                accepted_time = datetime.datetime.strptime(accepted_at, "%Y-%m-%d %H:%M:%S.%f")
                deadline_time = accepted_time + datetime.timedelta(minutes=deadline)
                remaining = deadline_time - now

                if remaining.total_seconds() < 0:
                    st.sidebar.error(f"🔴 {title}: просрочено!")
                elif remaining.total_seconds() < 1800:
                    st.sidebar.warning(f"⏳ {title}: <30 мин")

            if status == 'не просмотрено':
                created_time = datetime.datetime.strptime(str(task[7]), "%Y-%m-%d %H:%M:%S")
                if (now - created_time).total_seconds() > 600:
                    st.sidebar.info(f"⚠️ {title}: не просмотрено >10 мин")

    st.title("📋 Плановик задач")

    # --- Владелец ---
    if user['role'] == 'owner':
        st.subheader("👤 Управление пользователями")

        with st.expander("➕ Создать нового пользователя"):
            new_username = st.text_input("Логин нового пользователя")
            new_password = st.text_input("Пароль", type="password")
            role = st.selectbox("Роль", ["supervisor", "employee"])

            supervisors = get_supervisors()
            supervisor_names = [f"{id} — {name}" for id, name in supervisors]
            supervisor_id = None
            if role == "employee" and supervisor_names:
                selected = st.selectbox("Назначить руководителя", supervisor_names)
                supervisor_id = int(selected.split(" — ")[0])

            if st.button("Создать пользователя"):
                if new_username and new_password:
                    success = create_user(new_username, new_password, role, supervisor_id)
                    if success:
                        st.success(f"Пользователь '{new_username}' создан")
                        st.rerun()
                    else:
                        st.error("Ошибка при создании пользователя (возможно, логин занят)")
                else:
                    st.warning("Пожалуйста, заполните все поля")

        st.markdown("---")
        st.subheader("📋 Список пользователей")
        users = get_all_users()
        for uid, uname, urole in users:
            st.write(f"👤 {uname} — *{urole}*")

    # --- Руководитель ---
    elif user['role'] == 'supervisor':
        st.subheader("📌 Создать новую задачу")

        employees = get_employees_by_supervisor(user['id'])
        if not employees:
            st.warning("У вас пока нет подчинённых.")
        else:
            emp_dict = {f"{name} (ID {id})": id for id, name in employees}
            selected_emp = st.selectbox("Сотрудник", list(emp_dict.keys()))
            title = st.text_input("Название задачи")
            description = st.text_area("Описание")
            priority = st.slider("Приоритет (1 = срочно, 10 = неважно)", 1, 10, 5)
            deadline = st.number_input("Срок выполнения (в минутах)", min_value=1, step=1)

            uploaded_file = st.file_uploader("Прикрепить изображение", type=["jpg", "jpeg", "png"])
            image_path = None

            if st.button("📤 Отправить задачу"):
                if title and description:
                    if uploaded_file:
                        os.makedirs("tasks", exist_ok=True)
                        file_id = f"{uuid.uuid4()}.png"
                        image_path = os.path.join("tasks", file_id)
                        with open(image_path, "wb") as f:
                            f.write(uploaded_file.read())
                    create_task(
                        creator_id=user['id'],
                        assignee_id=emp_dict[selected_emp],
                        title=title,
                        description=description,
                        image_path=image_path,
                        priority=priority,
                        deadline_minutes=deadline
                    )
                    st.success("Задача отправлена!")
                    st.rerun()
                else:
                    st.warning("Пожалуйста, заполните все поля")

        st.markdown("---")
        st.subheader("📋 Отправленные задачи")
        task_list = get_tasks_created_by_supervisor(user['id'])
        for tid, empname, title, status, priority, created_at in task_list:
            st.markdown(f"""
            🧑‍💼 **{empname}**  
            📌 **{title}**  
            ⏱️ Статус: *{status}* | Приоритет: **{priority}**  
            🕒 Создана: {created_at}
            ---
            """)

        st.markdown("---")
        st.subheader("🔍 Задачи на проверке и ожидании принятия")
        review_tasks = get_tasks_pending_review(user['id'])

        for tid, empname, title, status, priority, created_at in review_tasks:
            st.markdown(f"""
            🧑‍💼 **{empname}**  
            📌 **{title}**  
            ⏱ Статус: *{status}* | Приоритет: **{priority}**  
            🕒 Создана: {created_at}
            """)

            col1, col2 = st.columns(2)
            with col1:
                if status == "на проверке":
                    if st.button(f"✅ Проверено — {tid}", key=f"verify_{tid}"):
                        update_task_status(tid, "выполнено")
                        st.rerun()
            with col2:
                if status == "не просмотрено":
                    if st.button(f"🔔 Напомнить — {tid}", key=f"remind_{tid}"):
                        st.info(f"⏰ Напоминание отправлено сотруднику '{empname}'!")

            st.markdown("---")

    # --- Сотрудник ---
    elif user['role'] == 'employee':
        st.subheader("📥 Мои задачи")

        status_filter = st.selectbox(
            "Фильтр по статусу",
            options=["все", "не просмотрено", "в работе", "на проверке", "выполнено"],
            index=0
        )

        task_placeholder = st.empty()

        def render_tasks():
            all_tasks = get_tasks_for_employee(user['id'])
            tasks = [t for t in all_tasks if status_filter == "все" or t[6] == status_filter]

            if not tasks:
                st.info("У вас пока нет задач по данному фильтру.")
            else:
                for task in tasks:
                    task_id, title, description, image_path, priority, deadline, status, created_at, accepted_at = task

                    deadline_time = None
                    time_left = None
                    if status == 'в работе' and accepted_at:
                        deadline_time = datetime.datetime.strptime(accepted_at, "%Y-%m-%d %H:%M:%S.%f") + datetime.timedelta(minutes=deadline)
                        now = datetime.datetime.now()
                        time_left = deadline_time - now

                        if time_left.total_seconds() > 0:
                            timer_text = f"⏳ До дедлайна: {str(time_left).split('.')[0]}"
                        else:
                            timer_text = "🔴 Дедлайн просрочен!"
                    else:
                        timer_text = "—"

                    st.markdown(f"""
                    ### 📌 {title}
                    📝 {description}  
                    🔴 Приоритет: **{priority}**  
                    ⏱ Статус: *{status}*  
                    📅 Назначена: {created_at}  
                    🕒 {timer_text}
                    """)

                    if image_path and os.path.exists(image_path):
                        st.image(image_path, width=300)

                    col1, col2 = st.columns(2)
                    with col1:
                        if status == 'не просмотрено':
                            if st.button("✅ Принято", key=f"accept_{task_id}"):
                                update_task_status(task_id, "в работе", accepted=True)
                                st.rerun()
                    with col2:
                        if status == 'в работе':
                            if st.button("📤 Выполнено", key=f"done_{task_id}"):
                                update_task_status(task_id, "на проверке", completed=True)
                                st.rerun()
                    st.markdown("---")

        with task_placeholder.container():
            render_tasks()

        time.sleep(1)
        st.rerun()

    else:
        st.warning("Неизвестная роль. Обратитесь к администратору.")
