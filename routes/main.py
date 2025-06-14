from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from db_connections import get_mysql_connection, get_mongo_connection
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


@main_bp.route("/tables_mongo_courses")
def show_tables_courses():
    db = get_mongo_connection()
    courses_collection = db["courses"]
    courses = list(courses_collection.find({}))
    return render_template("courses_mongo.html", courses=courses)


@main_bp.route("/tables_mongo_students")
def show_tables_students():
    db = get_mongo_connection()
    students_collection = db["students"]
    students = list(students_collection.find({}))
    return render_template("students_mongo.html", students=students)


@main_bp.route("/tables_mongo_employees")
def show_tables_employees():
    db = get_mongo_connection()
    employees_collection = db["employees"]
    employees = list(employees_collection.find({}))
    return render_template("employees_mongo.html", employees=employees)

@main_bp.route("/set-db-mode", methods=["POST"])
def set_db_mode():
    mode = request.form.get("db_mode")
    session['active_db_mode'] = mode
    return redirect(url_for("main.admin_dashboard"))


@main_bp.route("/admin-dashboard")
def admin_dashboard():
    db_mode = session.get('active_db_mode', 'sql')
    return render_template("admin_dashboard.html", db_mode=db_mode)


@main_bp.route("/")
def index():
    return render_template("index.html")


