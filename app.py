from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash
)
from db_connections import get_mysql_connection
from migrate_all import run_full_migration

from datetime import datetime
import subprocess

app = Flask(__name__)
app.secret_key = 'supersecretkey123'


@app.route("/generate-data")
def generate_data():
    try:
        subprocess.run(["python", "data_generator.py"], check=True)
        return redirect("/tables")
    except subprocess.CalledProcessError as e:
        return "Error generating data", 500


@app.route("/tables")
def show_tables():
    conn = get_mysql_connection()
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


@app.route('/select-course/<student_id>', methods=["GET", "POST"])
def select_course(student_id):
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM course")
    courses = cursor.fetchall()
    cursor.close()
    conn.close()
    if request.method == "POST":
        course_id = request.form["course_id"]
        student_id = request.form["student_id"]
        return redirect(url_for('course_groups', course_id=course_id, student_id=student_id))

    return render_template('select_course.html', courses=courses, student_id=student_id)


@app.route("/select-student", methods=["GET", "POST"])
def select_student():
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT student_id, first_name, last_name FROM student")
    students = cursor.fetchall()
    conn.close()

    if request.method == "POST":
        student_id = request.form["student_id"]
        return redirect(url_for("select_course", student_id=student_id))

    return render_template("select_student.html", students=students)


@app.route("/course-groups/<course_id>/<student_id>", methods=["GET", "POST"])
def course_groups(course_id, student_id):
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM student_group WHERE course_id = %s", (course_id,))
    groups = cursor.fetchall()

    cursor.execute("SELECT title FROM course WHERE course_id = %s", (course_id,))
    title_dictionary = cursor.fetchone()
    title = title_dictionary["title"]

    cursor.execute("SELECT student_group_id FROM group_membership WHERE student_id = %s", (student_id,))
    joined_group_rows = cursor.fetchall()
    joined_ids = [row["student_group_id"] for row in joined_group_rows]

    cursor.close()
    conn.close()

    return render_template('course_groups.html',
                           groups=groups, title=title, student_id=student_id, joined_ids=joined_ids)


@app.route("/join-group/", methods=["POST"])
def join_group():
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    course_id = request.form["course_id"]
    student_group_id = request.form["student_group_id"]
    student_id = request.form["student_id"]

    cursor.execute("SELECT * FROM student_group WHERE student_group_id = %s", (student_group_id,))
    group_data = cursor.fetchone()
    age_category = group_data["age_category"]
    amount_of_participants = group_data["amount_of_participants"]
    max_participants = group_data["max_participants"]

    if amount_of_participants >= max_participants:
        flash("❌ Cannot join: group is full.")
        return redirect(url_for("course_groups", course_id=course_id, student_id=student_id))

    cursor.execute("SELECT age FROM student WHERE student_id = %s", (student_id,))
    student_data = cursor.fetchone()
    student_age = student_data["age"]
    if not check_age(age_category, student_age):
        flash("❌ Cannot join: it is not you age category.")
        return redirect(url_for("course_groups", course_id=course_id, student_id=student_id))

    cursor.execute("INSERT INTO group_membership (student_id, student_group_id, course_id)"
                   " VALUES (%s, %s, %s)", (student_id, student_group_id, course_id))

    cursor.execute("UPDATE student_group SET amount_of_participants = amount_of_participants + 1 "
                   "WHERE student_group_id = %s", (student_group_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("course_groups", course_id=course_id, student_id=student_id))


def check_age(age_category, age):
    if age_category == "Adult":
        return age >= 18
    if age_category == "Teenage":
        return 11 > age < 18
    if age_category == "Kids":
        return age <= 11


@app.route("/submit-assignment", methods=["GET", "POST"])
def submit_assignment_select_student():
    conn = get_mysql_connection()
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
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        assignment_id = request.form["assignment_id"]
        submission_date = datetime.now()

        cursor.execute(
            """
            UPDATE assignment
            SET submission_date = %s
            WHERE assignment_id = %s AND from_student = %s
        """,
            (submission_date, assignment_id, student_id),
        )
        conn.commit()

    # Load student name and all assignments
    cursor.execute(
        "SELECT first_name, last_name FROM student WHERE student_id = %s", (student_id,)
    )
    student = cursor.fetchone()

    cursor.execute(
        """
        SELECT assignment_id, date_due, submission_date
        FROM assignment
        WHERE from_student = %s
    """,
        (student_id,),
    )
    assignments = cursor.fetchall()

    conn.close()

    return render_template(
        "submit_assignment.html",
        student_name=f"{student['first_name']} {student['last_name']}",
        student_id=student_id,
        assignments=assignments,
        now=datetime.now(),
    )


@app.route("/grade-assignment", methods=["GET", "POST"])
def select_mentor():
    conn = get_mysql_connection()
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
    conn = get_mysql_connection()
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


@app.route("/migrate", methods=["GET"])
def migrate_all():
    run_full_migration()
    return redirect(url_for("index"))


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    # Ilia's docker settings
    app.run(host="0.0.0.0", port=5050, debug=True)

    # Local host settings
    # app.run(debug=True)
