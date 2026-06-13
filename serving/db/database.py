import mysql.connector
from mysql.connector import Error

def get_db_connection():
    """Kết nối MySQL"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            user='root',
            password='password',
            database='rss_ingest'
        )
        return connection
    except Error as e:
        print(f"Error: {e}")
        return None