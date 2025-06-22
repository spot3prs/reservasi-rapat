import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # Sesuaikan dengan password MySQL Anda
        database="db_reservasi"
    )
