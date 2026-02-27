import json
from pathlib import Path


def extract_text_from_resume(resume_json):
    """Извлекает связный текст из объекта резюме HH.ru"""
    parts = []
    data = resume_json

    # 1. ФИО и заголовок
    name_parts = [data.get('last_name'), data.get('first_name'), data.get('middle_name')]
    full_name = ' '.join([n for n in name_parts if n])
    if full_name:
        parts.append(f"Кандидат: {full_name}")
    if data.get('title'):
        parts.append(f"Целевая должность: {data['title']}")
    parts.append("")

    # 2. Раздел "Обо мне"
    if data.get('skills'):
        parts.append("ОБО МНЕ:")
        parts.append(data['skills'])
        parts.append("")

    # 3. Опыт работы
    if data.get('experience') and isinstance(data['experience'], list):
        parts.append("ОПЫТ РАБОТЫ:")
        for exp in data['experience']:
            position = exp.get('position', 'Должность не указана')
            company = exp.get('company', 'Компания не указана')
            start = exp.get('start', '')
            end = exp.get('end', 'по настоящее время')
            duration = f" ({start} — {end})" if start else ""
            exp_line = f"- {position}, {company}{duration}"
            parts.append(exp_line)

            description = exp.get('description')
            if description:
                parts.append(f"  {description}")
        parts.append("")

    # 4. Образование
    if data.get('education'):
        parts.append("ОБРАЗОВАНИЕ:")
        edu = data['education']
        for higher in edu.get('higher', []):
            name = higher.get('name', '')
            year = higher.get('year', '')
            if name:
                edu_line = f"- {name}"
                if year:
                    edu_line += f" ({year} г.)"
                parts.append(edu_line)
        parts.append("")

    # 5. Навыки
    if data.get('skill_set'):
        parts.append(f"КЛЮЧЕВЫЕ НАВЫКИ: {', '.join(data['skill_set'])}")

    return "\n".join(parts)


def save_resumes_from_json(json_file, output_folder):
    """
    Читает JSON с hh.ru, применяет extract_text_from_resume,
    сохраняет в .txt и переименовывает исходный JSON в *_use.json
    """
    json_path = Path(json_file)

    # Загружаем JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        resumes = json.load(f)

    print(f"Загружено {len(resumes)} резюме из {json_path.name}")

    # Создаём выходную папку, если нужно
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    for i, resume in enumerate(resumes):
        # Извлекаем текст
        text = extract_text_from_resume(resume.get('raw', resume))

        # Сохраняем в .txt
        resume_id = resume.get('id', f"resume_{i:04d}")
        filepath = output_path / f"{resume_id}.txt"

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)

        if (i + 1) % 10 == 0:
            print(f"Сохранено {i + 1}/{len(resumes)}")

    # Переименовываем исходный JSON
    new_json_path = json_path.with_name(json_path.stem + "_used" + json_path.suffix)
    json_path.rename(new_json_path)

    print(f"\nГотово! {len(resumes)} файлов сохранено в {output_folder}")
    print(f"JSON переименован в: {new_json_path.name}")


import hashlib
from pathlib import Path


def deduplicate_txt_folder(folder_path):
    """
    Проходит по ВСЕМ .txt файлам в папке и удаляет дубликаты по содержимому
    """
    folder = Path(folder_path)
    if not folder.exists():
        print(f"Папка {folder_path} не найдена")
        return

    # Собираем все .txt файлы
    txt_files = list(folder.glob("*.txt"))
    print(f"Найдено {len(txt_files)} .txt файлов")

    # Словарь: хэш -> имя первого файла
    unique_hashes = {}
    duplicates_count = 0
    kept_count = 0

    for filepath in sorted(txt_files):  # сортируем для предсказуемости
        # Читаем содержимое
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Создаём хэш от содержимого (без учёта пробелов и регистра)
        clean_content = ' '.join(content.lower().split())
        content_hash = hashlib.md5(clean_content.encode()).hexdigest()

        if content_hash in unique_hashes:
            # Дубликат — удаляем
            filepath.unlink()
            duplicates_count += 1
            print(f"🗑️ Удалён дубликат: {filepath.name} (совпадает с {unique_hashes[content_hash]})")
        else:
            # Уникальный — запоминаем
            unique_hashes[content_hash] = filepath.name
            kept_count += 1

    print(f"\nИтоги:")
    print(f"Оставлено уникальных: {kept_count}")
    print(f"Удалено дубликатов: {duplicates_count}")
    print(f"Папка: {folder.absolute()}")

    return kept_count, duplicates_count


import json
from pathlib import Path


def create_label_studio_json(txt_folder="resumes_json/converted",
                             output_folder="resumes_json/for_label_studio"):
    """
    Собирает ВСЕ .txt из converted/ в один JSON для Label Studio
    """
    txt_folder = Path(txt_folder)
    output_folder = Path(output_folder)


    # Собираем все .txt файлы
    txt_files = list(txt_folder.glob("*.txt"))
    total_files = len(txt_files)

    print(f"Найдено {total_files} .txt файлов")

    if total_files == 0:
        print("Нет файлов для обработки")
        return

    # Создаём один большой JSON
    tasks = []
    for txt_file in txt_files:
        with open(txt_file, 'r', encoding='utf-8') as f:
            text = f.read()

        tasks.append({
            "data": {
                "text": text,
                "source": txt_file.name
            }
        })

    # Сохраняем
    output_file = output_folder / f"label_studio_all_{total_files}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

    print(f"JSON файл: {output_file.name} ({total_files} резюме)")
    print(f"Путь: {output_file.absolute()}")




# Использование:
#save_resumes_from_json("resumes_json/raw/it_resumes_20260226_153906.json", "resumes_json/converted")

# deduplicate_txt_folder("resumes_json/converted")
#
# create_label_studio_json()