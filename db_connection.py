import mysql.connector

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="qwe123",
            database="project"
        )
        if conn.is_connected():
            print(" Database connected successfully!")
        return conn
    except mysql.connector.Error as err:
        print(f"Database connection failed: {err}")
        return None


