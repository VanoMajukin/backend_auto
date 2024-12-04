import psycopg2
from psycopg2.extras import RealDictCursor

DB_PARAMS = {
    "dbname": "backend_auto",
    "user": "backend",
    "password": "MIS_2104",
    "host": "localhost",
    "port": 5432
}

def get_db_connection():
    """Создаёт соединение с базой данных."""
    conn = psycopg2.connect(**DB_PARAMS)
    return conn
