from flask import Blueprint, render_template, request, redirect, url_for, session
from db_connections import get_mysql_connection, get_mongo_connection
from datetime import datetime

assignments_bp = Blueprint("assignments", __name__)


# ──────────── Navigation ────────────
#### Student selection part
@assignments_bp.route("/select-student", methods=["GET"])
def select_student_landing():
    db_mode = session.get("active_db_mode", "sql")
    students = get_students_nosql() if db_mode == "nosql" else get_students_sql()
    return render_template("select_student.html", students=students, db_mode=db_mode)


@assignments_bp.route("/student-dashboard", methods=["GET", "POST"])
def dashboard_student():
    db_mode = session.get("active_db_mode", "sql")

    if request.method == "POST":
        student_id = request.form.get("student_id")
        student_name = get_student_name(student_id, db_mode)
        student_age = get_student_age(student_id, db_mode)
        session["current_student_id"] = student_id
        session["current_student_name"] = student_name
        session["current_student_age"] = student_age
    else:
        student_id = session.get("current_student_id")
        student_name = session.get("current_student_name", "Student")
        student_age = session.get("current_student_age", "Unknown")

    return render_template(
        "dashboards/student.html",
        student_id=student_id,
        student_name=student_name,
        student_age=student_age,
        db_mode=db_mode,
    )


#### Mentor selection part
@assignments_bp.route("/select-mentor", methods=["GET"])
def select_mentor_landing():
    db_mode = session.get("active_db_mode", "sql")
    mentors = get_mentors_nosql() if db_mode == "nosql" else get_mentors_sql()
    return render_template("select_mentor.html", mentors=mentors, db_mode=db_mode)


@assignments_bp.route("/mentor-dashboard", methods=["GET", "POST"])
def dashboard_mentor():
    db_mode = session.get("active_db_mode", "sql")

    if request.method == "POST":
        mentor_id = request.form.get("mentor_id")
        mentor_name = get_mentor_name(mentor_id, db_mode)
        session["current_mentor_id"] = mentor_id
        session["current_mentor_name"] = mentor_name
    else:
        mentor_id = session.get("current_mentor_id")
        mentor_name = session.get("current_mentor_name", "Mentor")

    return render_template(
        "dashboards/mentor.html",
        mentor_id=mentor_id,
        mentor_name=mentor_name,
        db_mode=db_mode,
    )


