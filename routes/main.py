from flask import Blueprint, render_template, redirect, url_for
from db_connections import get_mysql_connection
from migration.migrate_all import run_full_migration
import subprocess

main_bp = Blueprint("main", __name__)


@main_bp.route("/generate-data")
def generate_data():
    try:
        subprocess.run(["python", "data_generator.py"], check=True)
        return redirect(url_for("main.show_tables"))
    except subprocess.CalledProcessError as e:
        return "Error generating data", 500


@main_bp.route("/tables")
def show_tables():
    conn = get_mysql_connection()
    cursor = conn.cursor()

    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]

    data = {}
    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        data[table] = {"columns": columns, "rows": rows}

    cursor.close()
    conn.close()
    return render_template("tables.html", data=data)


@main_bp.route("/migrate", methods=["GET"])
def migrate_all_route():
    run_full_migration()
    return redirect(url_for("main.index"))


@main_bp.route("/")
def index():
    return render_template("index.html")
