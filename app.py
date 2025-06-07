from flask import (
    Flask,
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
)
import mysql.connector
import subprocess
import traceback
from datetime import datetime
# from pymongo import MongoClient

app = Flask(__name__)

def get_connection():
    return mysql.connector.connect(
        host="mariadb",                 # <- service name from docker-compose
        user="root",
        password="rootpass",
        database="language_school"
    )


# def get_connection():
#     return mysql.connector.connect(
#         host="mariadb",
#         user="flaskuser",
#         password="flaskpass",
#         database="language_school",
#     )


@app.route("/generate-data")
def generate_data():
    try:
        # Run data_generator.py using subprocess
        subprocess.run(["python", "data_generator.py"], check=True)
        return redirect("/tables")
    except subprocess.CalledProcessError as e:
        return "Error generating data", 500

# @app.rout("/migrate-to-nosql")
#@app.rout("/migrate-to-nosql")

@app.route("/tables")
def show_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Get all table names
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]

    # Fetch rows for each table
    data = {}
    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        data[table] = {"columns": columns, "rows": rows}

    cursor.close()
    conn.close()
    return render_template("tables.html", data=data)

@app.route('/select-course')
def select_course():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM course")
    courses = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('select_course.html', courses=courses)

@app.route('/course-groups/<course_id>')
def course_groups(course_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM student_group WHERE course_id = %s", (course_id,))
    groups = cursor.fetchall()

    cursor.execute("SELECT student_id, first_name, last_name FROM student")
    students = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('course_groups.html', groups=groups)



@app.route("/submit-assignment", methods=["GET", "POST"])
def submit_assignment_select_student():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT student_id, first_name, last_name FROM student")
    students = cursor.fetchall()
    conn.close()

    if request.method == "POST":
        student_id = request.form["student_id"]
        return redirect(url_for("submit_assignment_for_student", student_id=student_id))

    return render_template("select_student.html", students=students)


@app.route("/submit-assignment/<student_id>", methods=["GET", "POST"])
def submit_assignment_for_student(student_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        assignment_id = request.form["assignment_id"]
        submission_date = datetime.now()

        cursor.execute("""
            UPDATE assignment
            SET submission_date = %s
            WHERE assignment_id = %s AND from_student = %s
        """, (submission_date, assignment_id, student_id))
        conn.commit()

    # Load student name and all assignments
    cursor.execute("SELECT first_name, last_name FROM student WHERE student_id = %s", (student_id,))
    student = cursor.fetchone()

    cursor.execute("""
        SELECT assignment_id, date_due, submission_date
        FROM assignment
        WHERE from_student = %s
    """, (student_id,))
    assignments = cursor.fetchall()

    conn.close()

    return render_template("submit_assignment.html",
                           student_name=f"{student['first_name']} {student['last_name']}",
                           student_id=student_id,
                           assignments=assignments,
                           now=datetime.now())


@app.route("/grade-assignment", methods=["GET", "POST"])
def select_mentor():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT mentor_id FROM mentor")
    mentors = cursor.fetchall()
    conn.close()

    if request.method == "POST":
        mentor_id = request.form["mentor_id"]
        return redirect(url_for("grade_assignment", mentor_id=mentor_id))

    return render_template("select_mentor.html", mentors=mentors)


@app.route("/grade-assignment/<mentor_id>", methods=["GET", "POST"])
def grade_assignment(mentor_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Get students supervised by this mentor
    cursor.execute(
        """
        SELECT student_id, first_name, last_name
        FROM student
        WHERE mentor = %s
    """,
        (mentor_id,),
    )
    students = cursor.fetchall()

    # Get assignments from those students that have been submitted
    cursor.execute(
        """
        SELECT a.assignment_id, a.from_student, s.first_name, s.last_name, a.submission_date
        FROM assignment a
        JOIN student s ON a.from_student = s.student_id
        WHERE s.mentor = %s AND a.submission_date IS NOT NULL
          AND a.assignment_id NOT IN (SELECT assignment_id FROM checked_assignments)
    """,
        (mentor_id,),
    )
    assignments = cursor.fetchall()

    if request.method == "POST":
        assignment_id = request.form["assignment_id"]
        grade = int(request.form["grade"])
        checked_date = datetime.now()

        cursor.execute(
            """
            INSERT INTO checked_assignments (assignment_id, mentor_id, grade, checked_date)
            VALUES (%s, %s, %s, %s)
        """,
            (assignment_id, mentor_id, grade, checked_date),
        )

        conn.commit()
        conn.close()
        return redirect("/tables")

    conn.close()
    return render_template(
        "grade_assignment.html", assignments=assignments, mentor_id=mentor_id
    )


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    # Ilia's docker settings
    app.run(host='0.0.0.0', port = 5050, debug=True)

    # app.run(host='0.0.0.0', port = 5050, debug=True)
     app.run(host= '0.0.0.0', port = 5000, debug=True)
    # Local host settings
    # app.run(debug=True)
    #app.run(debug=True)
