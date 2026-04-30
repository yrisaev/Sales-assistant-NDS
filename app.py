import streamlit as st

import sqlite3
from datetime import datetime

#Создаем таблицу куда записыват значения логов будем по отработке возражений
conn = sqlite3.connect("assistant.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    objection TEXT,
    client_type TEXT,
    result TEXT,
    timestamp TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS scripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    objection TEXT,
    client_type TEXT,
    script TEXT,
    question TEXT
)
""")


conn.commit()

def get_top_objections(limit=5):
    cursor.execute("""
        SELECT objection, COUNT(*) as cnt
        FROM logs
        GROUP BY objection
        ORDER BY cnt DESC
        LIMIT ?
    """, (limit,))
    
    return [row[0] for row in cursor.fetchall()]

def load_scripts():
    cursor.execute("SELECT objection, client_type, script, question FROM scripts")
    rows = cursor.fetchall()

    scripts_dict = {}

    for objection, client_type, script, question in rows:
        if objection not in scripts_dict:
            scripts_dict[objection] = {}

        scripts_dict[objection][client_type] = {
            "script": script,
            "question": question
        }

    return scripts_dict




















#Само приложение с текстами и выбором вариантов
st.title("AI‑Ассистент менеджера НДС+")


# --- Навигация кнопками ---

if "page" not in st.session_state:
    st.session_state.page = "Ассистент"

st.sidebar.title("Навигация")

if st.sidebar.button("🤖 Ассистент"):
    st.session_state.page = "Ассистент"

if st.sidebar.button("📊 Аналитика"):
    st.session_state.page = "Аналитика"

if st.sidebar.button("🛠 Управление возражениями"):
    st.session_state.page = "Управление возражениями"

page = st.session_state.page







if page == "Ассистент":
    
    # ✅ Инициализация состояния
    if "selected_objection" not in st.session_state:
        st.session_state.selected_objection = None

    # --- База сценариев --- (оставил без изменений)
    scripts = load_scripts()

    if not scripts:
        st.warning("Пока нет добавленных возражений. Добавьте первое 👇")

    # --- ТОП кнопки ---
    st.subheader("🔥 Топ-возражения")

    top_objections = get_top_objections()

    if top_objections:
        cols = st.columns(len(top_objections))

        for i, objection_name in enumerate(top_objections):
            if cols[i].button(objection_name):
                # ИСПРАВЛЕНИЕ: сохраняем и мгновенно перезагружаем страницу
                st.session_state.selected_objection = objection_name
                st.rerun() 
    else:
        st.info("Пока недостаточно данных для топа")

    # --- Поиск ---
    search_query = st.text_input("Введите возражение клиента:")

    matching_objections = [
        key for key in scripts.keys()
        if search_query.lower() in key.lower()
    ]

    if matching_objections:
        # ИСПРАВЛЕНИЕ: Вычисляем, на каком месте в списке стоит выбранное возражение
        default_idx = 0
        if st.session_state.selected_objection in matching_objections:
            default_idx = matching_objections.index(st.session_state.selected_objection)

        selected_from_search = st.selectbox(
            "Выберите подходящее возражение:",
            matching_objections,
            index=default_idx # ИСПРАВЛЕНИЕ: принудительно устанавливаем выбор в списке
        )
        
        # Если менеджер поменял выбор именно в списке — обновляем состояние
        if st.session_state.selected_objection != selected_from_search:
            st.session_state.selected_objection = selected_from_search
            st.rerun()

    # --- Показ отработки ---
    selected_objection = st.session_state.selected_objection

    if selected_objection and selected_objection in scripts: # Добавил проверку на наличие в словаре

        st.divider() # Визуальная черта
        st.subheader(f"Выбрано: {selected_objection}")

        selected_client_type = st.selectbox(
            "Кто ЛПР?",
            ["Бухгалтер", "Директор"]
        )

        selected_script = scripts[selected_objection][selected_client_type]

        st.subheader("Речевой модуль:")
        st.info(selected_script["script"]) # info выглядит симпатичнее

        st.subheader("Усиливающий вопрос:")
        st.success(selected_script["question"]) # success выделяет вопрос зеленым

        # --- Результат звонка ---
        st.subheader("Результат звонка")

        result = st.radio(
            "Чем закончилась обработка?",
            ["Назначена презентация", "Продажа", "Не сработало"]
        )

        if st.button("Сохранить результат"):
            cursor.execute("""
                INSERT INTO logs (objection, client_type, result, timestamp)
                VALUES (?, ?, ?, ?)
            """, (
                selected_objection,
                selected_client_type,
                result,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            
            conn.commit()
            st.success("Результат сохранён ✅")

            st.rerun()

    st.divider()
    st.subheader("➕ Добавить новое возражение")

    new_objection = st.text_input("Текст возражения")
    new_client_type = st.selectbox(
        "Тип клиента",
        ["Бухгалтер", "Директор"],
        key="new_client_type"
    )

    new_script = st.text_area("Речевой модуль")
    new_question = st.text_area("Усиливающий вопрос")

    if st.button("Сохранить новое возражение"):

        if new_objection and new_script and new_question:

            cursor.execute("""
                INSERT INTO scripts (objection, client_type, script, question)
                VALUES (?, ?, ?, ?)
            """, (
                new_objection,
                new_client_type,
                new_script,
                new_question
            ))

            conn.commit()

            st.success("Новое возражение сохранено ✅")

            st.rerun()

        else:
            st.warning("Заполните все поля")












if page == "Аналитика":
    st.title("📊 Аналитика возражений")
    
    # 1. Загружаем данные из базы (теперь берем и timestamp)
    cursor.execute("SELECT objection, result, timestamp FROM logs")
    data = cursor.fetchall()

    if data:
        import pandas as pd
        df = pd.DataFrame(data, columns=["objection", "result", "timestamp"])
        
        # Преобразуем колонку timestamp в формат даты Python
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Создаем колонки для фильтрации
        df['year'] = df['timestamp'].dt.year
        df['month'] = df['timestamp'].dt.month
        df['day'] = df['timestamp'].dt.date # Год-месяц-день

        # --- БЛОК ФИЛЬТРОВ В SIDEBAR ---
        st.sidebar.header("Фильтры")
        
        # Выбор года
        years = sorted(df['year'].unique(), reverse=True)
        selected_year = st.sidebar.multiselect("Год", years, default=years)

        # Выбор месяца
        months = sorted(df['month'].unique())
        selected_month = st.sidebar.multiselect("Месяц (номер)", months, default=months)

        # Выбор диапазона дат
        min_date = df['day'].min()
        max_date = df['day'].max()
        
        st.sidebar.subheader("Диапазон дат")
        date_range = st.sidebar.date_input(
            "Выберите период",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

        # --- ПРИМЕНЕНИЕ ФИЛЬТРОВ ---
        # Проверка, что выбран диапазон (старт и конец)
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            mask = (
                df['year'].isin(selected_year) & 
                df['month'].isin(selected_month) & 
                (df['day'] >= start_date) & 
                (df['day'] <= end_date)
            )
            filtered_df = df.loc[mask]
        else:
            filtered_df = df # Если диапазон не до конца выбран

        # --- ПРОВЕРКА НА ПУСТОТУ ПОСЛЕ ФИЛЬТРОВ ---
        if filtered_df.empty:
            st.warning("В выбранном диапазоне нет данных")
        else:
            # --- ОТОБРАЖЕНИЕ МЕТРИК ---
            total_calls = len(filtered_df)
            presentations = len(filtered_df[filtered_df["result"] == "Назначена презентация"])
            sales = len(filtered_df[filtered_df["result"] == "Продажа"])
            
            total_conv_pres = (presentations / total_calls * 100) if total_calls > 0 else 0
            total_conv_sales = (sales / total_calls * 100) if total_calls > 0 else 0

            m_col1, m_col2, m_col3 = st.columns(3)
            m_col1.metric("Отработок", total_calls)
            m_col2.metric("Конверсия в Презентацию", f"{total_conv_pres:.1f}%")
            m_col3.metric("Конверсия в Оплату", f"{total_conv_sales:.1f}%")

            st.markdown("---")

            # --- ГРАФИКИ ---
            col_left, col_right = st.columns(2)

            with col_left:
                st.subheader("🔥 Популярные возражения")
                st.bar_chart(filtered_df["objection"].value_counts())

            with col_right:
                st.subheader("📈 Эффективность (%)")
                stats = filtered_df.groupby("objection").size()
                pres_stats = filtered_df[filtered_df["result"] == "Назначена презентация"].groupby("objection").size()
                
                # Считаем конверсию для графика
                conv_chart = (pres_stats / stats * 100).fillna(0)
                st.bar_chart(conv_chart)

            # --- ТАБЛИЦА С ДАННЫМИ ---
            with st.expander("Посмотреть отфильтрованные логи"):
                # Показываем таблицу, отсортированную по времени (свежие сверху)
                st.dataframe(filtered_df.sort_values("timestamp", ascending=False), use_container_width=True)

    else:
        st.info("Данных в базе пока нет")
    













if page == "Управление возражениями":

    st.title("🛠 Управление возражениями")

    # Загружаем все скрипты
    cursor.execute("""
        SELECT objection, client_type, script, question
        FROM scripts
        ORDER BY objection
    """)

    rows = cursor.fetchall()

    if not rows:
        st.info("Пока нет добавленных возражений")
    else:
        # Превращаем в словарь
        scripts_dict = {}

        for objection, client_type, script, question in rows:
            if objection not in scripts_dict:
                scripts_dict[objection] = {}
            scripts_dict[objection][client_type] = {
                "script": script,
                "question": question
            }

        # Выбор возражения
        selected_objection = st.selectbox(
            "Выберите возражение",
            list(scripts_dict.keys())
        )

        st.divider()

        st.subheader("👩‍💼 Бухгалтер")

        accountant_script = st.text_area(
            "Речевой модуль (Бухгалтер)",
            scripts_dict[selected_objection]
                .get("Бухгалтер", {})
                .get("script", "")
        )

        accountant_question = st.text_area(
            "Усиливающий вопрос (Бухгалтер)",
            scripts_dict[selected_objection]
                .get("Бухгалтер", {})
                .get("question", "")
        )

        st.divider()

        st.subheader("👨‍💼 Директор")

        director_script = st.text_area(
            "Речевой модуль (Директор)",
            scripts_dict[selected_objection]
                .get("Директор", {})
                .get("script", "")
        )

        director_question = st.text_area(
            "Усиливающий вопрос (Директор)",
            scripts_dict[selected_objection]
                .get("Директор", {})
                .get("question", "")
        )

        st.divider()

        if st.button("💾 Сохранить изменения"):

            # Обновляем бухгалтера
            cursor.execute("""
                UPDATE scripts
                SET script = ?, question = ?
                WHERE objection = ? AND client_type = 'Бухгалтер'
            """, (
                accountant_script,
                accountant_question,
                selected_objection
            ))

            # Обновляем директора
            cursor.execute("""
                UPDATE scripts
                SET script = ?, question = ?
                WHERE objection = ? AND client_type = 'Директор'
            """, (
                director_script,
                director_question,
                selected_objection
            ))

            conn.commit()

            st.toast("✅ Возражение обновлено")

        if st.button("🗑 Удалить возражение полностью"):

            cursor.execute("""
                DELETE FROM scripts
                WHERE objection = ?
            """, (selected_objection,))

            conn.commit()

            st.toast("🧹 Возражение удалено")
            st.rerun()





