from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
import psycopg2
from psycopg2.extras import RealDictCursor
from db_config import DB_CONFIG 
from werkzeug.security import generate_password_hash, check_password_hash
import os, datetime, jwt

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    # Проверяем, авторизован ли пользователь
    if "user_id" in session:
        username = session["username"]
        return render_template("index.html", username=username, authorized=True)
    else:
        return render_template("index.html", authorized=False)


app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static')

def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn

# Путь для отдачи файлов
@app.route('/static/<path:filename>')
def serve_static_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

app.secret_key = "87e6023616c1ef012b9a6a63316d17a6264b32f582f94019faf9a4f5355e3b8b"
SECRET_KEY = "81df54d73c6325c24dea59de2ef92d05fc649aefc661bcaf7882000a3d9a2068"

@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")  # Страница логин

@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        login = data.get("login")
        password = data.get("password")

        if not login or not password:
            return jsonify({"error": "Логин и пароль обязательны!"}), 400

        # Проверка пользователя в базе
        query = "SELECT * FROM users WHERE login = %s"
        user = execute_query(query, (login,))
        if not user:
            return jsonify({"error": "Пользователь не найден!"}), 404

        user = user[0]

        # Проверка пароля
        if not check_password_hash(user["password"], password):
            return jsonify({"error": "Неверный пароль!"}), 401

        # Установка сессии пользователя
        session["user_id"] = user["id"]
        session["username"] = user["login"]

        return jsonify({"message": "Успешный вход!"}), 200

    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({"error": "Ошибка сервера"}), 500

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.png', mimetype='image/png')

def execute_query(query, params=None):
    """Выполнение SQL-запроса с параметрами."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(query, params)

        # Проверяем, является ли запросом типа SELECT
        if query.strip().lower().startswith("select"):
            results = cursor.fetchall()  # Для SELECT получаем результаты
        else:
            conn.commit()  # Для остальных запросов фиксируем изменения
            results = None  # Нет результатов для возврата

        print("Запрос выполнен успешно:", query)
        return results
    except Exception as e:
        print(f"Ошибка: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# Регистрация
@app.route("/registration", methods=["GET", "POST"])
def registration():
    if request.method == "POST":
        # Получаем данные из запроса
        data = request.get_json()
        login = data.get("login")
        password = data.get("password")

        # Проверка, что поля не пустые
        if not login or not password:
            return jsonify({"error": "Логин и пароль обязательны!"}), 400

        # Хешируем пароль
        hashed_password = generate_password_hash(password)

        # SQL-запрос для добавления нового пользователя
        query = """
        INSERT INTO public.users (carsid, login, password)
        VALUES (NULL, %s, %s)
        """
        params = (login, hashed_password)

        # Выполнение запроса
        try:
            execute_query(query, params)
            return jsonify({"message": "Регистрация успешна!"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return render_template("registration.html")

@app.route("/search/cars", methods=["POST"])
def search_cars():
    """Обработка POST-запроса для поиска автомобилей с необязательными фильтрами."""
    if not request.is_json:
        return jsonify({"error": "Invalid Content-Type. Expected application/json."}), 415

    data = request.get_json()

    # Инициализируем базовый SQL-запрос
    base_query = """
    SELECT *
    FROM cars
    WHERE videolink IS NOT NULL
      AND photo IS NOT NULL
    """
    conditions = []  # Условия для фильтрации
    params = []  # Параметры для подстановки
      
    # Динамически добавляем условия
    if "brandname" in data and data["brandname"]:
        conditions.append("brandname @> ARRAY[%s]::character varying[]")
        params.append(data["brandname"])

    if "modelname" in data and data["modelname"]:
        conditions.append("modelname @> ARRAY[%s]::character varying[]")
        params.append(data["modelname"])

    if "bodytype" in data and data["bodytype"]:
        conditions.append("bodytype @> ARRAY[%s]::character varying[]")
        params.append(data["bodytype"])

    if "typedrive" in data and data["typedrive"]:
        conditions.append("typedrive @> ARRAY[%s]::character varying[]")
        params.append(data["typedrive"])

    if "colorcar" in data and data["colorcar"]:
        conditions.append("colorcar @> ARRAY[%s]::character varying[]")
        params.append(data["colorcar"])

    if "transmissiontype" in data and data["transmissiontype"]:
        conditions.append("transmissiontype @> ARRAY[%s]::character varying[]")
        params.append(data["transmissiontype"])

    # Проверка для enginecapacity
    if "enginecapacity" in data and data["enginecapacity"]:
        conditions.append("enginecapacity <= %s")  # Ищем значения меньше или равные переданному значению
        params.append(data["enginecapacity"])

    # Проверка для enginepower
    if "enginepower" in data and data["enginepower"]:
        conditions.append("enginepower <= %s")  # Ищем значения меньше или равные переданному значению
        params.append(data["enginepower"])

    if "year-from" in data and data["year-from"] and "year-to" in data and data["year-to"]:
        # Преобразуем строки в формат даты (начало и конец года)
        year_from = f"{data['year-from']}-01-01"
        year_to = f"{data['year-to']}-12-31"
        
        # Добавляем условие для yearrelease (между двумя датами)
        conditions.append("yearrelease BETWEEN %s AND %s")
        params.extend([year_from, year_to])

    if "countryorigin" in data and data["countryorigin"]:
        conditions.append("countryorigin @> ARRAY[%s]::character varying[]")
        params.append(data["countryorigin"])

    # Проверка для highway
    if "highway" in data and data["highway"]:
        conditions.append("highway @> ARRAY[%s]::numeric[] OR EXISTS (SELECT 1 FROM unnest(highway) AS h WHERE h <= %s)")
        params.extend([data["highway"], data["highway"]])  # Добавляем значение дважды, так как оно используется в двух частях условия

    # Проверка для city
    if "city" in data and data["city"]:
        conditions.append("city @> ARRAY[%s]::numeric[] OR EXISTS (SELECT 1 FROM unnest(city) AS c WHERE c <= %s)")
        params.extend([data["city"], data["city"]])  # Добавляем значение дважды


    if "fueltype" in data and data["fueltype"]:
        conditions.append("fueltype @> ARRAY[%s]::character varying[]")
        params.append(data["fueltype"])

    # Логика для wheellocation
    if "wheellocation" in data and data["wheellocation"] is not None:
        # Добавляем фильтр только если передан
        conditions.append("wheellocation = %s")
        params.append(data["wheellocation"])

    # Объединяем условия с базовым запросом
    if conditions:
        base_query += " AND " + " AND ".join(conditions)

    # Добавляем сортировку
    base_query += " ORDER BY yearrelease ASC;"

    # Выполняем запрос
    try:
        results = execute_query(base_query, params)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/favorites", methods=["GET"])
def favorites():
    if "user_id" not in session:
        return redirect(url_for("login_page"))  # Перенаправляем на страницу логина

    user_id = session["user_id"]
    username = session["username"]

    # Пример: заглушка для запроса избранных машин из БД
    query = "SELECT * FROM cars WHERE id = ANY (SELECT UNNEST(carsid) FROM users WHERE id = %s)"
    favorites = execute_query(query, (user_id,))  # Получаем избранные машины

    return render_template("favorites.html", username=username, favorites=favorites)

# Выход из системы
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5454, debug=True)



