import streamlit as st
import pandas as pd
import random
from pathlib import Path
import sys
from modules.config import ENTITY_COLORS, ENTITY_GROUPS, MODEL_REPO, MODEL_SUBFOLDERS, EXAMPLES_FILE
from modules.models import load_ner_model, predict_entities
from modules.visualization import color_text, hex_to_rgba, escape_html

# Добавляем пути для импорта модулей (актуально для локального запуска и деплоя)
sys.path.append(str(Path(__file__).parent))

def load_examples(file_path):
    """Загружает примеры резюме из CSV"""
    print(f"Loading examples from {file_path}")
    try:
        p = Path(file_path)
        print(p)
        if not p.exists():
            st.warning(f"Файл с примерами не найден: {file_path}")
        df = pd.read_csv(file_path)
        return df.to_dict('records')
    except Exception as e:
        st.error(f"Ошибка загрузки примеров: {e}")
        return []


def main():
    st.set_page_config(
        page_title="NER для IT-резюме",
        page_icon="📄",
        layout="wide"
    )

    st.title("🔍 Распознавание сущностей в IT-резюме")
    st.markdown("Загрузите своё резюме или выберите пример, чтобы увидеть, как модель выделяет сущности.")

    # Инициализация состояния сессии
    if 'input_text' not in st.session_state:
        st.session_state['input_text'] = ""
    if 'entities' not in st.session_state:
        st.session_state['entities'] = []
    if 'input_source' not in st.session_state:
        st.session_state['input_source'] = ""

    # Сайдбар
    with st.sidebar:
        st.header("⚙️ Настройки")

        st.subheader("Модели")
        use_g1 = st.checkbox("Group 1 (Стандартные)", value=True)
        use_g2 = st.checkbox("Group 2 (Компании/Технологии)", value=True)
        use_g3 = st.checkbox("Group 3 (Опыт/Навыки)", value=True)

        st.divider()
        st.subheader("🎨 Легенда")
        for group_name, entities in ENTITY_GROUPS.items():
            with st.expander(group_name, expanded=False):
                cols = st.columns(2)
                for i, entity in enumerate(entities):
                    with cols[i % 2]:
                        color = ENTITY_COLORS.get(entity, '#D3D3D3')
                        rgba = hex_to_rgba(color, alpha=0.5)
                        st.markdown(
                            f'<span style="background-color: {rgba}; padding: 2px 8px; border-radius: 3px; font-size: 12px;">{entity}</span>',
                            unsafe_allow_html=True
                        )

    # Загрузка моделей
    active_groups = []
    if use_g1: active_groups.append('group1')
    if use_g2: active_groups.append('group2')
    if use_g3: active_groups.append('group3')

    if not active_groups:
        st.warning("⚠️ Выберите хотя бы одну группу моделей в сайдбаре.")
        st.stop()

    # Загружаем модели
    # Мы не передаем аргументы, так как функция сама возьмет всё из config.py
    with st.spinner("🔄 Инициализация нейросетей..."):
        all_pipelines = load_ner_model()
        # Оставляем только те, что выбраны пользователем
        pipelines = {k: v for k, v in all_pipelines.items() if k in active_groups}

    # Загружаем примеры
    examples = load_examples(EXAMPLES_FILE)
    print(examples)
    # Кнопки Управления
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🎲 Случайный пример", use_container_width=True):
            if examples:
                ex = random.choice(examples)
                st.session_state['input_text'] = ex['text']
                st.session_state['input_source'] = f"Пример: {ex.get('title', 'Без названия')}"
                st.session_state['entities'] = []
                st.rerun()

    with col2:
        if st.button("🧹 Очистить", use_container_width=True):
            st.session_state['input_text'] = ""
            st.session_state['entities'] = []
            st.session_state['input_source'] = ""
            st.rerun()

    with col3:
        if st.button("🔄 Обновить", use_container_width=True):
            st.rerun()

    # Поле ввода
    text = st.text_area(
        "📝 Текст резюме:",
        value=st.session_state['input_text'],
        height=300,
        placeholder="Вставьте текст или выберите пример..."
    )

    if text != st.session_state['input_text']:
        st.session_state['input_text'] = text
        st.session_state['entities'] = []

    analyze_button = st.button("🔍 Анализировать", type="primary", use_container_width=True)

    # Обработка
    if analyze_button and text.strip():
        with st.spinner("🧠 Модели изучают ваше резюме..."):
            entities = predict_entities(text, pipelines)
            st.session_state['entities'] = entities

        st.subheader("📊 Результаты")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Найдено сущностей", len(entities))
        with c2:
            conf = sum(e['confidence'] for e in entities) / len(entities) if entities else 0
            st.metric("Уверенность", f"{conf:.2f}")
        with c3:
            st.metric("Источник", st.session_state.get('input_source', 'Ввод вручную'))

        if entities:
            st.subheader("📄 Визуализация")
            colored_html = color_text(text, entities, ENTITY_COLORS)

            st.markdown(
                f'<div style="background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #eee; line-height: 2.0; color: black;">{colored_html}</div>',
                unsafe_allow_html=True
            )

            with st.expander("📋 Посмотреть таблицу всех найденных тегов"):
                df_data = [{
                    'Текст': e['text'],
                    'Тип': e['label'],
                    'Группа': e['group'],
                    'Уверенность': round(e['confidence'], 3)
                } for e in entities]
                st.dataframe(pd.DataFrame(df_data), use_container_width=True)
        else:
            st.info("Сущности не обнаружены. Попробуйте другой текст или включите все группы моделей.")

    # Информация
    with st.expander("ℹ️ Подробнее о системе"):
        st.write(f"**Репозиторий моделей:** `{MODEL_REPO}`")
        st.write(
            "Система использует три независимых NER-модели. Если сущности пересекаются, цвета накладываются друг на друга (эффект слоев).")


if __name__ == "__main__":
    main()
# streamlit run app/main.py