from flask import Flask, render_template, request, jsonify
from db_config import get_db_connection

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/search", methods=["POST"])
def search():
    # Получаем параметры из запроса
    budget = request.form.get("budget")
    car_type = request.form.get("type")
    year = request.form.get("year")

    # Формируем запрос к базе данных
    query = """
        SELECT model, price, year, description
        FROM cars
        WHERE price <= %s AND car_type = %s AND year >= %s
        LIMIT 20;
    """
    params = (budget, car_type, year)

    # Выполняем запрос
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            results = cur.fetchall()
        conn.close()
        return jsonify(results)  # Отправляем данные клиенту
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
