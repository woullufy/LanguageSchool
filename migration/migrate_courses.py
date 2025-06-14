from db_connections import get_mysql_connection, get_mongo_connection


def migrate_courses():
    sql_conn = get_mysql_connection()
    mongo_db = get_mongo_connection()

    sql_cursor = sql_conn.cursor(dictionary=True)
    mongo_db.courses.delete_many({})

    # Fetch courses
    sql_cursor.execute("SELECT * FROM course")
    courses = sql_cursor.fetchall()

    # Fetch student groups
    sql_cursor.execute("SELECT * FROM student_group")
    all_groups = sql_cursor.fetchall()

    # Fetch group memberships
    sql_cursor.execute("SELECT * FROM group_membership")
    memberships = sql_cursor.fetchall()

    # Organize memberships into lookup
    students_by_group = {}
    for m in memberships:
        key = (m["student_group_id"], m["course_id"])
        students_by_group.setdefault(key, []).append(m["student_id"])

    # Group student_groups by course
    groups_by_course = {}
    for g in all_groups:
        key = g["course_id"]
        groups_by_course.setdefault(key, []).append(g)

    for course in courses:
        cid = course["course_id"]
        course_doc = {
            "course_id": cid,
            "language": course["language"],
            "title": course["title"],
            "level": course["level"],
            "tutor": course["tutor"],
            "student_group": [],
        }

        for g in groups_by_course.get(cid, []):
            group_key = (g["student_group_id"], cid)
            group_doc = {
                "student_group_id": g["student_group_id"],
                "age_category": g["age_category"],
                "max_participants": g["max_participants"],
                "students": students_by_group.get(group_key, []),
            }
            course_doc["student_group"].append(group_doc)

        mongo_db.courses.insert_one(course_doc)


if __name__ == "__main__":
    migrate_courses()
