import os
import psycopg2
from psycopg2 import sql, OperationalError
from dotenv import load_dotenv

load_dotenv()

def create_database_if_not_exists():
    """Connect to default 'postgres' database and create pharmacy_db if missing."""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            dbname='postgres',
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', '')
        )
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (os.getenv('DB_NAME', 'pharmacy_db'),))
            exists = cur.fetchone()
            if not exists:
                cur.execute(sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(os.getenv('DB_NAME', 'pharmacy_db'))
                ))
                print("Database created.")
        conn.close()
    except Exception as e:
        print(f"Error creating database: {e}")

def get_connection():
    """Return a connection to the pharmacy database."""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            dbname=os.getenv('DB_NAME', 'pharmacy_db'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', '')
        )
        return conn
    except OperationalError as e:
        print(f"Error connecting to database: {e}")
        return None

def create_tables():
    """Create tables if they don't exist."""
    conn = get_connection()
    if conn is None:
        return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) UNIQUE NOT NULL
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS medications (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    code VARCHAR(50) UNIQUE NOT NULL,
                    lot VARCHAR(100),
                    expiration_date DATE NOT NULL,
                    price NUMERIC(10,2) NOT NULL DEFAULT 0,
                    quantity INTEGER NOT NULL,
                    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL
                );
            """)
            cur.execute("SELECT COUNT(*) FROM categories")
            if cur.fetchone()[0] == 0:
                default_cats = ['Analgésicos', 'Antibióticos', 'Antiinflamatorios', 'Vitaminas', 'Otros']
                for cat in default_cats:
                    cur.execute("INSERT INTO categories (name) VALUES (%s) ON CONFLICT DO NOTHING", (cat,))
            conn.commit()
    except Exception as e:
        print(f"Error creating tables: {e}")
    finally:
        conn.close()