import streamlit as st
from transformers import pipeline, AutoModelForTokenClassification, AutoTokenizer
import torch
from modules.config import MODEL_REPO, MODEL_SUBFOLDERS, LOCAL_MODEL_PATHS


@st.cache_resource
def load_ner_model():
    pipelines = {}

    # Определяем устройство: 0 для CUDA, -1 для CPU
    device = 0 if torch.cuda.is_available() else -1

    for group_name, subfolder in MODEL_SUBFOLDERS.items():
        try:

            if LOCAL_MODEL_PATHS:
                model_source = LOCAL_MODEL_PATHS[group_name]
                print(f"Загрузка группы {group_name} из подпапки {subfolder}...")

                pipelines[group_name] = pipeline(
                    "ner",
                    model=model_source,
                    tokenizer=model_source,
                    aggregation_strategy="first",
                    stride=64,
                    device=device
                )
            else:
                model_source = MODEL_REPO
                current_subfolder = subfolder
                print(f"Загрузка группы {group_name} из подпапки {subfolder}...")

                # Загружаем токенайзер
                tokenizer = AutoTokenizer.from_pretrained(
                    model_source,
                    subfolder=current_subfolder
                )

                # Загружаем модель
                model = AutoModelForTokenClassification.from_pretrained(
                    model_source,
                    subfolder=current_subfolder,
                )
                pipelines[group_name] = pipeline(
                    "ner",
                    model=model,
                    tokenizer=tokenizer,
                    aggregation_strategy="first",
                    stride=64,
                    device=device
                )
        except Exception as e:
            st.error(f"Ошибка загрузки группы {group_name} из {subfolder}: {e}")

    return pipelines


def predict_entities(text, pipelines):
    """Предсказание сущностей выбранными моделями (как в твоём инференсе)"""
    all_entities = []

    for group_name, ner_pipe in pipelines.items():
        try:
            entities = ner_pipe(text)

            for entity in entities:
                all_entities.append({
                    'start': entity['start'],
                    'end': entity['end'],
                    'label': entity['entity_group'],
                    'text': entity['word'],
                    'confidence': float(entity['score']),
                    'group': group_name
                })
        except Exception as e:
            st.warning(f"Ошибка в модели {group_name}: {e}")

    # Сортируем по позиции в тексте
    all_entities.sort(key=lambda x: x['start'])
    return all_entities