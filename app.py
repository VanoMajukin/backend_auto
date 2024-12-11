from flask import Flask, render_template, request, jsonify, send_from_directory
import psycopg2
from psycopg2.extras import RealDictCursor
from db_config import DB_CONFIG 

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

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
    """Обработка POST-запроса для поиска автомобилей."""
    try:
        if not request.is_json:
            return jsonify({"error": "Invalid Content-Type. Expected application/json."}), 415

        data = request.get_json()

        # Преобразуем данные в массивы
        def ensure_list(value):
            if value and not isinstance(value, list):
                return [value]
            return value

        brandname = ensure_list(data.get("brandname"))
        modelname = ensure_list(data.get("modelname"))
        bodytype = ensure_list(data.get("bodytype"))
        typedrive = ensure_list(data.get("typedrive"))
        colorcar = ensure_list(data.get("colorcar"))
        enginecapacity = data.get("enginecapacity")
        enginepower = data.get("enginepower")
        year_from = data.get("year_from")
        year_to = data.get("year_to")

        # SQL-запрос
        query = """
        SELECT *
        FROM cars
        WHERE (brandname @> %s OR %s IS NULL)
        AND (modelname @> %s OR %s IS NULL)
        AND (bodytype @> %s OR %s IS NULL)
        AND (typedrive @> %s OR %s IS NULL)
        AND (colorcar @> %s OR %s IS NULL)
        AND (enginecapacity = %s OR %s IS NULL)
        AND (enginepower = %s OR %s IS NULL)
        AND (yearrelease BETWEEN %s AND %s OR (%s IS NULL AND %s IS NULL))
        AND videolink IS NOT NULL
        AND photo IS NOT NULL
        AND wheellocation IS NOT NULL
        ORDER BY yearrelease ASC;
        """


        params = (
            brandname, brandname,
            modelname, modelname,
            bodytype, bodytype,
            typedrive, typedrive,
            colorcar, colorcar,
            enginecapacity, enginecapacity,
            enginepower, enginepower,
            year_from, year_to, year_from, year_to
        )

        results = execute_query(query, params)
        return jsonify(results)

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

    
if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5454, debug=True)



