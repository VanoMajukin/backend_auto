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
        return results
    except Exception as e:
        print(f"Ошибка: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/", methods=["GET"])
def search():
    """Обработка поискового запроса."""
    data = request.get_json(force=True)
    
    # Извлечение диапазона годов
    year_from = data.get("year-from")
    year_to = data.get("year-to")

    # Остальные параметры
    brandname = data.get("brandname")
    modelname = data.get("modelname")
    bodytype = data.get("bodytype")
    typedrive = data.get("typedrive")
    transmissiontype = data.get("transmissiontype")
    countryorigin = data.get("countryorigin")
    colorcar = data.get("colorcar")
    enginecapacity = data.get("enginecapacity")
    enginepower = data.get("enginepower")
    highway = data.get("highway")
    city = data.get("city")
    fueltype = data.get("fueltype")

    # SQL-запрос
    query = """
    SELECT *
    FROM cars
    WHERE (brandname = %s OR %s IS NULL)
      AND (modelname = %s OR %s IS NULL)
      AND (bodytype = %s OR %s IS NULL)
      AND (typedrive = %s OR %s IS NULL)
      AND (transmissiontype = %s OR %s IS NULL)
      AND (countryorigin = %s OR %s IS NULL)      
      AND (colorcar = %s OR %s IS NULL)
      AND (enginecapacity = %s OR %s IS NULL)
      AND (enginepower = %s OR %s IS NULL)
      AND (highway = %s OR %s IS NULL)
      AND (city = %s OR %s IS NULL)
      AND (fueltype = %s OR %s IS NULL)
      AND (yearrelease BETWEEN %s AND %s OR (%s IS NULL AND %s IS NULL))
      AND videolink IS NOT NULL
      AND photo IS NOT NULL
      AND wheellocation IS NOT NULL
    ORDER BY yearrelease ASC;
    """

    # Параметры для SQL-запроса
    params = (
        brandname, brandname,
        modelname, modelname,
        bodytype, bodytype,
        typedrive, typedrive,
        transmissiontype, transmissiontype,
        countryorigin, countryorigin,
        colorcar, colorcar,
        enginecapacity, enginecapacity,
        enginepower, enginepower,
        highway, highway,
        city, city,
        fueltype, fueltype,
        year_from, year_to, year_from, year_to
    )

    # Выполняем запрос
    results = execute_query(query, params)
    return jsonify(results)

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5454, debug=True)



