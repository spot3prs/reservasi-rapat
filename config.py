import mysql.connector
from mysql.connector import MySQLConnection, cursor

def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='db_reservasi'
    )
    return conn
