from flask import Blueprint, render_template, request
from db_connections import get_mysql_connection, get_mongo_connection

reports_bp = Blueprint("reports", __name__)


# Students Assignment's Grades
@reports_bp.route("/graded-report", methods=["GET", "POST"])
def sql_graded_report():
    threshold = 70
    mode = "above"

    if request.method == "POST":
        try:
            threshold = int(request.form["threshold"])
            mode = request.form.get("mode", "above")
        except ValueError:
            pass

    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)

    comparator = ">=" if mode == "above" else "<"
    query = f"""
    SELECT 
        ca.assignment_id,
        ca.grade,
        ca.checked_date,
        m.mentor_id,
        e.first_name AS mentor_first_name,
        e.last_name AS mentor_last_name,
        s.student_id,
        s.first_name AS student_first_name,
        s.last_name AS student_last_name,
        a.submission_date,
        a.date_due,
        a.date_issued
    FROM checked_assignments ca
    JOIN mentor m ON ca.mentor_id = m.mentor_id
    JOIN employee e ON m.mentor_id = e.employee_id
    JOIN assignment a ON ca.assignment_id = a.assignment_id
    JOIN student s ON a.from_student = s.student_id
    WHERE ca.grade {comparator} %s
    ORDER BY ca.grade DESC
    """
    cursor.execute(query, (threshold,))
    results = cursor.fetchall()
    conn.close()

    return render_template(
        "report_graded_assignments.html",
        results=results,
        threshold=threshold,
        mode=mode,
    )


@reports_bp.route("/nosql-graded-report", methods=["GET", "POST"])
def nosql_graded_report():
    threshold = 70
    mode = "above"

    if request.method == "POST":
        try:
            threshold = int(request.form["threshold"])
            mode = request.form.get("mode", "above")
        except ValueError:
            pass

    db = get_mongo_connection()
    students_col = db["students"]
    employees_col = db["employees"]

    comparator = "$gte" if mode == "above" else "$lt"

    pipeline = [
        {"$unwind": "$assignments"},
        {"$match": {f"assignments.evaluation.grade": {comparator: threshold}}},
        {
            "$lookup": {
                "from": "employees",
                "localField": "mentor_id",
                "foreignField": "employee_id",
                "as": "mentor_info",
            }
        },
        {"$unwind": "$mentor_info"},
        {
            "$project": {
                "student_id": 1,
                "first_name": 1,
                "last_name": 1,
                "assignment_id": "$assignments.assignment_id",
                "grade": "$assignments.evaluation.grade",
                "checked_date": "$assignments.evaluation.checked_date",
                "submission_date": "$assignments.submission_date",
                "date_due": "$assignments.date_due",
                "date_issued": "$assignments.date_issued",
                "mentor_id": "$mentor_id",
                "mentor_first_name": "$mentor_info.first_name",
                "mentor_last_name": "$mentor_info.last_name",
            }
        },
        {"$sort": {"grade": -1}},
    ]

    results = list(students_col.aggregate(pipeline))

    return render_template(
        "report_graded_assignments.html",
        results=results,
        threshold=threshold,
        mode=mode,
        db_mode="nosql",
    )


# Average Group Age
@reports_bp.route("/average-age-report")
def average_age_report():
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        select c.title, c.language, c.level,
        round(avg(s.age)) as average_student_age, count(sg.amount_of_participants) as number_of_students
        from group_membership gm
        join student s ON gm.student_id = s.student_id
        join student_group sg ON gm.student_group_id = sg.student_group_id AND gm.course_id = sg.course_id
        join course c ON sg.course_id = c.course_id
        group by c.title, c.language, c.level
        """
    )
    reports = cursor.fetchall()
    return render_template("report_average_age.html", reports=reports)


@reports_bp.route("/avg-age-report-nosql")
def avg_age_report_nosql():
    db = get_mongo_connection()
    pipeline = [
        {"$unwind": "$student_group"},
        {"$unwind": "$student_group.students"},
        {
            "$lookup": {
                "from": "students",
                "localField": "student_group.students",
                "foreignField": "student_id",
                "as": "student",
            }
        },
        {"$unwind": "$student"},
        {
            "$group": {
                "_id": {"title": "$title", "language": "$language", "level": "$level"},
                "average_student_age": {"$avg": "$student.age"},
                "number_of_students": {"$sum": 1},
            }
        },
        {
            "$project": {
                "_id": 0,
                "title": "$_id.title",
                "language": "$_id.language",
                "level": "$_id.level",
                "average_student_age": {
                    "$toInt": {"$round": ["$average_student_age", 0]}
                },
                "number_of_students": 1,
            }
        },
    ]
    report = list(db["courses"].aggregate(pipeline))

    return render_template("report_average_age.html", reports=report)
