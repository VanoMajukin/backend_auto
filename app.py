from flask import Flask, render_template, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from db_config import DB_CONFIG 

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

def execute_query(query, params):
    try:
        conn = psycopg2.connect(**DB_CONFIG)  # Используем DB_CONFIG
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params)
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"Ошибка: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/search", methods=["POST"])
def search():
    # Получаем параметры из запроса
    data = request.get_json()
    brand = data.get("brand", None)
    model = data.get("model", None)
    min_price = data.get("min_price", 0)
    max_price = data.get("max_price", 10**9)
    year = data.get("year", None)

    # SQL-запрос
    query = """
    SELECT brand, model, price, year
    FROM cars
    WHERE (brand ILIKE %s OR %s IS NULL)
      AND (model ILIKE %s OR %s IS NULL)
      AND (price BETWEEN %s AND %s)
      AND (year = %s OR %s IS NULL)
    ORDER BY price ASC;
    """
    params = (
        f"%{brand}%", brand,
        f"%{model}%", model,
        min_price, max_price,
        year, year
    )

    # Выполняем запрос
    results = execute_query(query, params)
    return jsonify(results)



if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5454, debug=True)



