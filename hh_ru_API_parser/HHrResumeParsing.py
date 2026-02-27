import requests
import time
import os
import json
from datetime import datetime
from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)

# === КОНФИГУРАЦИЯ ===
CLIENT_ID = "Your Client ID"
CLIENT_SECRET = "Your Client Secret"
REDIRECT_URI = "http://127.0.0.1:5000/callback"

TOKEN_FILE = "user_token.json"
# RESUMES_FILE = "it_resumes.json"

# Папка для сохранения резюме
RESUMES_FOLDER = "resumes_json/raw/"
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
RESUMES_FILE = os.path.join(RESUMES_FOLDER, f"it_resumes_{timestamp}.json")

N_RESUMES = 100

# === HTML ИНТЕРФЕЙС ===
HTML = """
<!DOCTYPE html>
<html>
<body style="padding: 20px; font-family: Arial;">
    <h2>📊 Сбор IT-резюме</h2>

    {% if not token %}
    <a href="/login">
        <button style="padding: 12px 24px; background: #FF6600; color: white; border: none; border-radius: 4px; font-size: 16px;">
            🔑 Войти через HH.ru
        </button>
    </a>
    {% else %}
    <a href="/collect_resumes">
        <button style="padding: 12px 24px; background: #4CAF50; color: white; border: none; border-radius: 4px; font-size: 16px;">
            🚀 Собрать IT-резюме
        </button>
    </a>
    {% endif %}

    {% if message %}
    <div style="margin-top: 20px; padding: 15px; background: #e8f5e9; border-radius: 5px;">
        {{ message }}
    </div>
    {% endif %}
</body>
</html>
"""


# === АВТОРИЗАЦИЯ ===
@app.route('/login')
def login():
    auth_url = f"https://hh.ru/oauth/authorize?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&state=hh_parser"
    return redirect(auth_url)


@app.route('/callback')
def callback():
    code = request.args.get('code')

    if not code:
        return "Нет кода авторизации"

    token_url = "https://api.hh.ru/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.post(token_url, data=data, headers=headers)

    if response.status_code == 200:
        token_data = response.json()
        token_data['saved_at'] = time.time()

        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f)

        return redirect('/?msg=Авторизация успешна!')
    else:
        return f"Ошибка: {response.status_code}"


# === ЗАГРУЗКА ТОКЕНА ===
def load_token():
    try:
        with open(TOKEN_FILE, 'r') as f:
            data = json.load(f)

        saved_at = data.get('saved_at', 0)
        expires_in = data.get('expires_in', 1209600)

        if time.time() - saved_at < expires_in - 3600:
            return data['access_token']
    except:
        pass
    return None


# === ГЛАВНАЯ СТРАНИЦА ===
@app.route('/')
def home():
    token = load_token()
    return render_template_string(HTML, token=token, message=request.args.get('msg', ''))


# === ПРОСТОЙ СБОР РЕЗЮМЕ ===
@app.route('/collect_resumes')
def collect_resumes():
    token = load_token()
    if not token:
        return redirect('/login')

    headers = {"Authorization": f"Bearer {token}"}

    # Простые запросы
    queries = [
        ("ML", "машинное обучение"),
        ("Data Science", "data scientist"),
        ("Python", "python разработчик"),
        ("Backend", "backend разработчик")
    ]

    all_resumes = []
    today = datetime.now().strftime("%Y-%m-%d")

    print("=" * 60)
    print("Начинаем сбор...")

    for query_name, query_text in queries:
        if len(all_resumes) >= N_RESUMES:
            break

        print(f"\n{query_name}")

        # ПРОСТОЙ запрос
        params = {
            "text": query_text,
            "per_page": N_RESUMES // 4,
            "page": 0
        }

        try:
            response = requests.get("https://api.hh.ru/resumes", headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])

                print(f"   Найдено: {len(items)}")

                for item in items:
                    if len(all_resumes) >= N_RESUMES:
                        break

                    resume_id = item.get('id')
                    print(f"   [{len(all_resumes) + 1}/{N_RESUMES}] ID: {resume_id}")

                    # Простая функция получения резюме
                    resume_details = get_resume_full(resume_id, headers)
                    if resume_details:
                        resume_details['query'] = query_name
                        resume_details['date'] = today
                        all_resumes.append(resume_details)

                    time.sleep(0.2)
            else:
                print(f"Ошибка: {response.status_code}")

        except Exception as e:
            print(f"Ошибка: {e}")

    # Сохраняем
    if all_resumes:
        try:
            with open(RESUMES_FILE, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        except:
            existing = []

        existing.extend(all_resumes)

        with open(RESUMES_FILE, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)

        print(f"\nСобрано: {len(all_resumes)} резюме")
        return redirect(f'/?msg=Собрано {len(all_resumes)} резюме')

    return redirect('/?msg=Не собрано резюме')


def get_resume_full(resume_id, headers):
    try:
        response = requests.get(f"https://api.hh.ru/resumes/{resume_id}", headers=headers, timeout=10)
        data = response.json()

        # Собираем ВСЕ текстовые поля
        text_parts = []

        # Добавляем все строковые поля
        for key, value in data.items():
            if isinstance(value, str) and value.strip():
                text_parts.append(f"{key.upper()}: {value}")
            elif isinstance(value, list) and value:
                text_parts.append(f"{key.upper()}: {', '.join(str(v) for v in value)}")

        return {
            "id": resume_id,
            "text": "\n".join(text_parts),  # Всё в одном тексте
            "raw": data
        }
    except:
        return None

# === ЗАПУСК ===
if __name__ == '__main__':
    print("=" * 60)
    print("Сбор IT-резюме HH.ru")
    print("=" * 60)
    print("Откройте: http://127.0.0.1:5000")
    print("=" * 60)

    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)