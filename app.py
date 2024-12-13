from flask import Flask, render_template, request, jsonify, send_from_directory
import psycopg2
from psycopg2.extras import RealDictCursor
from db_config import DB_CONFIG 

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/registration")
def registration():
    return render_template("registration.html")

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.png', mimetype='image/png')

def execute_query(query, params):
    """Выполнение SQL-запроса с параметрами."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params)
        results = cursor.fetchall()
        print(results)
        return results
    except Exception as e:
        print(f"Ошибка: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

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

    if "enginecapacity" in data and data["enginecapacity"]:
        conditions.append("enginecapacity = %s")
        params.append(data["enginecapacity"])

    if "enginepower" in data and data["enginepower"]:
        conditions.append("enginepower = %s")
        params.append(data["enginepower"])

    if "year_from" in data and data["year_from"] and "year_to" in data and data["year_to"]:
        conditions.append("yearrelease BETWEEN %s AND %s")
        params.extend([data["year_from"], data["year_to"]])
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

    
if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5454, debug=True)



