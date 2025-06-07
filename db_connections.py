import mysql.connector
from pymongo import MongoClient

def get_mysql_connection():
    return mysql.connector.connect(
        host="localhost",
        user="flaskuser",
        password="flaskpass",
        database="language_school"
    )

def get_mongo_connection():
    client = MongoClient("mongodb://localhost:27017/")
    return client.language_school_nosql
