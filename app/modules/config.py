from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
print(BASE_DIR)
ENTITY_COLORS = {
    # Group 1
    'TIME': '#9254DE',  # фиолетовый
    'LINKS': '#ff4013',  # ярко-оранжевый/красный
    'POSITIONS': '#D3F261',  # салатовый
    'DEGREE': '#5CDBD3',  # бирюзовый
    'LOCATION': '#096DD9',  # синий
    'METRICS': '#FFC069',  # оранжевый

    # Group 2
    'COMPANIES': '#AD8B00',  # оливковый
    'TECHNOLOGIES': '#9a244f',  # бордовый
    'NAME': '#263e0f',  # тёмно-зелёный

    # Group 3
    'RESPONSIBILITIES': '#F759AB',  # розовый
    'EDUCATION': '#389E0D',  # зелёный
    'SKILLS': '#FFA39E',  # персиковый/светло-розовый
    'PROJECTS': '#006d8f',  # тёмно-синий
    'ACHIEVEMENTS': '#00364a',  # очень тёмный синий
    'CONTACTS': '#ADC6FF'  # светло-синий
}

ENTITY_GROUPS = {
    'Group 1 (Стандартные)': ['TIME', 'LINKS', 'POSITIONS', 'DEGREE', 'LOCATION', 'METRICS'],
    'Group 2 (Компании/Технологии)': ['COMPANIES', 'TECHNOLOGIES', 'NAME'],
    'Group 3 (Прочее)': ['RESPONSIBILITIES', 'EDUCATION', 'SKILLS', 'PROJECTS', 'ACHIEVEMENTS', 'CONTACTS']
}

MODEL_REPO = "Zirok05/ner_russian_it_resumes"

MODEL_SUBFOLDERS = {
    'group1': 'model_1',
    'group2': 'model_2',
    'group3': 'model_3'
}

LOCAL_MODEL_PATHS = {
    'group1': str(BASE_DIR / 'models' / 'model_1_final'),
    'group2': str(BASE_DIR / 'models' / 'model_2_final'),
    'group3': str(BASE_DIR / 'models' / 'model_3_final')
}

EXAMPLES_FILE = 'app/data/examples.csv'


