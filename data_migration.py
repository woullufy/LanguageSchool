import mysql.connector
from pymongo import MongoClient

def migrate_students():
    sql_conn = mysql.connector.connect(
        host="localhost",
        user="flaskuser",
        password="flaskpass",
        database="language_school"
    )
    sql_cursor = sql_conn.cursor(dictionary=True)

    # Connect to MongoDB
    mongo_client = MongoClient("mongodb://localhost:27017/")
    mongo_db = mongo_client.language_school_nosql

    # Clear old student data
    mongo_db.students.delete_many({})

    # Fetch all students
    sql_cursor.execute("SELECT * FROM student")
    students = sql_cursor.fetchall()

    for student in students:
        student_id = student["student_id"]

        # Fetch assignments for this student
        sql_cursor.execute("SELECT * FROM assignment WHERE from_student = %s", (student_id,))
        assignments = sql_cursor.fetchall()

        # Fetch grading info for each assignment (if exists)
        for assignment in assignments:
            sql_cursor.execute(
                "SELECT * FROM checked_assignments WHERE assignment_id = %s",
                (assignment["assignment_id"],)
            )
            checked = sql_cursor.fetchone()
            if checked:
                assignment["grade"] = checked["grade"]
                assignment["graded_by"] = checked["mentor_id"]
                assignment["graded_at"] = checked["checked_date"]

        # Build MongoDB document
        student_doc = {
            "student_id": student["student_id"],
            "first_name": student["first_name"],
            "last_name": student["last_name"],
            "email": student["email"],
            "age": student["age"],
            "mentor_id": student["mentor"],
            "assignments": assignments
        }

        # Insert into MongoDB
        mongo_db.students.insert_one(student_doc)


if __name__ == "__main__":
    migrate_students()