# ──────────── Use case ────────────
#### Submit assignment
@assignments_bp.route("/submit-assignment/<student_id>", methods=["GET", "POST"])
def submit_assignment_for_student(student_id):
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    db_mode = session.get("active_db_mode", "sql")

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

    cursor.execute(
        "SELECT first_name, last_name FROM student WHERE student_id = %s", (student_id,)
    )
    student = cursor.fetchone()

    cursor.execute(
        """
        SELECT assignment_id, date_issued, date_due, submission_date
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
        db_mode=db_mode,
        now=datetime.now(),
    )


@assignments_bp.route("/submit-assignment-nosql/<student_id>", methods=["GET", "POST"])
def submit_assignment_nosql_for_student(student_id):
    db = get_mongo_connection()
    assignments = []
    current_time = datetime.now()
    students_col = db["students"]
    db_mode = session.get("active_db_mode", "sql")

    if request.method == "POST":
        assignment_id = request.form["assignment_id"]
        submission_date_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        students_col.update_one(
            {
                "student_id": student_id,
                "assignments.assignment_id": assignment_id,
            },
            {"$set": {"assignments.$.submission_date": submission_date_str}},
        )

        return redirect(
            url_for(
                "assignments.submit_assignment_nosql_for_student",
                student_id=student_id,
            )
        )

    student_doc = students_col.find_one({"student_id": student_id})

    if student_doc:
        for assign in student_doc.get("assignments", []):
            adapted_assignment = {
                "assignment_id": assign.get("assignment_id"),
                "date_issued": (
                    datetime.strptime(
                        assign.get("date_issued", ""), "%Y-%m-%dT%H:%M:%S"
                    )
                    if assign.get("date_issued")
                    else None
                ),
                "date_due": (
                    datetime.strptime(assign.get("date_due", ""), "%Y-%m-%dT%H:%M:%S")
                    if assign.get("date_due")
                    else None
                ),
                "submission_date": (
                    datetime.strptime(
                        assign.get("submission_date", ""), "%Y-%m-%dT%H:%M:%S"
                    )
                    if assign.get("submission_date")
                    else None
                ),
            }
            assignments.append(adapted_assignment)

    student_name = f"{student_doc.get('first_name')} {student_doc.get('last_name')}"

    return render_template(
        "submit_assignment.html",
        student_name=student_name,
        student_id=student_id,
        assignments=assignments,
        now=current_time,
        db_mode=db_mode,
    )


#### Grading assignment
@assignments_bp.route("/grade-assignment-sql/<mentor_id>", methods=["GET", "POST"])
def grade_assignments_sql_for_mentor(mentor_id):
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    db_mode = session.get("active_db_mode", "sql")

    if request.method == "POST":
        raw_assignment_id = request.form["assignment_id"]
        assignment_id = raw_assignment_id.split("::")[0]
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

        return redirect(
            url_for("assignments.grade_assignments_sql_for_mentor", mentor_id=mentor_id)
        )

    cursor.execute(
        """
        SELECT 
            a.assignment_id,
            a.from_student,
            s.first_name,
            s.last_name,
            a.submission_date,
            a.date_due,
            ca.grade,
            ca.checked_date
        FROM assignment a
        JOIN student s ON a.from_student = s.student_id
        LEFT JOIN checked_assignments ca ON a.assignment_id = ca.assignment_id
        WHERE s.mentor = %s AND a.submission_date IS NOT NULL
        """,
        (mentor_id,),
    )
    assignments = cursor.fetchall()

    conn.close()
    return render_template(
        "grade_assignment.html",
        assignments=assignments,
        mentor_id=mentor_id,
        mentor_name=get_mentor_name(mentor_id, db_mode),
        db_mode=db_mode,
    )


@assignments_bp.route("/grade-assignment-nosql/<mentor_id>", methods=["GET", "POST"])
def grade_assignments_nosql_for_mentor(mentor_id):
    db = get_mongo_connection()
    students_col = db["students"]
    db_mode = session.get("active_db_mode", "sql")

    assignments = []

    student_cursor = students_col.find(
        {"mentor_id": mentor_id},
        {"student_id": 1, "first_name": 1, "last_name": 1, "assignments": 1},
    )

    for student in student_cursor:
        for a in student.get("assignments", []):
            eval_data = a.get("evaluation", {})
            if a.get("submission_date"):

                submission_date = datetime.strptime(
                    a["submission_date"], "%Y-%m-%dT%H:%M:%S"
                )
                date_due = datetime.strptime(a["date_due"], "%Y-%m-%dT%H:%M:%S")

                assignments.append(
                    {
                        "assignment_id": a["assignment_id"],
                        "from_student": student["student_id"],
                        "first_name": student["first_name"],
                        "last_name": student["last_name"],
                        "submission_date": submission_date,
                        "date_due": date_due,
                        "grade": eval_data.get("grade"),
                        "checked_date": eval_data.get("checked_date"),
                    }
                )

    if request.method == "POST":
        assignment_id = request.form["assignment_id"]
        student_id = request.form["student_id"]
        grade = int(request.form["grade"])
        checked_date = datetime.now().strftime("%Y-%m-%d")

        students_col.update_one(
            {"student_id": student_id, "assignments.assignment_id": assignment_id},
            {
                "$set": {
                    "assignments.$.evaluation.grade": grade,
                    "assignments.$.evaluation.checked_date": checked_date,
                }
            },
        )

        return redirect(
            url_for(
                "assignments.grade_assignments_nosql_for_mentor",
                mentor_id=mentor_id,
                db_mode=db_mode,
            )
        )

    return render_template(
        "grade_assignment.html",
        assignments=assignments,
        mentor_id=mentor_id,
        db_mode=db_mode,
    )


# ──────────── Helper function ────────────
def get_students_sql():
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT student_id, first_name, last_name, age FROM student")
    students = cursor.fetchall()
    conn.close()
    return students


def get_students_nosql():
    db = get_mongo_connection()
    return list(
        db["students"].find(
            {}, {"student_id": 1, "first_name": 1, "last_name": 1, "age": 1, "_id": 0}
        )
    )


def get_mentors_sql():
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT m.mentor_id, e.first_name, e.last_name
        FROM mentor m
        JOIN employee e ON m.mentor_id = e.employee_id
    """
    )
    mentors = cursor.fetchall()
    conn.close()
    return mentors


