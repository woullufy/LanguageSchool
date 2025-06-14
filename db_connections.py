import mysql.connector
from pymongo import MongoClient
from flask import session 


def get_mysql_connection():
    return mysql.connector.connect(
        host="mariadb",
        user="flaskuser",
        password="flaskpass",
        database="language_school",
    )


def get_mongo_connection():
    client = MongoClient("mongodb://mongodb:27017/")
    return client.language_school_nosql


def get_active_db_connection():
    db_mode = session.get('active_db_mode', 'sql')
    
    if db_mode == 'sql':
        return get_mysql_connection()
    elif db_mode == 'nosql':
        return get_mongo_connection()
    else:
        return get_mysql_connection()