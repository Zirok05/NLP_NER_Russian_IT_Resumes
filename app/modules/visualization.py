def color_text(text, entities, entity_colors):
    """
    Реализует вложенную подсветку (как в Label Studio).
    Разбивает текст на сегменты по точкам начала и конца всех сущностей.
    """
    if not entities:
        return escape_html(text)

    # 1. Собираем все уникальные точки разреза текста
    stops = set([0, len(text)])
    for e in entities:
        stops.add(e['start'])
        stops.add(e['end'])

    sorted_stops = sorted(list(stops))

    # 2. Для каждого интервала между точками разреза ищем подходящие сущности
    html_segments = []
    for i in range(len(sorted_stops) - 1):
        start, end = sorted_stops[i], sorted_stops[i + 1]
        segment_text = text[start:end]

        if not segment_text:
            continue

        # Ищем все сущности, которые покрывают этот интервал
        matched_entities = [
            e for e in entities
            if e['start'] <= start and e['end'] >= end
        ]

        # Экранируем текст сегмента
        safe_text = escape_html(segment_text)

        if not matched_entities:
            html_segments.append(safe_text)
        else:
            # Сортируем сущности для стабильного порядка (например, по длине)
            # Чтобы вложенность была предсказуемой
            matched_entities.sort(key=lambda x: (x['end'] - x['start']), reverse=True)

            # Оборачиваем текст в слои span
            opening_tags = ""
            closing_tags = ""
            for e in matched_entities:
                color = entity_colors.get(e['label'], '#D3D3D3')
                rgba = hex_to_rgba(color, alpha=0.5)  # Используем прозрачность
                title = f"{e['label']} ({e['confidence']:.2f})"

                # Добавляем стиль для визуального разделения вложенных элементов
                opening_tags += f'<span style="background-color: {rgba}; border-bottom: 2px solid {color}; padding: 1px 0;" title="{title}">'
                closing_tags += '</span>'

            html_segments.append(f'{opening_tags}{safe_text}{closing_tags}')

    return "".join(html_segments)

def hex_to_rgba(hex_color, alpha=0.3):
    """Преобразует HEX в RGBA строку"""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f'rgba({r}, {g}, {b}, {alpha})'

def escape_html(text):
    """Заменяет проблемные символы на безопасные аналоги"""
    text = text.replace('«', '"')
    text = text.replace('»', '"')
    text = text.replace('—', '-')
    text = text.replace('–', '-')
    text = text.replace('…', '...')

    return (text.replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))
