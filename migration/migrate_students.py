from db_connections import get_mysql_connection, get_mongo_connection


def migrate_students():
    sql_conn = get_mysql_connection()
    mongo_db = get_mongo_connection()

    sql_cursor = sql_conn.cursor(dictionary=True)
    mongo_db.students.delete_many({})

    # Get students
    sql_cursor.execute("SELECT * FROM student")
    all_students = sql_cursor.fetchall()

    # Get assignments
    sql_cursor.execute("SELECT * FROM assignment")
    assignments = sql_cursor.fetchall()
    assignments_by_student = {}
    for a in assignments:
        sid = a["from_student"]
        if sid not in assignments_by_student:
            assignments_by_student[sid] = []
        assignments_by_student[sid].append(a)

    # Get graded assignments
    sql_cursor.execute("SELECT * FROM checked_assignments")
    checked = {g["assignment_id"]: g for g in sql_cursor.fetchall()}

    for student in all_students:
        student_id = student["student_id"]
        doc = {
            "student_id": student_id,
            "age": student["age"],
            "first_name": student["first_name"],
            "last_name": student["last_name"],
            "email": student["email"],
            "mentor_id": student["mentor"],
            "assignments": [],
        }

        for a in assignments_by_student.get(student_id, []):
            assignment_doc = {
                "assignment_id": a["assignment_id"],
                "date_due": a["date_due"].isoformat(),
                "date_issued": a["date_issued"].isoformat(),
                "submission_date": (
                    a["submission_date"].isoformat() if a["submission_date"] else None
                ),
            }

            if a["assignment_id"] in checked:
                g = checked[a["assignment_id"]]
                assignment_doc["evaluation"] = {
                    "grade": g["grade"],
                    "checked_date": (
                        g["checked_date"].isoformat() if g["checked_date"] else None
                    ),
                }

            doc["assignments"].append(assignment_doc)

        mongo_db.students.insert_one(doc)


if __name__ == "__main__":
    migrate_students()
