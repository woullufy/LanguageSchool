from flask import Blueprint, render_template, request, redirect, url_for, flash
from db_connections import get_mysql_connection

student_management_bp = Blueprint("student_management", __name__)


@student_management_bp.route("/select-course/<student_id>", methods=["GET", "POST"])
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
        return redirect(
            url_for("student_management.course_groups", course_id=course_id, student_id=student_id)
        )

    return render_template("select_course.html", courses=courses, student_id=student_id)


@student_management_bp.route("/select-student", methods=["GET", "POST"])
def select_student():
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT student_id, first_name, last_name FROM student")
    students = cursor.fetchall()
    conn.close()

    if request.method == "POST":
        student_id = request.form["student_id"]
        return redirect(url_for("student_management.select_course", student_id=student_id))

    return render_template("select_student.html", students=students)


@student_management_bp.route("/course-groups/<course_id>/<student_id>", methods=["GET", "POST"])
def course_groups(course_id, student_id):
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM student_group WHERE course_id = %s", (course_id,))
    groups = cursor.fetchall()

    cursor.execute("SELECT title FROM course WHERE course_id = %s", (course_id,))
    title_dictionary = cursor.fetchone()
    title = title_dictionary["title"]

    cursor.execute(
        "SELECT student_group_id FROM group_membership WHERE student_id = %s",
        (student_id,),
    )
    joined_group_rows = cursor.fetchall()
    joined_ids = [row["student_group_id"] for row in joined_group_rows]

    cursor.close()
    conn.close()

    return render_template(
        "course_groups.html",
        groups=groups,
        title=title,
        student_id=student_id,
        joined_ids=joined_ids,
    )


@student_management_bp.route("/join-group/", methods=["POST"])
def join_group():
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    course_id = request.form["course_id"]
    student_group_id = request.form["student_group_id"]
    student_id = request.form["student_id"]

    cursor.execute(
        "SELECT * FROM student_group WHERE student_group_id = %s", (student_group_id,)
    )
    group_data = cursor.fetchone()
    age_category = group_data["age_category"]
    amount_of_participants = group_data["amount_of_participants"]
    max_participants = group_data["max_participants"]

    if amount_of_participants >= max_participants:
        flash("❌ Cannot join: group is full.")
        return redirect(
            url_for("student_management.course_groups", course_id=course_id, student_id=student_id)
        )

    cursor.execute("SELECT age FROM student WHERE student_id = %s", (student_id,))
    student_data = cursor.fetchone()
    student_age = student_data["age"]
    if not check_age(age_category, student_age):
        flash("❌ Cannot join: it is not you age category.")
        return redirect(
            url_for("student_management.course_groups", course_id=course_id, student_id=student_id)
        )

    cursor.execute(
        "INSERT INTO group_membership (student_id, student_group_id, course_id)"
        " VALUES (%s, %s, %s)",
        (student_id, student_group_id, course_id),
    )

    cursor.execute(
        "UPDATE student_group SET amount_of_participants = amount_of_participants + 1 "
        "WHERE student_group_id = %s",
        (student_group_id,),
    )

    conn.commit()
    conn.close()

    return redirect(
        url_for("student_management.course_groups", course_id=course_id, student_id=student_id)
    )


def check_age(age_category, age):
    if age_category == "Adult":
        return age >= 18
    if age_category == "Teenager":
        return 11 < age < 18
    if age_category == "Kids":
        return age <= 11