def get_mentors_nosql():
    db = get_mongo_connection()
    employees_col = db["employees"]
    mentors_raw = list(
        employees_col.find(
            {"role": "mentor"},
            {"employee_id": 1, "first_name": 1, "last_name": 1, "_id": 0},
        )
    )
    mentors = [
        {
            "mentor_id": m.get("employee_id"),
            "first_name": m.get("first_name"),
            "last_name": m.get("last_name"),
        }
        for m in mentors_raw
    ]
    return mentors


def get_student_name(student_id, db_mode):
    if db_mode == "nosql":
        db = get_mongo_connection()
        student = db["students"].find_one(
            {"student_id": student_id}, {"first_name": 1, "last_name": 1}
        )
        if student:
            return f"{student.get('first_name')} {student.get('last_name')}"
    else:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT first_name, last_name FROM student WHERE student_id = %s",
            (student_id,),
        )
        result = cursor.fetchone()
        conn.close()
        if result:
            return f"{result['first_name']} {result['last_name']}"
    return "Guest Student"


def get_student_age(student_id, db_mode):
    if db_mode == "nosql":
        db = get_mongo_connection()
        student = db["students"].find_one({"student_id": student_id}, {"age": 1})
        if student:
            return f"{student.get('age')}"
    else:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT age FROM student WHERE student_id = %s",
            (student_id,),
        )
        result = cursor.fetchone()
        conn.close()
        if result:
            return f"{result['age']}"
    return "Unknown"


def get_mentor_name(mentor_id, db_mode):
    if db_mode == "nosql":
        db = get_mongo_connection()
        mentor = db["employees"].find_one(
            {"employee_id": mentor_id, "role": "mentor"},
            {"first_name": 1, "last_name": 1},
        )
        if mentor:
            return f"{mentor.get('first_name')} {mentor.get('last_name')}"
    else:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT e.first_name, e.last_name
            FROM mentor m
            JOIN employee e ON m.mentor_id = e.employee_id
            WHERE m.mentor_id = %s
        """,
            (mentor_id,),
        )
        result = cursor.fetchone()
        conn.close()
        if result:
            return f"{result['first_name']} {result['last_name']}"
    return "Guest Mentor"


def get_mentor_details_sql(mentor_id):
    conn = get_mysql_connection()
    mentor_info = None
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT mentor_id, first_name, last_name FROM mentor WHERE mentor_id = %s",
        (mentor_id,),
    )
    mentor_info = cursor.fetchone()

    return mentor_info


def get_mentor_details_nosql(mentor_id):
    db = get_mongo_connection()
    mentor_info = None
    employees_col = db["employees"]
    mentor_info_raw = employees_col.find_one(
        {"employee_id": mentor_id, "role": "mentor"},
        {"employee_id": 1, "first_name": 1, "last_name": 1, "_id": 0},
    )
    if mentor_info_raw:
        mentor_info = {
            "mentor_id": mentor_info_raw["employee_id"],
            "first_name": mentor_info_raw["first_name"],
            "last_name": mentor_info_raw["last_name"],
        }

    return mentor_info
