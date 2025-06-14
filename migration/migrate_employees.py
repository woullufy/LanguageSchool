from db_connections import get_mysql_connection, get_mongo_connection


def migrate_employees():
    sql_conn = get_mysql_connection()
    mongo_db = get_mongo_connection()

    sql_cursor = sql_conn.cursor(dictionary=True)
    mongo_db.employees.delete_many({})

    sql_cursor.execute("SELECT * FROM employee")
    all_employees = sql_cursor.fetchall()

    sql_cursor.execute("SELECT * FROM mentor")
    mentors = {m["mentor_id"]: m for m in sql_cursor.fetchall()}

    sql_cursor.execute("SELECT * FROM tutor")
    tutors = {t["tutor_id"]: t for t in sql_cursor.fetchall()}

    for emp in all_employees:
        emp_id = emp["employee_id"]
        doc = {
            "employee_id": emp_id,
            "first_name": emp["first_name"],
            "last_name": emp["last_name"],
        }

        if emp_id in mentors:
            m = mentors[emp_id]
            doc["role"] = "mentor"
            doc["xp_level"] = m["xp_level"]
            doc["amount_of_students"] = m["amount_of_students"]
            doc["supervise"] = m["supervisor"]
        elif emp_id in tutors:
            t = tutors[emp_id]
            doc["role"] = "tutor"
            doc["years_of_experience"] = t["years_of_experience"]
            doc["language_speciality"] = t["language_speciality"]
        else:
            doc["role"] = "employee"

        mongo_db.employees.insert_one(doc)


if __name__ == "__main__":
    migrate_employees()
